"""CSV data migration: bring existing clients and matters into BoraLaw.

Contacts CSV columns (header row required, extra columns ignored):
    display_name*, kind, email, phone, address, national_id, notes
Matters CSV columns:
    title*, practice_area, status, client_name, court_name,
    court_case_number, opened_on (YYYY-MM-DD), description
A client_name that matches an existing contact (case-insensitive) is linked;
otherwise a new contact is created.
"""
import csv
import io
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.matters import _next_reference
from app.database import get_db
from app.deps import get_current_user
from app.models import Contact, Jurisdiction, Matter, User
from app.models.matters import MATTER_STATUSES, PRACTICE_AREAS
from app.services.audit import log_action

router = APIRouter(prefix="/import", tags=["import"])

MAX_ROWS = 2000


def _read_csv(content: bytes) -> list[dict]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CSV has no header row")
    rows = [
        {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        for row in reader
    ]
    if len(rows) > MAX_ROWS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Too many rows (max {MAX_ROWS})")
    return rows


@router.post("/contacts")
async def import_contacts(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = _read_csv(await file.read())
    existing = {
        name.lower()
        for (name,) in (
            await db.execute(
                select(Contact.display_name).where(Contact.tenant_id == user.tenant_id)
            )
        ).all()
    }
    created, skipped, errors = 0, 0, []
    for i, row in enumerate(rows, start=2):  # 1 = header line
        name = row.get("display_name") or row.get("emri") or ""
        if not name:
            errors.append(f"Line {i}: missing display_name")
            continue
        if name.lower() in existing:
            skipped += 1
            continue
        db.add(
            Contact(
                tenant_id=user.tenant_id,
                display_name=name[:255],
                kind=(row.get("kind") or "person")[:16],
                email=(row.get("email") or None),
                phone=(row.get("phone") or row.get("telefoni") or None),
                address=(row.get("address") or row.get("adresa") or None),
                national_id=(row.get("national_id") or None),
                notes=(row.get("notes") or None),
            )
        )
        existing.add(name.lower())
        created += 1
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="import.contacts",
        entity_type="tenant", entity_id=str(user.tenant_id),
        details={"created": created, "skipped": skipped},
    )
    await db.commit()
    return {"created": created, "skipped": skipped, "errors": errors[:20]}


@router.post("/matters")
async def import_matters(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = _read_csv(await file.read())
    jurisdiction = (
        await db.execute(select(Jurisdiction).where(Jurisdiction.code == "XK"))
    ).scalar_one()

    async def _find_or_create_contact(name: str) -> uuid.UUID:
        contact = (
            await db.execute(
                select(Contact).where(
                    Contact.tenant_id == user.tenant_id,
                    func.lower(Contact.display_name) == name.lower(),
                )
            )
        ).scalars().first()
        if contact is None:
            contact = Contact(tenant_id=user.tenant_id, display_name=name[:255])
            db.add(contact)
            await db.flush()
        return contact.id

    created, errors = 0, []
    for i, row in enumerate(rows, start=2):
        title = row.get("title") or row.get("titulli") or ""
        if not title:
            errors.append(f"Line {i}: missing title")
            continue
        area = (row.get("practice_area") or "civil").lower()
        if area not in PRACTICE_AREAS:
            area = "other"
        matter_status = (row.get("status") or "open").lower()
        if matter_status not in MATTER_STATUSES:
            matter_status = "open"
        opened_on: date | None = None
        raw_date = row.get("opened_on") or ""
        if raw_date:
            for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
                try:
                    opened_on = datetime.strptime(raw_date, fmt).date()
                    break
                except ValueError:
                    continue
            if opened_on is None:
                errors.append(f"Line {i}: unreadable date '{raw_date}' (use YYYY-MM-DD)")
        client_id = None
        client_name = row.get("client_name") or row.get("klienti") or ""
        if client_name:
            client_id = await _find_or_create_contact(client_name)
        matter = Matter(
            tenant_id=user.tenant_id,
            reference=await _next_reference(db, user.tenant_id, area),
            title=title[:500],
            description=(row.get("description") or None),
            practice_area=area,
            status=matter_status,
            jurisdiction_id=jurisdiction.id,
            responsible_user_id=user.id,
            client_id=client_id,
            court_name=(row.get("court_name") or None),
            court_case_number=(row.get("court_case_number") or None),
            opened_on=opened_on or date.today(),
        )
        db.add(matter)
        await db.flush()
        created += 1
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="import.matters",
        entity_type="tenant", entity_id=str(user.tenant_id),
        details={"created": created},
    )
    await db.commit()
    return {"created": created, "errors": errors[:20]}
