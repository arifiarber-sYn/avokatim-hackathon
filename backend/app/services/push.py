"""Web Push notifications for the PWA (deadline reminders on the phone).
Uses VAPID keys from settings; disabled when keys are not configured."""
import asyncio
import json
import logging
import uuid

from pywebpush import WebPushException, webpush
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import PushSubscription

logger = logging.getLogger(__name__)


def push_enabled() -> bool:
    return bool(settings.vapid_public_key and settings.vapid_private_key)


def _send_one_sync(sub: dict, payload: str) -> None:
    webpush(
        subscription_info=sub,
        data=payload,
        vapid_private_key=settings.vapid_private_key,
        vapid_claims={"sub": settings.vapid_subject},
        ttl=24 * 3600,
    )


async def send_push_to_user(
    db: AsyncSession, user_id: uuid.UUID, *, title: str, body: str, url: str = "/dashboard"
) -> int:
    """Send a notification to all of the user's subscribed devices.
    Dead subscriptions (410/404) are removed. Returns how many were delivered."""
    if not push_enabled():
        return 0
    subs = (
        await db.execute(select(PushSubscription).where(PushSubscription.user_id == user_id))
    ).scalars().all()
    if not subs:
        return 0

    payload = json.dumps({"title": title, "body": body, "url": url})
    delivered = 0
    for sub in subs:
        info = {
            "endpoint": sub.endpoint,
            "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
        }
        try:
            await asyncio.to_thread(_send_one_sync, info, payload)
            delivered += 1
        except WebPushException as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code in (404, 410):
                await db.execute(
                    delete(PushSubscription).where(PushSubscription.id == sub.id)
                )
                logger.info("Removed dead push subscription %s", sub.id)
            else:
                logger.warning("Push to %s failed: %s", sub.endpoint[:60], exc)
        except Exception as exc:
            logger.warning("Push failed: %s", exc)
    await db.commit()
    return delivered
