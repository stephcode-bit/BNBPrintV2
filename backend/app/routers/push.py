from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import PushSubscription
from app.schemas import PushSubscriptionIn

router = APIRouter(prefix="/api/push", tags=["push"])
settings = get_settings()


@router.get("/vapid-public-key")
def get_vapid_public_key():
    """Frontend fetches this to call PushManager.subscribe()."""
    return {"publicKey": settings.vapid_public_key}


@router.post("/subscribe", status_code=201)
def subscribe(payload: PushSubscriptionIn, db: Session = Depends(get_db)):
    existing = db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint)
    ).scalar_one_or_none()
    if existing:
        return {"status": "already_subscribed"}

    sub = PushSubscription(**payload.model_dump())
    db.add(sub)
    db.commit()
    return {"status": "subscribed"}


@router.delete("/unsubscribe", status_code=204)
def unsubscribe(endpoint: str, db: Session = Depends(get_db)):
    existing = db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    ).scalar_one_or_none()
    if existing:
        db.delete(existing)
        db.commit()
    return None
