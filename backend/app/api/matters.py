import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models import Contact, Jurisdiction, Matter, MatterNote, MatterParty, User
from app.schemas.matters import (
    MatterIn,
    MatterNoteIn,
    MatterNoteOut,
    MatterOut,
    MatterPartyIn,
    MatterPartyOut,
    MatterUpdate,
)
from app.services.audit import log_action

router = APIRouter(prefix="/matters", tags=["matters"])

_AREA_CODE = {
    "civil": "C", "criminal": "P", "family": "F", "commercial": "K",
    "labor": "L", "administrative": "A", "other": "X",
}


async def _next_reference(db: AsyncSession, tenant_id: uuid.UUID, practice_area: str) -> str:
    """Sequential per-tenant reference like 2026-C-0007."""
    year = date.today().year
    prefix = f"{year}-{_AREA_CODE.get(practice_area, 'X')}-"
    count = (
        await db.execute(
            select(func.count(Matter.id)).where(
                Matter.tenant_id == tenant_id, Matter.reference.like(f"{prefix}%")
            )
        )
    ).scalar_one()
    return f"{prefix}{count + 1:04d}"


async def get_owned_matter(db: AsyncSession, user: User, matter_id: uuid.UUID) -> Matter:
    matter = (
        await db.execute(
            select(Matter)
            .options(selectinload(Matter.client))
            .where(Matter.id == matter_id, Matter.tenant_id == user.tenant_id)
        )
    ).scalar_one_or_none()
    if matter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Matter not found")
    return matter


@router.get("", response_model=list[MatterOut])
async def list_matters(
    status_filter: str | None = None,
    practice_area: str | None = None,
    q: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Matter)
        .options(selectinload(Matter.client))
        .where(Matter.tenant_id == user.tenant_id)
    )
    if status_filter:
        stmt = stmt.where(Matter.status == status_filter)
    if practice_area:
        stmt = stmt.where(Matter.practice_area == practice_area)
    if q:
        needle = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(Matter.title).like(needle) | func.lower(Matter.reference).like(needle)
        )
    stmt = stmt.order_by(Matter.created_at.desc()).limit(200)
    return (await db.execute(stmt)).scalars().all()


@router.post("", response_model=MatterOut, status_code=status.HTTP_201_CREATED)
async def create_matter(
    body: MatterIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    jurisdiction = (
        await db.execute(select(Jurisdiction).where(Jurisdiction.code == body.jurisdiction_code))
    ).scalar_one_or_none()
    if jurisdiction is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown jurisdiction")

    data = body.model_dump(exclude={"jurisdiction_code"})
    matter = Matter(
        tenant_id=user.tenant_id,
        reference=await _next_reference(db, user.tenant_id, body.practice_area),
        jurisdiction_id=jurisdiction.id,
        responsible_user_id=user.id,
        opened_on=data.pop("opened_on") or date.today(),
        **data,
    )
    db.add(matter)
    await db.flush()
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="matter.create",
        entity_type="matter", entity_id=str(matter.id), details={"reference": matter.reference},
    )
    await db.commit()
    return await get_owned_matter(db, user, matter.id)


@router.get("/{matter_id}", response_model=MatterOut)
async def get_matter(
    matter_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_owned_matter(db, user, matter_id)


@router.patch("/{matter_id}", response_model=MatterOut)
async def update_matter(
    matter_id: uuid.UUID,
    body: MatterUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    matter = await get_owned_matter(db, user, matter_id)
    changes = body.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(matter, k, v)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="matter.update",
        entity_type="matter", entity_id=str(matter.id), details={"fields": list(changes)},
    )
    await db.commit()
    return await get_owned_matter(db, user, matter.id)


@router.get("/{matter_id}/parties", response_model=list[MatterPartyOut])
async def list_parties(
    matter_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_owned_matter(db, user, matter_id)
    stmt = (
        select(MatterParty)
        .options(selectinload(MatterParty.contact))
        .where(MatterParty.matter_id == matter_id)
    )
    return (await db.execute(stmt)).scalars().all()


@router.post("/{matter_id}/parties", response_model=MatterPartyOut, status_code=201)
async def add_party(
    matter_id: uuid.UUID,
    body: MatterPartyIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_owned_matter(db, user, matter_id)
    contact = await db.get(Contact, body.contact_id)
    if contact is None or contact.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found")
    party = MatterParty(matter_id=matter_id, **body.model_dump())
    db.add(party)
    await db.commit()
    stmt = (
        select(MatterParty)
        .options(selectinload(MatterParty.contact))
        .where(MatterParty.id == party.id)
    )
    return (await db.execute(stmt)).scalar_one()


@router.get("/{matter_id}/notes", response_model=list[MatterNoteOut])
async def list_notes(
    matter_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_owned_matter(db, user, matter_id)
    stmt = (
        select(MatterNote)
        .where(MatterNote.matter_id == matter_id)
        .order_by(MatterNote.created_at.desc())
    )
    return (await db.execute(stmt)).scalars().all()


@router.post("/{matter_id}/notes", response_model=MatterNoteOut, status_code=201)
async def add_note(
    matter_id: uuid.UUID,
    body: MatterNoteIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_owned_matter(db, user, matter_id)
    note = MatterNote(
        tenant_id=user.tenant_id, matter_id=matter_id, author_id=user.id, body=body.body
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note
