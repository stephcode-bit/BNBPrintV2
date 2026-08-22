"""
Entry point for the $0/month deployment path: a scheduled GitHub Actions
job (see .github/workflows/scanner.yml) runs this script instead of an
always-on Railway/Render process.

What it does, once per invocation:
  1. Loads the last snapshot from Upstash Redis (so state survives across
     scheduled restarts).
  2. Loops for up to SCAN_LOOP_BUDGET_SECONDS (default 5h45m), polling for
     new bonding-curve tokens + refreshing already-tracked ones, on
     SCAN_POLL_INTERVAL_SECONDS cadence (default 15s).
  3. Writes the updated snapshot + stats back to Upstash on every cycle,
     and sends Web Push for newly-flagged runners.
  4. Exits cleanly when the time budget runs out, so the *next* scheduled
     job (see the workflow's cron — every 5h, comfortably inside this
     job's 5h45m budget) can pick up without a gap in coverage.

Why polling instead of the WebSocket subscription app/services/chain_
listener.run_listener() uses: a GitHub Actions runner isn't a great place
to hold one raw WSS connection open for 5+ hours (CI network egress can be
less stable than a real host), and HTTPS polling is trivial to make
resilient — one bad request just gets retried on the next tick instead of
tearing down a whole subscription. The trade-off, stated plainly: detection
latency is bounded by SCAN_POLL_INTERVAL_SECONDS instead of being instant.
At the default 15s, plus the frontend's own ~15-20s poll, worst case is
roughly 30-40s from on-chain event to your screen — not instant, but not
the 5-minute+ delay a bare cron-only setup would give you either.

Run locally with:  cd backend && python scan_runner.py
(needs the same .env as the FastAPI app, plus UPSTASH_REDIS_REST_URL/TOKEN)
"""
import asyncio
import logging
import random
import time

from app.config import get_settings
from app.services import chain_listener, push_runner, store
from app.services.chain_listener import (
    _demo_symbol,
    _random_address,
    process_token_pipeline,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("bnbprint.scan_runner")
settings = get_settings()

_last_seen_block: dict[str, int] = {}  # per-w3-connection cursor, live mode only


async def _demo_tick() -> list[dict]:
    """~40% chance per tick of a new synthetic token — DEMO_MODE only."""
    if random.random() > 0.4:
        return []
    from datetime import datetime, timezone

    symbol, name = _demo_symbol()
    platform = random.choice(chain_listener.DEMO_PLATFORMS)
    return [{
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
    }]


async def _live_tick() -> list[dict]:
    """
    Polls for new tokens since the last checked block via HTTPS.

    four.meme's TokenManager2 is fully decoded — see
    app/services/four_meme.py for how that contract address + the
    TokenCreate event ABI were verified (two independent, cross-confirming
    sources, not a guess). Any other configured factory (GraFun,
    EXTRA_BONDING_FACTORIES) still only gets its raw logs counted/logged
    rather than decoded into a token dict, since their token-creation
    event ABIs aren't confirmed yet — see app/services/bonding.py's
    GraFunReader docstring for the specific gap and how to close it the
    same way four.meme's was closed.
    """
    from datetime import datetime, timezone

    from app.services import four_meme
    from app.services.security_checks import get_web3

    w3 = get_web3()
    if w3 is None:
        return []

    try:
        latest = w3.eth.block_number
    except Exception:
        logger.warning("live poll: RPC call failed this tick")
        return []

    from_block = _last_seen_block.get("cursor", latest - 5)
    if latest <= from_block:
        return []

    discovered: list[dict] = []

    configured_four_meme = settings.bonding_factories.get("four.meme")
    if configured_four_meme and configured_four_meme.lower() == four_meme.TOKEN_MANAGER2.lower():
        try:
            contract = w3.eth.contract(address=four_meme.TOKEN_MANAGER2, abi=four_meme.EVENT_ABI)
            events = contract.events.TokenCreate().get_logs(from_block=from_block + 1, to_block=latest)
            for ev in events:
                args = ev["args"]
                discovered.append({
                    "address": args["token"],
                    "symbol": args["symbol"][:32] if args["symbol"] else "",
                    "name": args["name"][:128] if args["name"] else "",
                    "decimals": 18,
                    "pair_address": None,
                    "factory": "four.meme",
                    "dex": None,
                    "bonding_platform": "four.meme",
                    "creation_block": ev["blockNumber"],
                    "creation_timestamp": datetime.fromtimestamp(args["launchTime"], tz=timezone.utc),
                })
            if events:
                logger.info("live poll: %d new four.meme token(s) decoded", len(events))
        except Exception:
            logger.warning("live poll: four.meme TokenCreate decode failed this tick", exc_info=True)

    other_addresses = [a for name, a in settings.bonding_factories.items() if name != "four.meme"]
    other_addresses += [a for a in (settings.pancakeswap_v2_factory, settings.pancakeswap_v3_factory) if a]
    if other_addresses:
        try:
            logs = w3.eth.get_logs({"fromBlock": from_block + 1, "toBlock": latest, "address": other_addresses})
            if logs:
                logger.info("live poll: %d log(s) from other configured factories (decode pending, see docstring)", len(logs))
        except Exception:
            logger.warning("live poll: eth_getLogs failed for other factories this tick")

    _last_seen_block["cursor"] = latest
    return discovered


def _as_datetime(ts):
    """Normalizes a creation_timestamp that may be a live datetime object
    (tokens discovered this run) or a string (tokens resumed from a prior
    Upstash snapshot, where json.dumps(..., default=str) turned datetimes
    into plain strings) into a single comparable datetime — or None if it
    can't be parsed. Without this, mixing the two types in one max()/>=
    comparison raises a TypeError and crashes the whole scan loop once a
    run has both resumed and freshly-discovered tokens in memory."""
    from datetime import datetime

    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str) and ts:
        for candidate in (ts, ts.replace("Z", "+00:00")):
            try:
                return datetime.fromisoformat(candidate)
            except ValueError:
                continue
    return None


def _compute_stats(known: dict[str, dict]) -> dict:
    from datetime import datetime, timedelta, timezone

    tokens = list(known.values())
    total = len(tokens)
    bonding = sum(1 for t in tokens if t.get("is_bonding"))
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    def _created_recently(t: dict) -> bool:
        ts = _as_datetime(t.get("creation_timestamp"))
        return bool(ts and ts >= since)

    runners_24h = sum(1 for t in tokens if t.get("is_runner") and _created_recently(t))
    avg_security = sum((t.get("security_score") or 0) for t in tokens) / total if total else 0.0
    normalized_dates = [d for d in (_as_datetime(t.get("creation_timestamp")) for t in tokens) if d is not None]
    last_token_at = max(normalized_dates, default=None)

    return {
        "total_tokens": total,
        "bonding_tokens": bonding,
        "migrated_tokens": total - bonding,
        "runners_24h": runners_24h,
        "avg_security_score": round(avg_security, 1),
        "last_token_at": last_token_at,
    }


def _track_progress(enriched: dict, previous: "dict | None") -> dict:
    """
    Maintains two fields used to detect "dead" bonding-curve tokens — ones
    stuck with no buys — so they can be pruned after DEAD_BONDING_MINUTES
    of no forward movement:
      progress_high_water_mark: the best bonding_progress % seen so far
      progress_stale_since: when that high-water mark was last set (i.e.
        the last time progress actually moved forward)

    Progress on a bonding curve only ever goes up (more BNB raised), so
    "not progressing" is unambiguous: no new high-water mark. A small
    epsilon avoids float noise from re-reading the same on-chain state
    resetting the clock. Once a token migrates (is_bonding flips False)
    these fields stop being consulted — migrated is a success case, never
    pruned by _prune_dead_bonding.
    """
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    current_progress = enriched.get("bonding_progress") or 0.0
    prev_high = (previous or {}).get("progress_high_water_mark")
    prev_stale_since = (previous or {}).get("progress_stale_since")

    if prev_high is None or current_progress > prev_high + 0.01:
        enriched["progress_high_water_mark"] = current_progress
        enriched["progress_stale_since"] = now
    else:
        enriched["progress_high_water_mark"] = prev_high
        enriched["progress_stale_since"] = prev_stale_since

    return enriched


def _prune_dead_bonding(known: dict[str, dict]) -> int:
    """Removes bonding-curve tokens whose progress hasn't beaten its own
    high-water mark in DEAD_BONDING_MINUTES — see _track_progress. Migrated
    tokens (is_bonding=False) are never touched here. Returns the number
    removed, purely for logging."""
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.dead_bonding_minutes)
    dead = []
    for address, t in known.items():
        if not t.get("is_bonding"):
            continue
        stale_since = _as_datetime(t.get("progress_stale_since"))
        if stale_since and stale_since <= cutoff:
            dead.append(address)

    for address in dead:
        del known[address]
    return len(dead)


async def _handle_discovered(raw: dict, known: dict[str, dict], notified: set[str]) -> None:
    try:
        enriched = await process_token_pipeline(raw)
    except Exception:
        logger.exception("pipeline failed for %s", raw.get("address"))
        return

    address = enriched["address"]
    previous = known.get(address)
    was_runner = previous.get("is_runner", False) if previous else False
    enriched = _track_progress(enriched, previous)
    known[address] = enriched

    alert_type = "runner" if enriched["is_runner"] else "new_token"
    message = (
        f"🚀 {enriched['symbol']} flagged as a likely runner ({enriched['runner_score']:.0f}/100)"
        if enriched["is_runner"]
        else f"New token detected: {enriched['symbol']} on {enriched.get('bonding_platform') or enriched.get('dex') or 'DEX'}"
    )
    await store.append_alert({"token_address": address, "alert_type": alert_type, "message": message})

    if enriched["is_runner"] and not was_runner and address not in notified:
        notified.add(address)
        await push_runner.notify_all(
            title=f"🚀 Runner: {enriched['symbol']}",
            body=f"Runner score {enriched['runner_score']:.0f}/100 · security {enriched['security_score']:.0f}/100",
            url=f"/token/{address}",
        )


async def _refresh_bonding(known: dict[str, dict]) -> None:
    bonding_addrs = [a for a, t in known.items() if t.get("is_bonding")][:50]
    for address in bonding_addrs:
        row = known[address]
        token_dict = {
            "address": row["address"],
            "symbol": row["symbol"],
            "name": row["name"],
            "decimals": row["decimals"],
            "pair_address": row.get("pair_address"),
            "factory": row.get("factory"),
            "dex": row.get("dex"),
            "bonding_platform": row.get("bonding_platform"),
            "creation_block": row.get("creation_block"),
            "creation_timestamp": row["creation_timestamp"],
        }
        try:
            enriched = await process_token_pipeline(token_dict)
        except Exception:
            logger.exception("refresh failed for %s", address)
            continue
        enriched = _track_progress(enriched, row)
        known[address] = enriched


async def main() -> None:
    logger.info(
        "scan_runner starting (demo_mode=%s, poll_interval=%ds, budget=%ds)",
        settings.demo_mode, settings.scan_poll_interval_seconds, settings.scan_loop_budget_seconds,
    )
    # One-time diagnostic: reveals the *shape* of the Upstash URL secret
    # (length, whether it starts with https://, and a short repr of its
    # head/tail) without ever logging the token or the full URL, so a
    # stray quote mark, leading space, or swapped URL/TOKEN value shows up
    # here instead of us guessing blind from a generic httpx error.
    _url = settings.upstash_redis_rest_url
    _token = settings.upstash_redis_rest_token
    logger.info(
        "Upstash URL diagnostic: set=%s len=%d starts_with_https=%s head=%r tail=%r",
        bool(_url), len(_url), _url.startswith("https://"), _url[:12], _url[-6:] if _url else "",
    )
    logger.info(
        "Upstash TOKEN diagnostic: set=%s len=%d head=%r",
        bool(_token), len(_token), _token[:6] if _token else "",
    )

    snapshot = await store.get_snapshot()
    known: dict[str, dict] = {t["address"]: t for t in snapshot if t.get("address")}
    notified: set[str] = {a for a, t in known.items() if t.get("is_runner")}
    logger.info("resumed with %d known tokens from previous snapshot", len(known))

    start = time.monotonic()
    last_refresh = 0.0

    while time.monotonic() - start < settings.scan_loop_budget_seconds:
        cycle_start = time.monotonic()

        try:
            new_raws = await (_demo_tick() if settings.demo_mode else _live_tick())
            for raw in new_raws:
                if raw["address"] not in known:
                    await _handle_discovered(raw, known, notified)

            if cycle_start - last_refresh >= settings.bonding_refresh_interval:
                await _refresh_bonding(known)
                last_refresh = cycle_start

            pruned = _prune_dead_bonding(known)
            if pruned:
                logger.info(
                    "pruned %d dead bonding-curve token(s) — no progress in %dmin",
                    pruned, settings.dead_bonding_minutes,
                )

            await store.save_snapshot(list(known.values()))
            await store.save_stats(_compute_stats(known))
        except Exception:
            # Belt-and-suspenders: any bug in one cycle (an unexpected data
            # shape, a transient failure we didn't anticipate, etc.) logs
            # and moves on to the next tick instead of exiting the whole
            # process — a hard crash here wastes the rest of this run's
            # multi-hour budget until the next scheduled restart picks up,
            # which is a much worse outcome than one skipped cycle.
            logger.exception("scan cycle failed unexpectedly — continuing to next tick")

        elapsed = time.monotonic() - cycle_start
        await asyncio.sleep(max(1.0, settings.scan_poll_interval_seconds - elapsed))

    logger.info("time budget exhausted after %d tokens tracked — exiting for the next scheduled run", len(known))


if __name__ == "__main__":
    asyncio.run(main())
