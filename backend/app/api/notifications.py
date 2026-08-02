"""Notification center API (D-054): bell list, read state, live unread
stream (SSE) and the per-user interrupt-budget preferences."""
import asyncio
import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal, get_db
from app.deps import get_current_user
from app.models import Notification, User
from app.models.notifications import NOTIFICATION_KINDS

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _visible(user: User):
    return (
        Notification.tenant_id == user.tenant_id,
        or_(Notification.user_id.is_(None), Notification.user_id == user.id),
    )


class NotificationOut(BaseModel):
    id: uuid.UUID
    kind: str
    title: str
    body: str | None
    url: str | None
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    limit: int = 30,
    kind: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Notification)
        .where(*_visible(user))
        .order_by(Notification.created_at.desc())
        .limit(min(limit, 100))
    )
    if kind:
        stmt = stmt.where(Notification.kind == kind)
    rows = (await db.execute(stmt)).scalars().all()
    return rows


async def _unread_count(db: AsyncSession, user: User) -> int:
    return (
        await db.execute(
            select(func.count(Notification.id)).where(
                *_visible(user), Notification.read_at.is_(None)
            )
        )
    ).scalar_one()


@router.get("/unread-count")
async def unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return {"unread": await _unread_count(db, user)}


@router.post("/{notification_id}/read", status_code=204)
async def mark_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await db.get(Notification, notification_id)
    if row is None or row.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    if row.read_at is None:
        row.read_at = datetime.now(UTC)
        await db.commit()


@router.post("/read-all", status_code=204)
async def mark_all_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(*_visible(user), Notification.read_at.is_(None))
        .values(read_at=datetime.now(UTC))
    )
    await db.commit()


@router.get("/stream")
async def stream(user: User = Depends(get_current_user)):
    """Lightweight SSE: emits the unread count whenever it changes.
    The client falls back to polling if the stream drops."""

    async def gen():
        last: int | None = None
        # ~15 min per connection, then the client reconnects
        for _ in range(60):
            async with SessionLocal() as db:
                count = await _unread_count(db, user)
            if count != last:
                last = count
                yield f"data: {json.dumps({'unread': count})}\n\n"
            else:
                yield ": keepalive\n\n"
            await asyncio.sleep(15)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------- interrupt budget (per-kind delivery preference) ----------

class PrefsIn(BaseModel):
    prefs: dict[str, str]


@router.get("/prefs")
async def get_prefs(user: User = Depends(get_current_user)):
    return {"kinds": list(NOTIFICATION_KINDS), "prefs": user.notification_prefs or {}}


@router.put("/prefs")
async def put_prefs(
    body: PrefsIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    clean = {
        k: v
        for k, v in body.prefs.items()
        if k in NOTIFICATION_KINDS and v in ("push", "center")
    }
    row = await db.get(User, user.id)
    row.notification_prefs = clean
    await db.commit()
    return {"kinds": list(NOTIFICATION_KINDS), "prefs": clean}
