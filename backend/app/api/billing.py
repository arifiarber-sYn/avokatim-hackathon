import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.matters import get_owned_matter
from app.database import get_db
from app.deps import get_current_user
from app.models import Contact, Expense, Invoice, InvoiceItem, Matter, Tenant, TimeEntry, User
from app.schemas.billing import (
    ExpenseIn,
    ExpenseOut,
    InvoiceCreateIn,
    InvoiceOut,
    TimeEntryIn,
    TimeEntryOut,
)
from app.services.audit import log_action
from app.services.invoice_pdf import build_invoice_pdf
from app.services.notifications import send_email

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


# ---------- Expenses (matter disbursements) ----------

@router.get("/expenses", response_model=list[ExpenseOut])
async def list_expenses(
    matter_id: uuid.UUID | None = None,
    unbilled_only: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Expense).where(Expense.tenant_id == user.tenant_id)
    if matter_id:
        stmt = stmt.where(Expense.matter_id == matter_id)
    if unbilled_only:
        stmt = stmt.where(Expense.invoice_id.is_(None), Expense.billable.is_(True))
    stmt = stmt.order_by(Expense.incurred_on.desc()).limit(500)
    return (await db.execute(stmt)).scalars().all()


@router.post("/expenses", response_model=ExpenseOut, status_code=201)
async def create_expense(
    body: ExpenseIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_owned_matter(db, user, body.matter_id)
    expense = Expense(tenant_id=user.tenant_id, user_id=user.id, **body.model_dump())
    db.add(expense)
    await db.flush()
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="expense.create",
        entity_type="expense", entity_id=str(expense.id),
        details={"amount": str(body.amount), "category": body.category},
    )
    await db.commit()
    await db.refresh(expense)
    return expense


@router.delete("/expenses/{expense_id}", status_code=204)
async def delete_expense(
    expense_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    expense = await db.get(Expense, expense_id)
    if expense is None or expense.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Expense not found")
    if expense.invoice_id is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Expense is already invoiced")
    await db.delete(expense)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="expense.delete",
        entity_type="expense", entity_id=str(expense_id),
    )
    await db.commit()


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
    contact_id = body.contact_id
    if body.matter_id:
        matter = await get_owned_matter(db, user, body.matter_id)
        if contact_id is None:
            contact_id = matter.client_id  # bill the matter's client by default

    vat_rate = body.vat_rate
    if vat_rate is None:
        tenant = await db.get(Tenant, user.tenant_id)
        vat_rate = tenant.default_vat_rate if tenant else 0

    invoice = Invoice(
        tenant_id=user.tenant_id,
        number=await _next_invoice_number(db, user.tenant_id),
        matter_id=body.matter_id,
        contact_id=contact_id,
        currency=body.currency,
        due_on=body.due_on,
        notes=body.notes,
        vat_rate=vat_rate,
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

    if body.include_unbilled_expenses and body.matter_id:
        expenses = (
            await db.execute(
                select(Expense).where(
                    Expense.tenant_id == user.tenant_id,
                    Expense.matter_id == body.matter_id,
                    Expense.invoice_id.is_(None),
                    Expense.billable.is_(True),
                )
            )
        ).scalars().all()
        for expense in expenses:
            db.add(
                InvoiceItem(
                    invoice_id=invoice.id,
                    description=f"Shpenzim {expense.incurred_on:%d.%m.%Y} — {expense.description}",
                    quantity=Decimal("1"),
                    unit_price=expense.amount,
                )
            )
            expense.invoice_id = invoice.id

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


async def _invoice_pdf_bytes(db: AsyncSession, user: User, invoice: Invoice) -> bytes:
    tenant = await db.get(Tenant, user.tenant_id)
    contact = await db.get(Contact, invoice.contact_id) if invoice.contact_id else None
    matter = await db.get(Matter, invoice.matter_id) if invoice.matter_id else None
    return build_invoice_pdf(invoice=invoice, tenant=tenant, contact=contact, matter=matter)


@router.get("/invoices/{invoice_id}/pdf")
async def invoice_pdf(
    invoice_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The fiscal invoice as a PDF — for printing or sending to the client."""
    invoice = await _load_invoice(db, user, invoice_id)
    pdf = await _invoice_pdf_bytes(db, user, invoice)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="invoice.pdf",
        entity_type="invoice", entity_id=str(invoice.id),
    )
    await db.commit()
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="fatura-{invoice.number}.pdf"'},
    )


@router.post("/invoices/{invoice_id}/send", response_model=InvoiceOut)
async def send_invoice(
    invoice_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Email the invoice PDF to the client and mark it as sent."""
    invoice = await _load_invoice(db, user, invoice_id)
    if invoice.status == "void":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invoice is void")
    contact = await db.get(Contact, invoice.contact_id) if invoice.contact_id else None
    if contact is None or not contact.email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Client has no email address")

    if invoice.issued_on is None:
        invoice.issued_on = date.today()
    pdf = await _invoice_pdf_bytes(db, user, invoice)
    tenant = await db.get(Tenant, user.tenant_id)
    sent = await send_email(
        contact.email,
        f"Fatura {invoice.number} — {tenant.name}",
        (
            f"E nderuar/i nderuar {contact.display_name},\n\n"
            f"Në bashkëngjitje gjeni faturën {invoice.number} me vlerë "
            f"{invoice.total_with_vat:.2f} {invoice.currency}"
            + (f", me afat pagese deri më {invoice.due_on:%d.%m.%Y}" if invoice.due_on else "")
            + f".\n\nMe respekt,\n{user.full_name}\n{tenant.name}\n"
        ),
        attachments=[(f"fatura-{invoice.number}.pdf", pdf, "application/pdf")],
    )
    if not sent:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Email could not be sent (SMTP)")
    if invoice.status == "draft":
        invoice.status = "sent"
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="invoice.send",
        entity_type="invoice", entity_id=str(invoice.id), details={"to": contact.email},
    )
    await db.commit()
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
