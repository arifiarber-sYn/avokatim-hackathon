import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import Contact, User
from app.schemas.matters import ContactIn, ContactOut
from app.services.audit import log_action

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=list[ContactOut])
async def list_contacts(
    q: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Contact).where(Contact.tenant_id == user.tenant_id)
    if q:
        stmt = stmt.where(func.lower(Contact.display_name).contains(q.lower()))
    stmt = stmt.order_by(Contact.display_name).limit(200)
    return (await db.execute(stmt)).scalars().all()


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contact = Contact(tenant_id=user.tenant_id, **body.model_dump())
    db.add(contact)
    await db.flush()
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="contact.create",
        entity_type="contact", entity_id=str(contact.id),
    )
    await db.commit()
    await db.refresh(contact)
    return contact


async def _get_owned_contact(db: AsyncSession, user: User, contact_id: uuid.UUID) -> Contact:
    contact = await db.get(Contact, contact_id)
    if contact is None or contact.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found")
    return contact


@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact(
    contact_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_owned_contact(db, user, contact_id)


@router.put("/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: uuid.UUID,
    body: ContactIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contact = await _get_owned_contact(db, user, contact_id)
    for k, v in body.model_dump().items():
        setattr(contact, k, v)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="contact.update",
        entity_type="contact", entity_id=str(contact.id),
    )
    await db.commit()
    await db.refresh(contact)
    return contact
