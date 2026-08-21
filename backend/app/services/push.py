"""
Standard Web Push (VAPID) notifications — no Firebase required.

Generate a VAPID keypair once with:
    python -c "from py_vapid import Vapid02; v=Vapid02(); v.generate_keys(); print(v.public_key, v.private_key)"
or the simpler `vapid --gen` CLI from the `py-vapid` package, and put the
resulting keys in VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY.
"""
import json
import logging

from pywebpush import WebPushException, webpush
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import PushSubscription

logger = logging.getLogger("bnbprint.push")
settings = get_settings()


def notify_all(db: Session, title: str, body: str, url: str = "/") -> None:
    if not settings.vapid_private_key:
        return  # push not configured — silently skip, WebSocket already covers in-app alerts

    payload = json.dumps({"title": title, "body": body, "url": url})
    subs = db.execute(select(PushSubscription)).scalars().all()

    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_subject},
            )
        except WebPushException as exc:
            logger.warning("push failed for subscription %s: %s", sub.id, exc)
            if exc.response is not None and exc.response.status_code in (404, 410):
                db.delete(sub)  # subscription expired/unsubscribed client-side
    db.commit()
