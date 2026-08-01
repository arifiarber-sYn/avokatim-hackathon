"""Token-less inbound email classification (D-043 F4): mail whose sender
matched a known contact is parked as an EmailSuggestion; the lawyer accepts
(files it into the matter) or dismisses. Nothing is filed automatically."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.matters import get_owned_matter, restricted_visibility_filter
from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Contact, EmailSuggestion, Matter, User
from app.schemas.matters import EmailSuggestionOut
from app.services.audit import log_action

router = APIRouter(tags=["email-suggestions"])


def _out(sug: EmailSuggestion, matter: Matter, contact: Contact | None) -> EmailSuggestionOut:
    out = EmailSuggestionOut.model_validate(sug)
    out.matter_reference = matter.reference
    out.matter_title = matter.title
    out.contact_name = contact.display_name if contact else None
    return out


@router.get("/email-suggestions", response_model=list[EmailSuggestionOut])
async def pending_email_suggestions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pending sender-matched emails across the office (dashboard card)."""
    stmt = (
        select(EmailSuggestion, Matter, Contact)
        .join(Matter, Matter.id == EmailSuggestion.matter_id)
        .outerjoin(Contact, Contact.id == EmailSuggestion.contact_id)
        .where(
            EmailSuggestion.tenant_id == user.tenant_id,
            EmailSuggestion.status == "pending",
            restricted_visibility_filter(user),
        )
        .order_by(EmailSuggestion.created_at.desc())
        .limit(50)
    )
    return [
        _out(sug, matter, contact)
        for sug, matter, contact in (await db.execute(stmt)).all()
    ]


async def _get_owned_email_suggestion(
    db: AsyncSession, user: User, suggestion_id: uuid.UUID
) -> EmailSuggestion:
    sug = await db.get(EmailSuggestion, suggestion_id)
    if sug is None or sug.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Suggestion not found")
    await get_owned_matter(db, user, sug.matter_id)  # enforces restricted access
    if sug.status != "pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Suggestion already handled")
    return sug


@router.post("/email-suggestions/{suggestion_id}/accept", status_code=204)
async def accept_email_suggestion(
    suggestion_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """File the parked email into the matter — note, attachments and the
    deadline scan, exactly like a token-addressed email."""
    from app.services.email_ingest import file_suggested_message

    sug = await _get_owned_email_suggestion(db, user, suggestion_id)
    await file_suggested_message(db, sug)
    sug.status = "accepted"
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id,
        action="email_suggestion.accept", entity_type="email_suggestion",
        entity_id=str(sug.id), details={"sender": sug.sender},
    )
    await db.commit()


@router.post("/email-suggestions/{suggestion_id}/dismiss", status_code=204)
async def dismiss_email_suggestion(
    suggestion_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss the suggestion and delete the parked raw message."""
    sug = await _get_owned_email_suggestion(db, user, suggestion_id)
    sug.status = "dismissed"
    (settings.documents_dir / sug.raw_path).unlink(missing_ok=True)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id,
        action="email_suggestion.dismiss", entity_type="email_suggestion",
        entity_id=str(sug.id), details={"sender": sug.sender},
    )
    await db.commit()
