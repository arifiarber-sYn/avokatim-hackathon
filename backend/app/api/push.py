"""Web Push subscription management for the PWA."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import PushSubscription, User
from app.services.push import push_enabled

router = APIRouter(prefix="/push", tags=["push"])


class SubscriptionIn(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    user_agent: str | None = None


@router.get("/vapid-public-key")
async def vapid_public_key(user: User = Depends(get_current_user)):
    return {"key": settings.vapid_public_key, "enabled": push_enabled()}


@router.post("/subscribe", status_code=201)
async def subscribe(
    body: SubscriptionIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = (
        await db.execute(
            select(PushSubscription).where(PushSubscription.endpoint == body.endpoint)
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.user_id = user.id
        existing.p256dh = body.p256dh
        existing.auth = body.auth
    else:
        db.add(
            PushSubscription(
                tenant_id=user.tenant_id,
                user_id=user.id,
                endpoint=body.endpoint,
                p256dh=body.p256dh,
                auth=body.auth,
                user_agent=(body.user_agent or "")[:255] or None,
            )
        )
    await db.commit()
    return {"subscribed": True}


class UnsubscribeIn(BaseModel):
    endpoint: str


@router.post("/unsubscribe")
async def unsubscribe(
    body: UnsubscribeIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(PushSubscription).where(
            PushSubscription.endpoint == body.endpoint,
            PushSubscription.user_id == user.id,
        )
    )
    await db.commit()
    return {"subscribed": False}
