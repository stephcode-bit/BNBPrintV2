"""
Web Push (VAPID) sender for scan_runner.py — same standard Web Push as
app/services/push.py, but reading subscriptions from Upstash (via
app/services/store.py) instead of a Postgres session, since scan_runner.py
has no database. See app/services/push.py's docstring for how to generate
a VAPID keypair; the keys are used identically here.
"""
import json
import logging

from pywebpush import WebPushException, webpush

from app.config import get_settings
from app.services import store

logger = logging.getLogger("bnbprint.push_runner")
settings = get_settings()


async def notify_all(title: str, body: str, url: str = "/") -> None:
    if not settings.vapid_private_key:
        return  # push not configured — skip silently, the dashboard itself still shows the runner

    payload = json.dumps({"title": title, "body": body, "url": url})
    subs = await store.get_push_subscriptions()

    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub["endpoint"],
                    "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
                },
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_subject},
            )
        except WebPushException as exc:
            logger.warning("push failed for %s: %s", sub.get("endpoint", "?")[:40], exc)
            if exc.response is not None and exc.response.status_code in (404, 410):
                await store.remove_push_subscription(sub["endpoint"])  # expired/unsubscribed client-side
        except Exception:
            logger.exception("unexpected push failure for %s", sub.get("endpoint", "?")[:40])
