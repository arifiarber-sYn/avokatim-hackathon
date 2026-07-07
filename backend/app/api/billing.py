import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.matters import get_owned_matter
from app.database import get_db
from app.deps import get_current_user
from app.models import Invoice, InvoiceItem, TimeEntry, User
from app.schemas.billing import InvoiceCreateIn, InvoiceOut, TimeEntryIn, TimeEntryOut
from app.services.audit import log_action

router = APIRouter(tags=["billing"])


@router.get("/time-entries", response_model=list[TimeEntryOut])
async def list_time_entries(
    matter_id: uuid.UUID | None = None,
    unbilled_only: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(TimeEntry).where(TimeEntry.tenant_id == user.tenant_id)
    if matter_id:
        stmt = stmt.where(TimeEntry.matter_id == matter_id)
    if unbilled_only:
        stmt = stmt.where(TimeEntry.invoice_id.is_(None), TimeEntry.billable.is_(True))
    stmt = stmt.order_by(TimeEntry.started_at.desc()).limit(500)
    return (await db.execute(stmt)).scalars().all()


@router.post("/time-entries", response_model=TimeEntryOut, status_code=201)
async def create_time_entry(
    body: TimeEntryIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_owned_matter(db, user, body.matter_id)
    entry = TimeEntry(tenant_id=user.tenant_id, user_id=user.id, **body.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def _next_invoice_number(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    year = date.today().year
    prefix = f"F-{year}-"
    count = (
        await db.execute(
            select(func.count(Invoice.id)).where(
                Invoice.tenant_id == tenant_id, Invoice.number.like(f"{prefix}%")
            )
        )
    ).scalar_one()
    return f"{prefix}{count + 1:04d}"


async def _load_invoice(db: AsyncSession, user: User, invoice_id: uuid.UUID) -> Invoice:
    invoice = (
        await db.execute(
            select(Invoice)
            .options(selectinload(Invoice.items))
            .where(Invoice.id == invoice_id, Invoice.tenant_id == user.tenant_id)
        )
    ).scalar_one_or_none()
    if invoice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invoice not found")
    return invoice


@router.get("/invoices", response_model=list[InvoiceOut])
async def list_invoices(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(Invoice.tenant_id == user.tenant_id)
        .order_by(Invoice.created_at.desc())
        .limit(200)
    )
    return (await db.execute(stmt)).scalars().all()


@router.post("/invoices", response_model=InvoiceOut, status_code=201)
async def create_invoice(
    body: InvoiceCreateIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.matter_id:
        await get_owned_matter(db, user, body.matter_id)

    invoice = Invoice(
        tenant_id=user.tenant_id,
        number=await _next_invoice_number(db, user.tenant_id),
        matter_id=body.matter_id,
        contact_id=body.contact_id,
        currency=body.currency,
        due_on=body.due_on,
        notes=body.notes,
    )
    db.add(invoice)
    await db.flush()

    for item in body.items:
        db.add(InvoiceItem(invoice_id=invoice.id, **item.model_dump()))

    if body.include_unbilled_time and body.matter_id:
        entries = (
            await db.execute(
                select(TimeEntry).where(
                    TimeEntry.tenant_id == user.tenant_id,
                    TimeEntry.matter_id == body.matter_id,
                    TimeEntry.invoice_id.is_(None),
                    TimeEntry.billable.is_(True),
                )
            )
        ).scalars().all()
        for entry in entries:
            rate = entry.hourly_rate or Decimal("0")
            hours = Decimal(entry.minutes) / Decimal(60)
            db.add(
                InvoiceItem(
                    invoice_id=invoice.id,
                    description=f"{entry.started_at:%d.%m.%Y} — {entry.description}",
                    quantity=hours.quantize(Decimal("0.01")),
                    unit_price=rate,
                )
            )
            entry.invoice_id = invoice.id

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="invoice.create",
        entity_type="invoice", entity_id=str(invoice.id), details={"number": invoice.number},
    )
    await db.commit()
    return await _load_invoice(db, user, invoice.id)


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(
    invoice_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _load_invoice(db, user, invoice_id)


@router.patch("/invoices/{invoice_id}/status", response_model=InvoiceOut)
async def set_invoice_status(
    invoice_id: uuid.UUID,
    new_status: str,
    payment_reference: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if new_status not in ("draft", "sent", "paid", "void"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status")
    invoice = await _load_invoice(db, user, invoice_id)
    invoice.status = new_status
    if new_status == "sent" and invoice.issued_on is None:
        invoice.issued_on = date.today()
    if new_status == "paid":
        invoice.paid_on = date.today()
        if payment_reference:
            invoice.payment_reference = payment_reference[:128]
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="invoice.status",
        entity_type="invoice", entity_id=str(invoice.id),
        details={"status": new_status, "payment_reference": payment_reference},
    )
    await db.commit()
    return await _load_invoice(db, user, invoice_id)
