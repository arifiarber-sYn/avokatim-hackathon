"""ICS calendar feed so deadlines appear in Google Calendar / Outlook / phones.
The feed URL carries a long-lived signed token (no session needed by calendar apps)."""
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Deadline, Matter, User

router = APIRouter(tags=["calendar"])

FEED_SCOPE = "calendar_feed"


def _feed_token(user_id: uuid.UUID) -> str:
    return pyjwt.encode(
        {"scope": FEED_SCOPE, "sub": str(user_id)},
        settings.secret_key,
        algorithm="HS256",
    )


def _ics_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    )


@router.get("/calendar/feed-url")
async def feed_url(user: User = Depends(get_current_user)):
    token = _feed_token(user.id)
    return {"url": f"{settings.public_base_url}/api/calendar/feed.ics?token={token}"}


@router.get("/calendar/feed.ics")
async def feed(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = pyjwt.decode(token, settings.secret_key, algorithms=["HS256"])
        if payload.get("scope") != FEED_SCOPE:
            raise ValueError("wrong scope")
        user_id = uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid feed token")

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid feed token")

    horizon_past = datetime.now(UTC) - timedelta(days=30)
    rows = (
        await db.execute(
            select(Deadline, Matter.reference)
            .join(Matter, Matter.id == Deadline.matter_id)
            .where(
                Deadline.tenant_id == user.tenant_id,
                Deadline.due_at >= horizon_past,
            )
            .order_by(Deadline.due_at)
            .limit(500)
        )
    ).all()

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//BoraLaw//Deadlines//SQ",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:BoraLaw",
    ]
    for deadline, ref in rows:
        start = deadline.due_at.astimezone(UTC)
        summary = f"[{ref}] {deadline.title}"
        description = deadline.legal_basis or ""
        lines += [
            "BEGIN:VEVENT",
            f"UID:{deadline.id}@boralaw",
            f"DTSTAMP:{datetime.now(UTC):%Y%m%dT%H%M%SZ}",
            f"DTSTART:{start:%Y%m%dT%H%M%SZ}",
            f"DTEND:{start + timedelta(hours=1):%Y%m%dT%H%M%SZ}",
            f"SUMMARY:{_ics_escape(summary)}",
        ]
        if description:
            lines.append(f"DESCRIPTION:{_ics_escape(description)}")
        if deadline.status != "pending":
            lines.append("STATUS:CANCELLED" if deadline.status == "missed" else "STATUS:CONFIRMED")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")

    return Response(
        content="\r\n".join(lines) + "\r\n",
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="boralaw.ics"'},
    )
