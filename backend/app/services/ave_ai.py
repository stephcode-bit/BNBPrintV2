"""
Thin, cached client for the Ave AI security/analytics API.

Ave AI's exact endpoint shapes vary by plan/version, so this wraps calls in
a defensive try/except and normalizes whatever comes back into the fields
BNBPRINT actually needs. If AVE_AI_API_KEY is unset (or the call fails),
callers get `None` and BNBPRINT falls back to on-chain-only scoring —
the app never hard-fails just because one signal provider is down.
"""
import logging
import time
from dataclasses import dataclass
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger("bnbprint.ave_ai")
settings = get_settings()

_CACHE_TTL_SECONDS = 120
_cache: dict[str, tuple[float, "AveSecurity"]] = {}


@dataclass
class AveSecurity:
    security_score: Optional[float]  # 0-100, higher = safer
    honeypot_risk: Optional[bool]
    is_liquidity_locked: Optional[bool]
    is_contract_verified: Optional[bool]
    is_mintable: Optional[bool]
    is_owner_renounced: Optional[bool]
    buy_tax_pct: Optional[float]
    sell_tax_pct: Optional[float]
    top10_holder_pct: Optional[float]
    raw: dict


async def fetch_security(token_address: str) -> Optional[AveSecurity]:
    if not settings.ave_ai_api_key:
        return None

    cached = _cache.get(token_address)
    if cached and (time.time() - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    url = f"{settings.ave_ai_base_url}/tokens/{token_address}/security"
    headers = {"X-API-KEY": settings.ave_ai_api_key}

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, headers=headers, params={"chain": "bsc"})
            resp.raise_for_status()
            body = resp.json()
    except Exception as exc:  # network error, 4xx/5xx, bad JSON, etc.
        logger.warning("Ave AI lookup failed for %s: %s", token_address, exc)
        return None

    data = body.get("data", body)
    result = AveSecurity(
        security_score=_safe_float(data.get("security_score") or data.get("score")),
        honeypot_risk=data.get("is_honeypot"),
        is_liquidity_locked=data.get("lp_locked") or data.get("liquidity_locked"),
        is_contract_verified=data.get("is_verified") or data.get("source_verified"),
        is_mintable=data.get("is_mintable"),
        is_owner_renounced=data.get("owner_renounced") or data.get("renounced"),
        buy_tax_pct=_safe_float(data.get("buy_tax")),
        sell_tax_pct=_safe_float(data.get("sell_tax")),
        top10_holder_pct=_safe_float(data.get("top10_holder_percent")),
        raw=data,
    )
    _cache[token_address] = (time.time(), result)
    return result


def _safe_float(value) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
