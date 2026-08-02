"""Platform feedback channel: any visitor can send a complaint, suggestion
or problem report to the platform operator (no account needed) via /kontakti.
Superadmins review and mark entries handled in the /platform panel."""
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.marketplace import _ip, _rate_limit
from app.database import get_db
from app.deps import require_superadmin
from app.models import PlatformFeedback, User
from app.services.audit import log_action
from app.services.notifications import _is_test_recipient
from app.services.ops_notify import notify_ops

public_router = APIRouter(prefix="/public", tags=["public"])
admin_router = APIRouter(prefix="/platform", tags=["platform"])


class FeedbackIn(BaseModel):
    kind: str = Field(pattern="^(ankese|sugjerim|problem)$")
    name: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    message: str = Field(min_length=10, max_length=5000)


@public_router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    body: FeedbackIn,
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # No operator email here on purpose: feedback lives in the /platform
    # review queue (with an unhandled-count badge), keeping the owner's
    # personal inbox reserved for real correspondence. The operator assistant
    # gets a Telegram heads-up instead.
    await _rate_limit("public_feedback", _ip(request), limit=5, window_seconds=3600)
    entry = PlatformFeedback(
        kind=body.kind,
        name=(body.name or "").strip() or None,
        email=str(body.email) if body.email else None,
        message=body.message.strip(),
    )
    db.add(entry)
    await db.commit()
    if not (body.email and _is_test_recipient(str(body.email))):
        background.add_task(
            notify_ops, "feedback",
            f"Feedback i ri ({body.kind}) nga {entry.name or 'anonim'}: "
            f"{entry.message[:300]} — shqyrtohet te /platform.",
        )
    return {"received": True}


# ---------- frontend error relay (D-054 F6) ----------

class ClientErrorIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    stack: str | None = Field(default=None, max_length=8000)
    url: str | None = Field(default=None, max_length=500)


@public_router.post("/client-error", status_code=status.HTTP_202_ACCEPTED)
async def report_client_error(body: ClientErrorIn, request: Request):
    """Browser errors land in the self-hosted GlitchTip (when configured)
    instead of vanishing in users' consoles. No PII: message + stack + URL."""
    from app.config import settings

    await _rate_limit("client_error", _ip(request), limit=10, window_seconds=3600)
    if settings.sentry_dsn:
        import sentry_sdk

        with sentry_sdk.new_scope() as scope:
            scope.set_tag("source", "frontend")
            scope.set_context(
                "browser",
                {
                    "url": body.url or "",
                    "user_agent": request.headers.get("user-agent", "")[:300],
                },
            )
            sentry_sdk.capture_message(
                f"[frontend] {body.message}\n{body.stack or ''}"[:9000], level="error"
            )
    return {"received": True}


# ---------- operator review ----------

@admin_router.get("/feedback/pending-count")
async def pending_feedback_count(
    admin: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Unhandled feedback count — drives the badge on the Platform nav item."""
    n = await db.scalar(
        select(func.count())
        .select_from(PlatformFeedback)
        .where(PlatformFeedback.status == "new")
    )
    return {"count": n or 0}


@admin_router.get("/feedback")
async def list_feedback(
    status_filter: str = "new",
    admin: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PlatformFeedback).order_by(PlatformFeedback.created_at.desc()).limit(200)
    if status_filter != "all":
        stmt = stmt.where(PlatformFeedback.status == status_filter)
    entries = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": str(e.id),
            "kind": e.kind,
            "name": e.name,
            "email": e.email,
            "message": e.message,
            "status": e.status,
            "handled_note": e.handled_note,
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]


class HandleIn(BaseModel):
    note: str | None = Field(default=None, max_length=500)


@admin_router.post("/feedback/{feedback_id}/handle")
async def handle_feedback(
    feedback_id: uuid.UUID,
    body: HandleIn,
    admin: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    entry = await db.get(PlatformFeedback, feedback_id)
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Feedback not found")
    entry.status = "handled"
    entry.handled_note = body.note
    await log_action(
        db, tenant_id=admin.tenant_id, user_id=admin.id,
        action="platform.feedback_handle", entity_type="platform_feedback",
        entity_id=str(entry.id),
    )
    await db.commit()
    return {"status": "handled"}
