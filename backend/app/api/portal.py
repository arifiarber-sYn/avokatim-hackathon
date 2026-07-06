"""Client portal: a client logs in with email + portal password and sees the
status, deadlines (hearings only) and shared documents of their matters."""
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Contact, Deadline, Matter, User
from app.security import hash_password, verify_password
from app.services.audit import log_action

router = APIRouter(prefix="/portal", tags=["portal"])
portal_bearer = HTTPBearer(auto_error=False)


class PortalInviteIn(BaseModel):
    contact_id: uuid.UUID
    password: str


class PortalLoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/invite")
async def invite_client(
    body: PortalInviteIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The lawyer enables portal access for a client contact."""
    contact = await db.get(Contact, body.contact_id)
    if contact is None or contact.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found")
    if not contact.email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Contact has no email")
    contact.portal_password_hash = hash_password(body.password)
    contact.portal_enabled = True
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="portal.invite",
        entity_type="contact", entity_id=str(contact.id),
    )
    await db.commit()
    return {"enabled": True}


@router.post("/login")
async def portal_login(body: PortalLoginIn, db: AsyncSession = Depends(get_db)):
    contact = (
        await db.execute(
            select(Contact).where(
                Contact.email == body.email.lower(), Contact.portal_enabled.is_(True)
            )
        )
    ).scalar_one_or_none()
    if (
        contact is None
        or not contact.portal_password_hash
        or not verify_password(body.password, contact.portal_password_hash)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    now = datetime.now(UTC)
    token = pyjwt.encode(
        {"portal_contact": str(contact.id), "iat": now, "exp": now + timedelta(hours=12)},
        settings.secret_key,
        algorithm="HS256",
    )
    return {"access_token": token, "client_name": contact.display_name}


async def _portal_contact(
    creds: HTTPAuthorizationCredentials | None = Depends(portal_bearer),
    db: AsyncSession = Depends(get_db),
) -> Contact:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = pyjwt.decode(creds.credentials, settings.secret_key, algorithms=["HS256"])
        contact_id = uuid.UUID(payload["portal_contact"])
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    contact = await db.get(Contact, contact_id)
    if contact is None or not contact.portal_enabled:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Portal access disabled")
    return contact


@router.get("/my-matters")
async def my_matters(
    contact: Contact = Depends(_portal_contact),
    db: AsyncSession = Depends(get_db),
):
    matters = (
        await db.execute(
            select(Matter).where(
                Matter.client_id == contact.id, Matter.status.notin_(["archived"])
            )
        )
    ).scalars().all()
    result = []
    for m in matters:
        hearings = (
            await db.execute(
                select(Deadline).where(
                    Deadline.matter_id == m.id,
                    Deadline.kind == "hearing",
                    Deadline.status == "pending",
                )
            )
        ).scalars().all()
        result.append(
            {
                "reference": m.reference,
                "title": m.title,
                "status": m.status,
                "court_name": m.court_name,
                "upcoming_hearings": [
                    {"title": h.title, "at": h.due_at.isoformat()} for h in hearings
                ],
            }
        )
    return result
