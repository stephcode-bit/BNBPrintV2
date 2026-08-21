"""
Background orchestration: wires the chain listener's discovery events into
the DB + WebSocket broadcast, and runs periodic jobs that refresh bonding
tokens' security/progress data and prune stale rows.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models import Alert, Token
from app.schemas import TokenOut
from app.services import chain_listener, push
from app.services.chain_listener import process_token_pipeline
from app.ws_manager import manager

logger = logging.getLogger("bnbprint.tasks")
settings = get_settings()


async def _on_new_token(token: dict):
    enriched = await process_token_pipeline(token)

    db = SessionLocal()
    try:
        existing = db.get(Token, enriched["address"])
        if existing:
            for key, value in enriched.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            row = existing
        else:
            row = Token(**{k: v for k, v in enriched.items() if hasattr(Token, k)})
            db.add(row)
        db.commit()
        db.refresh(row)

        alert_type = "runner" if row.is_runner else "new_token"
        message = (
            f"🚀 {row.symbol} flagged as a likely runner ({row.runner_score:.0f}/100)"
            if row.is_runner
            else f"New token detected: {row.symbol} on {row.bonding_platform or row.dex or 'DEX'}"
        )
        alert = Alert(token_address=row.address, alert_type=alert_type, message=message)
        db.add(alert)
        db.commit()

        out = TokenOut.model_validate(row).model_dump()
        await manager.broadcast("new_token", out)
        if row.is_runner:
            await manager.broadcast("runner_flagged", out)
            push.notify_all(
                db,
                title=f"🚀 Runner: {row.symbol}",
                body=f"Runner score {row.runner_score:.0f}/100 · security {row.security_score:.0f}/100",
                url=f"/token/{row.address}",
            )
    finally:
        db.close()


async def start_chain_listener():
    """Runs forever as a background task from FastAPI's lifespan."""
    while True:
        try:
            await chain_listener.run_listener(_on_new_token)
        except Exception:
            logger.exception("chain listener crashed, restarting in 5s")
            await asyncio.sleep(5)


async def refresh_bonding_tokens_loop():
    """Every BONDING_REFRESH_INTERVAL seconds, re-run the pipeline for
    tokens still bonding so progress/security/runner scores stay current."""
    while True:
        await asyncio.sleep(settings.bonding_refresh_interval)
        db = SessionLocal()
        try:
            stmt = select(Token).where(Token.is_bonding.is_(True)).limit(50)
            tokens = db.execute(stmt).scalars().all()
            for row in tokens:
                token_dict = {
                    "address": row.address,
                    "symbol": row.symbol,
                    "name": row.name,
                    "decimals": row.decimals,
                    "pair_address": row.pair_address,
                    "factory": row.factory,
                    "dex": row.dex,
                    "bonding_platform": row.bonding_platform,
                    "creation_block": row.creation_block,
                    "creation_timestamp": row.creation_timestamp or datetime.now(timezone.utc),
                }
                try:
                    enriched = await process_token_pipeline(token_dict)
                except Exception:
                    logger.exception("refresh failed for %s", row.address)
                    continue

                was_bonding = row.is_bonding
                for key, value in enriched.items():
                    if hasattr(row, key):
                        setattr(row, key, value)
                db.commit()
                db.refresh(row)

                out = TokenOut.model_validate(row).model_dump()
                await manager.broadcast("token_updated", out)

                if was_bonding and not row.is_bonding:
                    alert = Alert(
                        token_address=row.address,
                        alert_type="bonding_complete",
                        message=f"{row.symbol} finished bonding and migrated to the DEX",
                    )
                    db.add(alert)
                    db.commit()
                    await manager.broadcast("bonding_complete", out)
        finally:
            db.close()


async def cleanup_stale_tokens_loop():
    """Prunes tokens that never gained traction, to keep the feed relevant."""
    while True:
        await asyncio.sleep(3600)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.stale_token_cleanup_hours)
        db = SessionLocal()
        try:
            stmt = select(Token).where(
                Token.created_at < cutoff,
                Token.is_bonding.is_(True),
                Token.runner_score < 20,
            )
            stale = db.execute(stmt).scalars().all()
            for row in stale:
                db.delete(row)
            if stale:
                db.commit()
                logger.info("cleaned up %d stale tokens", len(stale))
        finally:
            db.close()
