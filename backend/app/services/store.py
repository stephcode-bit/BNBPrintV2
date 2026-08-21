"""
Upstash Redis (REST API) — the shared state store between the scanner
(app/scan_runner.py, run on a schedule by GitHub Actions) and the frontend's
Next.js API routes (which read the same store directly, see
frontend/app/api/*/route.ts).

Why Redis-over-REST instead of Postgres: this project moved off an
always-on Railway/Postgres deployment (which cost money every month) onto
a $0/month stack — a scheduled GitHub Actions job instead of an always-on
process, and Upstash's free tier (500K commands/month, no sleep/cold-start,
no card required) instead of a hosted Postgres with a monthly compute-hour
budget that a near-continuous scanner would burn through in ~2-3 weeks.
Upstash's REST API also means both the Python scanner AND Vercel's
serverless functions can talk to it with a plain HTTPS call — no
persistent connection pool to manage on either side.

Data model (deliberately simple — a handful of JSON blobs, not a relational
schema):
  bnbprint:tokens        -> JSON list of enriched token dicts (the "snapshot")
  bnbprint:stats         -> JSON dict (StatsOut-shaped)
  bnbprint:alerts        -> Redis LIST of JSON alert dicts, capped length
  bnbprint:push_subs     -> Redis HASH, field=endpoint, value=JSON subscription

If UPSTASH_REDIS_REST_URL/TOKEN aren't set (e.g. running the old
always-on FastAPI app locally against Postgres instead), every function
here degrades to a harmless no-op / empty result rather than raising —
so app/main.py's legacy path still works without Upstash configured.
"""
import json
import logging
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger("bnbprint.store")
settings = get_settings()

MAX_TOKENS = 300  # cap the snapshot so the blob doesn't grow unbounded
MAX_ALERTS = 200

_client: Optional[httpx.AsyncClient] = None


def _configured() -> bool:
    return bool(settings.upstash_redis_rest_url and settings.upstash_redis_rest_token)


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.upstash_redis_rest_url,
            headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
            timeout=10.0,
        )
    return _client


async def _pipeline(commands: list[list[Any]]) -> list[Any]:
    """Runs a batch of Redis commands in one HTTPS round-trip via Upstash's
    REST pipeline endpoint. Each command is a list like ["SET", "key", "val"].
    Returns the list of per-command results (raises on transport errors,
    logs+returns [] on a non-2xx so a flaky Upstash call never crashes the
    scanner mid-loop)."""
    if not _configured():
        return []
    try:
        resp = await _get_client().post("/pipeline", json=commands)
        resp.raise_for_status()
        return [r.get("result") for r in resp.json()]
    except Exception:
        logger.exception("Upstash pipeline call failed (continuing with empty result)")
        return []


async def _get(key: str) -> Optional[str]:
    results = await _pipeline([["GET", key]])
    return results[0] if results else None


async def _set(key: str, value: str) -> None:
    await _pipeline([["SET", key, value]])


# --- Token snapshot -------------------------------------------------------

async def get_snapshot() -> list[dict]:
    raw = await _get("bnbprint:tokens")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        logger.warning("bnbprint:tokens held non-JSON data, starting fresh")
        return []


async def save_snapshot(tokens: list[dict]) -> None:
    # Keep the most recently touched tokens first, cap the list, and make
    # sure every value is JSON-serializable (datetimes -> isoformat).
    trimmed = tokens[-MAX_TOKENS:] if len(tokens) > MAX_TOKENS else tokens
    await _set("bnbprint:tokens", json.dumps(trimmed, default=str))


# --- Stats ------------------------------------------------------------------

async def get_stats() -> dict:
    raw = await _get("bnbprint:stats")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return {}


async def save_stats(stats: dict) -> None:
    await _set("bnbprint:stats", json.dumps(stats, default=str))


# --- Alerts -------------------------------------------------------------

async def append_alert(alert: dict) -> None:
    await _pipeline([
        ["LPUSH", "bnbprint:alerts", json.dumps(alert, default=str)],
        ["LTRIM", "bnbprint:alerts", 0, MAX_ALERTS - 1],
    ])


async def get_alerts(limit: int = 50) -> list[dict]:
    results = await _pipeline([["LRANGE", "bnbprint:alerts", 0, limit - 1]])
    raw_list = results[0] if results else []
    out = []
    for raw in raw_list or []:
        try:
            out.append(json.loads(raw))
        except (TypeError, ValueError):
            continue
    return out


# --- Push subscriptions ---------------------------------------------------

async def add_push_subscription(sub: dict) -> None:
    endpoint = sub["endpoint"]
    await _pipeline([["HSET", "bnbprint:push_subs", endpoint, json.dumps(sub, default=str)]])


async def remove_push_subscription(endpoint: str) -> None:
    await _pipeline([["HDEL", "bnbprint:push_subs", endpoint]])


async def get_push_subscriptions() -> list[dict]:
    results = await _pipeline([["HVALS", "bnbprint:push_subs"]])
    raw_list = results[0] if results else []
    out = []
    for raw in raw_list or []:
        try:
            out.append(json.loads(raw))
        except (TypeError, ValueError):
            continue
    return out
