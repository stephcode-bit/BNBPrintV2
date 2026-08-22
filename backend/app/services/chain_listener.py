"""
Real-time token discovery.

Two sources feed the same pipeline:
  1. PancakeSwap V2/V3 `PairCreated` events (plain DEX launches / tokens
     that have finished bonding and migrated).
  2. Bonding-curve platform factory events (four.meme, GraFun, ...) —
     "token created" logs, read generically via topic0 + heuristics since
     each platform's event signature differs.

In DEMO_MODE (the default — see .env.example) this module instead runs a
synthetic generator that emits realistic-looking tokens on an interval, so
the whole app is explorable with zero RPC/API keys. Flip DEMO_MODE=false
and fill in RPC_WSS_URL + verified factory addresses/ABIs to go live.
"""
import asyncio
import logging
import random
import string
import time
from datetime import datetime, timezone
from typing import Optional

from web3 import Web3

from app.config import get_settings
from app.services import ave_ai, bonding, goplus, security_checks
from app.services.scoring import ScoringInputs, compute_runner_score, compute_security_score, is_runner

logger = logging.getLogger("bnbprint.listener")
settings = get_settings()

# PairCreated(address indexed token0, address indexed token1, address pair, uint)
PAIR_CREATED_TOPIC = Web3.keccak(text="PairCreated(address,address,address,uint256)").hex()

DEMO_PLATFORMS = ["four.meme", "grafun", "pancakeswap_v2"]
DEMO_PREFIXES = ["MOON", "PEPE", "BNB", "ROCK", "DOGE", "SHIB", "FLOKI", "CHAD", "WOJAK", "BASED"]
DEMO_SUFFIXES = ["INU", "AI", "X", "2.0", "KING", "COIN", "GOD", "MAX", "PRIME", ""]


def _invert_optional(value: Optional[bool]) -> Optional[bool]:
    """None-safe `not x` — for turning `is_mintable` into `mint_disabled`
    without accidentally treating "unknown" as "False"."""
    return None if value is None else (not value)


def _first_not_none(*values):
    """Returns the first argument that isn't None (or falsy-from-`and`
    short-circuiting, e.g. `goplus_result and goplus_result.field` when
    goplus_result is None) — used to merge multiple best-effort signal
    sources in priority order without a real one being clobbered by a
    later source that simply doesn't have an opinion."""
    for v in values:
        if v is not None:
            return v
    return None


def _random_address() -> str:
    return "0x" + "".join(random.choices(string.hexdigits.lower()[:16], k=40))


def _demo_symbol() -> tuple[str, str]:
    prefix = random.choice(DEMO_PREFIXES)
    suffix = random.choice(DEMO_SUFFIXES)
    symbol = f"{prefix}{suffix}"
    name = f"{prefix.title()} {suffix}".strip() + " Token"
    return symbol[:10], name


async def demo_token_generator(on_new_token):
    """Emits a new synthetic token every few seconds, forever, for DEMO_MODE."""
    logger.info("DEMO_MODE enabled — generating synthetic token feed")
    while True:
        await asyncio.sleep(random.uniform(4, 11))
        symbol, name = _demo_symbol()
        platform = random.choice(DEMO_PLATFORMS)
        token = {
            "address": _random_address(),
            "symbol": symbol,
            "name": name,
            "decimals": 18,
            "pair_address": _random_address() if platform == "pancakeswap_v2" else None,
            "factory": platform,
            "dex": "pancakeswap_v2" if platform == "pancakeswap_v2" else None,
            "bonding_platform": None if platform == "pancakeswap_v2" else platform,
            "creation_block": random.randint(40_000_000, 41_000_000),
            "creation_timestamp": datetime.now(timezone.utc),
        }
        try:
            await on_new_token(token)
        except Exception:
            logger.exception("on_new_token handler failed")


async def process_token_pipeline(token: dict) -> dict:
    """
    Runs the full security + bonding + scoring pipeline for a single token
    and returns the enriched fields ready to persist. This is the same
    pipeline used for both the initial discovery pass and the periodic
    background refresh (see app/tasks.py).
    """
    address = token["address"]
    pair_address = token.get("pair_address")
    platform = token.get("bonding_platform")

    # 1. GoPlus Security — the real honeypot/tax/LP-lock simulator (see
    #    app/services/goplus.py). This is the primary source for
    #    honeypot_risk and buy/sell tax; it's a dedicated third-party
    #    simulator rather than something we hand-roll with eth_call.
    goplus_result = None if settings.demo_mode else await goplus.fetch_security(address)

    # 2. Ave AI (best-effort, cached, skipped automatically if no API key)
    ave = await ave_ai.fetch_security(address)

    # 3. On-chain checks (best-effort, skipped automatically if no RPC) —
    #    still useful as a third, independent cross-check even once GoPlus
    #    and/or Ave AI are configured.
    if settings.demo_mode:
        onchain = _demo_onchain_result()
    else:
        onchain = security_checks.run_full_check(address, pair_address)

    # 4. Bonding progress
    w3 = None if settings.demo_mode else security_checks.get_web3()
    bonding_status = None
    if platform:
        bonding_status = bonding.read_bonding_status(w3, platform, address)

    # creation_timestamp may be a live datetime (freshly discovered this
    # run) or a plain string (a resumed token whose prior JSON round-trip
    # through Upstash turned it to text — see scan_runner.py's _as_datetime
    # for the same issue on the stats side). Without normalizing here,
    # `datetime.now() - <string>` raises a TypeError that _refresh_bonding
    # silently swallows, which means a resumed token's bonding progress —
    # and dead-token staleness tracking — never updates again after its
    # first save. That's why previously-stuck tokens stayed stuck forever.
    _created = token["creation_timestamp"]
    if isinstance(_created, str):
        for _candidate in (_created, _created.replace("Z", "+00:00")):
            try:
                _created = datetime.fromisoformat(_candidate)
                break
            except ValueError:
                continue
        else:
            _created = datetime.now(timezone.utc)

    liquidity_usd = token.get("liquidity_usd") or (
        random.uniform(500, 60_000) if settings.demo_mode else 0.0
    )
    volume_24h = token.get("volume_24h_usd") or (
        liquidity_usd * random.uniform(0.1, 4.0) if settings.demo_mode else 0.0
    )
    holder_count = token.get("holder_count") or (
        random.randint(3, 900)
        if settings.demo_mode
        else ((goplus_result.holder_count if goplus_result else None) or 0)
    )
    market_cap = token.get("market_cap_usd") or (
        random.uniform(2_000, 800_000) if settings.demo_mode else 0.0
    )
    age_minutes = max(
        0.1,
        (datetime.now(timezone.utc) - _created).total_seconds() / 60,
    )

    # Merge the three signal sources with a clear priority: GoPlus (a real,
    # dedicated simulator) first, then Ave AI, then our own on-chain checks,
    # falling through to the next source whenever the preferred one has no
    # opinion (None) rather than blindly overwriting a real signal.
    if settings.demo_mode:
        honeypot_risk = onchain.honeypot_risk
        buy_tax_pct = onchain.buy_tax_pct
        sell_tax_pct = onchain.sell_tax_pct
    else:
        honeypot_risk = _first_not_none(goplus_result and goplus_result.honeypot_risk, ave and ave.honeypot_risk, onchain.honeypot_risk)
        buy_tax_pct = _first_not_none(goplus_result and goplus_result.buy_tax_pct, ave and ave.buy_tax_pct, onchain.buy_tax_pct) or 0.0
        sell_tax_pct = _first_not_none(goplus_result and goplus_result.sell_tax_pct, ave and ave.sell_tax_pct, onchain.sell_tax_pct) or 0.0

    inputs = ScoringInputs(
        ave_security_score=ave.security_score if ave else None,
        honeypot_risk=honeypot_risk,
        liquidity_locked=bool(_first_not_none(goplus_result and goplus_result.lp_locked, ave and ave.is_liquidity_locked, onchain.liquidity_locked)),
        owner_renounced=bool(_first_not_none(goplus_result and goplus_result.owner_renounced, ave and ave.is_owner_renounced, onchain.owner_renounced)),
        mint_disabled=bool(
            _first_not_none(
                _invert_optional(goplus_result.is_mintable) if goplus_result else None,
                onchain.mint_disabled,
            )
        ),
        contract_verified=_first_not_none(goplus_result and goplus_result.is_open_source, ave and ave.is_contract_verified, onchain.contract_verified),
        top10_holder_pct=_first_not_none(goplus_result and goplus_result.top10_holder_pct, ave and ave.top10_holder_pct, onchain.top10_holder_pct),
        buy_tax_pct=buy_tax_pct,
        sell_tax_pct=sell_tax_pct,
        volume_24h_usd=volume_24h,
        liquidity_usd=liquidity_usd,
        market_cap_usd=market_cap,
        holder_count=holder_count,
        holder_growth_per_hour=random.uniform(0, 40) if settings.demo_mode else 0.0,
        bonding_progress_pct=bonding_status.progress_pct if bonding_status else 100.0,
        bonding_speed_pct_per_hour=random.uniform(0, 60) if settings.demo_mode else 0.0,
        age_minutes=age_minutes,
    )

    security_score = compute_security_score(inputs)
    runner_score = compute_runner_score(inputs, security_score)

    return {
        **token,
        "creation_timestamp": _created,  # normalized above — always a real datetime from here on
        "liquidity_usd": liquidity_usd,
        "liquidity_locked": inputs.liquidity_locked,
        "market_cap_usd": market_cap,
        "price_usd": market_cap / 1_000_000_000 if market_cap else 0.0,
        "volume_24h_usd": volume_24h,
        "holder_count": holder_count,
        "top10_holder_pct": inputs.top10_holder_pct or 0.0,
        "owner_address": onchain.owner_address,
        "owner_renounced": inputs.owner_renounced,
        "mint_disabled": inputs.mint_disabled,
        "contract_verified": bool(inputs.contract_verified),
        "honeypot_risk": inputs.honeypot_risk,
        "buy_tax_pct": inputs.buy_tax_pct,
        "sell_tax_pct": inputs.sell_tax_pct,
        "ave_security_score": ave.security_score if ave else None,
        "security_score": security_score,
        "runner_score": runner_score,
        "is_runner": is_runner(runner_score),
        "bonding_progress": bonding_status.progress_pct if bonding_status else 100.0,
        "is_bonding": bonding_status.is_bonding if bonding_status else False,
        "last_checked_at": datetime.now(timezone.utc),
    }


class _DemoOnchain:
    def __init__(self):
        self.owner_address = "0x000000000000000000000000000000000000dEaD" if random.random() > 0.3 else _random_address()
        self.owner_renounced = self.owner_address.lower().endswith("dead")
        self.mint_disabled = self.owner_renounced or random.random() > 0.5
        self.contract_verified = random.random() > 0.25
        self.honeypot_risk = random.random() < 0.12
        self.buy_tax_pct = round(random.uniform(0, 12), 1)
        self.sell_tax_pct = round(random.uniform(0, 15), 1)
        self.liquidity_locked = random.random() > 0.35
        self.top10_holder_pct = round(random.uniform(10, 85), 1)


def _demo_onchain_result() -> _DemoOnchain:
    return _DemoOnchain()


async def run_listener(on_new_token):
    """
    Entry point called from app startup. In DEMO_MODE, runs the synthetic
    generator. In live mode, opens a WebSocket subscription to new heads,
    filters logs for PairCreated + configured bonding factories, and hands
    off decoded token-creation events to `on_new_token`.
    """
    if settings.demo_mode:
        await demo_token_generator(on_new_token)
        return

    if not settings.rpc_wss_url:
        logger.warning("DEMO_MODE is off but RPC_WSS_URL is unset — listener idle.")
        return

    from web3 import WebSocketProvider  # web3 v7 async provider
    from web3.main import AsyncWeb3

    logger.info("Connecting to BNB Chain via websocket for live event listening...")
    async with AsyncWeb3(WebSocketProvider(settings.rpc_wss_url)) as w3:
        addresses = [settings.pancakeswap_v2_factory, settings.pancakeswap_v3_factory]
        addresses += list(settings.bonding_factories.values())
        addresses = [Web3.to_checksum_address(a) for a in addresses if a]

        subscription_id = await w3.eth.subscribe(
            "logs", {"address": addresses}
        )
        logger.info("Subscribed to logs for %d factory addresses", len(addresses))

        async for payload in w3.socket.process_subscriptions():
            log = payload["result"]
            try:
                await _handle_log(w3, log, on_new_token)
            except Exception:
                logger.exception("failed to handle log %s", log.get("transactionHash"))


async def _handle_log(w3, log, on_new_token):
    """
    Decodes a raw log into a token-creation event. `PairCreated` logs are
    straightforward (fixed signature); bonding-curve "token created" logs
    vary per platform, so this dispatches on the log's source address and
    expects a platform-specific decoder to be filled in once you have each
    factory's verified ABI (see app/services/bonding.py for the same
    "confirm the ABI" caveat).
    """
    topics = log.get("topics", [])
    if not topics:
        return

    topic0 = topics[0].hex() if hasattr(topics[0], "hex") else topics[0]

    if topic0 == PAIR_CREATED_TOPIC:
        # token0, token1 are indexed topics[1], topics[2]; pair address is
        # in the non-indexed data. Decode with the router/factory ABI here.
        logger.info("PairCreated log seen: tx=%s", log.get("transactionHash"))
        # TODO: decode + call on_new_token(...) once the factory ABI is loaded.
        return

    # Bonding-curve factory logs — dispatch by source address once each
    # platform's "TokenCreated"-style event signature/ABI is confirmed.
    logger.debug("Unhandled log from %s (topic0=%s)", log.get("address"), topic0)
