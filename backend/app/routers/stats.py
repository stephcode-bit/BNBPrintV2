from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Token
from app.schemas import StatsOut

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    total = db.execute(select(func.count(Token.address))).scalar_one()
    bonding = db.execute(select(func.count(Token.address)).where(Token.is_bonding.is_(True))).scalar_one()
    migrated = total - bonding

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    runners_24h = db.execute(
        select(func.count(Token.address)).where(Token.is_runner.is_(True), Token.created_at >= since)
    ).scalar_one()

    avg_security = db.execute(select(func.avg(Token.security_score))).scalar_one() or 0.0
    last_token = db.execute(select(func.max(Token.created_at))).scalar_one()

    return StatsOut(
        total_tokens=total,
        bonding_tokens=bonding,
        migrated_tokens=migrated,
        runners_24h=runners_24h,
        avg_security_score=round(float(avg_security), 1),
        last_token_at=last_token,
    )
