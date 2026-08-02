"""In-app notification center (D-054).

`notify()` is the single entry point every feature calls: it writes the
bell row and — honoring each user's interrupt-budget preference — fans out
Web Push. Email/SMS stay where they are; this is the in-app layer that was
missing. Does not commit; the caller owns the transaction.
"""
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification, User
from app.services.push import push_enabled, send_push_to_user

logger = logging.getLogger(__name__)


def _wants_push(user: User, kind: str) -> bool:
    prefs = user.notification_prefs or {}
    return prefs.get(kind, "push") == "push"


async def notify(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    kind: str,
    title: str,
    body: str | None = None,
    url: str | None = None,
    user_id: uuid.UUID | None = None,
    push: bool = True,
) -> Notification:
    """Create a bell notification (user_id=None → whole tenant) and send
    Web Push to each recipient whose interrupt budget allows this kind."""
    row = Notification(
        tenant_id=tenant_id,
        user_id=user_id,
        kind=kind,
        title=title[:300],
        body=body,
        url=url[:300] if url else None,
    )
    db.add(row)
    await db.flush()

    if push and push_enabled():
        if user_id is not None:
            recipients = [await db.get(User, user_id)]
        else:
            recipients = (
                (
                    await db.execute(
                        select(User).where(
                            User.tenant_id == tenant_id, User.is_active.is_(True)
                        )
                    )
                )
                .scalars()
                .all()
            )
        for user in recipients:
            if user is None or not _wants_push(user, kind):
                continue
            try:
                await send_push_to_user(
                    db, user.id, title=title, body=body or "", url=url or "/dashboard"
                )
            except Exception as exc:
                logger.warning("Push fan-out failed for %s: %s", user.id, exc)
    return row
