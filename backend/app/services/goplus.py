"""
GoPlus Security API — a real, working honeypot/rug-risk simulator.

This replaces "build our own eth_call honeypot simulator" with a free,
purpose-built third-party service that already does exactly that (they run
the buy/sell simulation server-side across many chains, BNB Chain included,
and expose the result as a plain JSON API — no wallet, no gas, no ABI
needed on our end). It's this project's primary honeypot-risk source;
Ave AI and our own on-chain checks (security_checks.py) still run
alongside it and all three get merged in chain_listener.process_token_pipeline.

Docs: https://docs.gopluslabs.io/reference/token-security-api
Endpoint: GET https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses=...
  chain_id 56 = BNB Smart Chain mainnet.

No API key is required for light/testing usage (public rate limit applies).
For production volume, sign up at https://gopluslabs.io/ for a free
App Key + App Secret and set GOPLUS_APP_KEY / GOPLUS_APP_SECRET below to
get an access token with a much higher rate limit — see `_get_access_token`.
Everything degrades gracefully to "unknown" if the API is unset/unreachable,
same pattern as ave_ai.py.
"""
import logging
import time
from dataclasses import dataclass
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger("bnbprint.goplus")
settings = get_settings()

BSC_CHAIN_ID = "56"
_CACHE_TTL_SECONDS = 120
_cache: dict[str, tuple[float, "GoPlusSecurity"]] = {}

_token_cache: dict[str, tuple[float, str]] = {}  # app_key -> (expires_at, access_token)


@dataclass
class GoPlusSecurity:
    honeypot_risk: Optional[bool]
    buy_tax_pct: Optional[float]
    sell_tax_pct: Optional[float]
    is_open_source: Optional[bool]  # -> maps to contract_verified
    is_mintable: Optional[bool]
    owner_renounced: Optional[bool]
    lp_locked: Optional[bool]
    holder_count: Optional[int]
    top10_holder_pct: Optional[float]
    raw: dict


async def _get_access_token(client: httpx.AsyncClient) -> Optional[str]:
    """Optional: exchange GOPLUS_APP_KEY/SECRET for a higher-rate-limit
    access token. Skipped entirely if those aren't set — the API works
    keyless at a lower rate limit, which is plenty for a small deployment."""
    if not settings.goplus_app_key or not settings.goplus_app_secret:
        return None

    cached = _token_cache.get(settings.goplus_app_key)
    if cached and time.time() < cached[0]:
        return cached[1]

    try:
        import hashlib

        timestamp = int(time.time())
        sign = hashlib.sha1(f"{settings.goplus_app_key}{timestamp}{settings.goplus_app_secret}".encode()).hexdigest()
        resp = await client.post(
            "https://api.gopluslabs.io/api/v1/token",
            json={"app_key": settings.goplus_app_key, "time": timestamp, "sign": sign},
            timeout=8.0,
        )
        resp.raise_for_status()
        body = resp.json()
        token = body.get("result", {}).get("access_token")
        expires_in = body.get("result", {}).get("expires_in", 3600)
        if token:
            _token_cache[settings.goplus_app_key] = (time.time() + expires_in - 60, token)
        return token
    except Exception as exc:
        logger.warning("GoPlus auth failed, falling back to keyless requests: %s", exc)
        return None


async def fetch_security(token_address: str) -> Optional[GoPlusSecurity]:
    cached = _cache.get(token_address)
    if cached and (time.time() - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {}
            token = await _get_access_token(client)
            if token:
                headers["Authorization"] = token

            resp = await client.get(
                f"https://api.gopluslabs.io/api/v1/token_security/{BSC_CHAIN_ID}",
                params={"contract_addresses": token_address},
                headers=headers,
            )
            resp.raise_for_status()
            body = resp.json()
    except Exception as exc:
        logger.warning("GoPlus lookup failed for %s: %s", token_address, exc)
        return None

    data = (body.get("result") or {}).get(token_address.lower(), {})
    if not data:
        return None

    holders = data.get("holders") or []
    top10_pct = None
    if holders:
        try:
            top10_pct = sum(float(h.get("percent", 0)) for h in holders[:10]) * 100
        except (TypeError, ValueError):
            top10_pct = None

    lp_holders = data.get("lp_holders") or []
    lp_locked = any(h.get("is_locked") in (1, "1", True) for h in lp_holders) if lp_holders else None

    result = GoPlusSecurity(
        honeypot_risk=_to_bool(data.get("is_honeypot")),
        buy_tax_pct=_safe_pct(data.get("buy_tax")),
        sell_tax_pct=_safe_pct(data.get("sell_tax")),
        is_open_source=_to_bool(data.get("is_open_source")),
        is_mintable=_to_bool(data.get("is_mintable")),
        owner_renounced=_to_bool(data.get("owner_address") in ("", None) or data.get("can_take_back_ownership") == "0"),
        lp_locked=lp_locked,
        holder_count=_safe_int(data.get("holder_count")),
        top10_holder_pct=top10_pct,
        raw=data,
    )
    _cache[token_address] = (time.time(), result)
    return result


def _to_bool(value) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return str(value) in ("1", "true", "True")


def _safe_pct(value) -> Optional[float]:
    try:
        return float(value) * 100 if value is not None else None
    except (TypeError, ValueError):
        return None


def _safe_int(value) -> Optional[int]:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
