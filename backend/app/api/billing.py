import uuid
from datetime import date, datetime, time as dt_time, timezone
from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.matters import get_owned_matter
from app.database import get_db
from app.jurisdictions import jurisdiction_row_for_tenant
from app.deps import get_current_user
from app.models import (
    Contact,
    Expense,
    FeeTariffItem,
    Invoice,
    InvoiceItem,
    Jurisdiction,
    Matter,
    Tenant,
    TimeEntry,
    TimeSuggestion,
    TrustTransaction,
    User,
)
from app.schemas.billing import (
    ExpenseIn,
    ExpenseOut,
    FeeTariffItemOut,
    InvoiceCreateIn,
    InvoiceOut,
    TimeEntryIn,
    TimeEntryOut,
    TrustBalanceOut,
    TrustTransactionIn,
    TrustTransactionOut,
)
from app.services.audit import log_action
from app.services.invoice_pdf import build_invoice_pdf
from app.i18n import pick_locale, tr
from app.services.notifications import send_email
from app.services.payments import create_payment_link, payments_enabled, verify_webhook_signature

router = APIRouter(tags=["billing"])
# Unauthenticated endpoints (Stripe webhook) — mounted separately in main.py
public_router = APIRouter(tags=["billing"])


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


# ---------- Passive time capture (suggestions from activity) ----------


@router.get("/time-suggestions")
async def list_time_suggestions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pending billable-time candidates derived from the audit trail."""
    stmt = (
        select(TimeSuggestion, Matter.reference, Matter.title)
        .join(Matter, Matter.id == TimeSuggestion.matter_id)
        .where(
            TimeSuggestion.tenant_id == user.tenant_id,
            TimeSuggestion.status == "pending",
        )
        .order_by(TimeSuggestion.day.desc())
        .limit(100)
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "id": str(s.id),
            "matter_id": str(s.matter_id),
            "matter_reference": ref,
            "matter_title": title,
            "day": s.day.isoformat(),
            "suggested_minutes": s.suggested_minutes,
            "description": s.description,
        }
        for s, ref, title in rows
    ]


@router.post("/time-suggestions/generate")
async def generate_time_suggestions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """On-demand scan of recent activity ('Gjenero nga aktiviteti' button)."""
    from app.services.time_capture import generate_suggestions

    created = await generate_suggestions(db, user.tenant_id)
    await db.commit()
    return {"created": created}


class TimeSuggestionAcceptIn(BaseModel):
    minutes: int | None = Field(default=None, ge=1, le=24 * 60)
    description: str | None = Field(default=None, max_length=2000)
    hourly_rate: Decimal | None = None


async def _load_suggestion(
    db: AsyncSession, user: User, suggestion_id: uuid.UUID
) -> TimeSuggestion:
    suggestion = await db.get(TimeSuggestion, suggestion_id)
    if suggestion is None or suggestion.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Suggestion not found")
    if suggestion.status != "pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Suggestion already handled")
    return suggestion


@router.post("/time-suggestions/{suggestion_id}/accept", response_model=TimeEntryOut)
async def accept_time_suggestion(
    suggestion_id: uuid.UUID,
    body: TimeSuggestionAcceptIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Turn the suggestion into a real TimeEntry (editable minutes/text)."""
    suggestion = await _load_suggestion(db, user, suggestion_id)
    await get_owned_matter(db, user, suggestion.matter_id)
    rate = body.hourly_rate
    if rate is None:
        # Default to the accepting lawyer's most recent rate
        rate = (
            await db.execute(
                select(TimeEntry.hourly_rate)
                .where(
                    TimeEntry.tenant_id == user.tenant_id,
                    TimeEntry.user_id == user.id,
                    TimeEntry.hourly_rate.is_not(None),
                )
                .order_by(TimeEntry.started_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
    entry = TimeEntry(
        tenant_id=user.tenant_id,
        matter_id=suggestion.matter_id,
        user_id=user.id,
        started_at=datetime.combine(suggestion.day, dt_time(9, 0), tzinfo=timezone.utc),
        minutes=body.minutes or suggestion.suggested_minutes,
        description=body.description or suggestion.description,
        billable=True,
        hourly_rate=rate,
    )
    db.add(entry)
    await db.flush()
    suggestion.status = "accepted"
    suggestion.time_entry_id = entry.id
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="time_suggestion.accept",
        entity_type="time_suggestion", entity_id=str(suggestion.id),
        details={"minutes": entry.minutes},
    )
    await db.commit()
    await db.refresh(entry)
    return entry


@router.post("/time-suggestions/{suggestion_id}/dismiss", status_code=204)
async def dismiss_time_suggestion(
    suggestion_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    suggestion = await _load_suggestion(db, user, suggestion_id)
    suggestion.status = "dismissed"
    await db.commit()
    return Response(status_code=204)


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


# ---------- Client funds ledger (trust accounting) ----------

async def _trust_balance(db: AsyncSession, tenant_id: uuid.UUID, matter_id: uuid.UUID) -> Decimal:
    total = (
        await db.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (TrustTransaction.kind == "deposit", TrustTransaction.amount),
                            else_=-TrustTransaction.amount,
                        )
                    ),
                    0,
                )
            ).where(
                TrustTransaction.tenant_id == tenant_id,
                TrustTransaction.matter_id == matter_id,
            )
        )
    ).scalar_one()
    return Decimal(total)


@router.get("/trust/transactions", response_model=list[TrustTransactionOut])
async def list_trust_transactions(
    matter_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(TrustTransaction).where(TrustTransaction.tenant_id == user.tenant_id)
    if matter_id:
        stmt = stmt.where(TrustTransaction.matter_id == matter_id)
    stmt = stmt.order_by(TrustTransaction.occurred_on.desc(), TrustTransaction.created_at.desc())
    return (await db.execute(stmt.limit(500))).scalars().all()


@router.get("/trust/balances", response_model=list[TrustBalanceOut])
async def trust_balances(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Current client-funds balance per matter (only matters with activity)."""
    signed = func.sum(
        case(
            (TrustTransaction.kind == "deposit", TrustTransaction.amount),
            else_=-TrustTransaction.amount,
        )
    ).label("balance")
    rows = (
        await db.execute(
            select(Matter.id, Matter.reference, Matter.title, Contact.display_name, signed)
            .join(TrustTransaction, TrustTransaction.matter_id == Matter.id)
            .outerjoin(Contact, Contact.id == Matter.client_id)
            .where(TrustTransaction.tenant_id == user.tenant_id)
            .group_by(Matter.id, Matter.reference, Matter.title, Contact.display_name)
            .order_by(Matter.reference)
        )
    ).all()
    return [
        TrustBalanceOut(
            matter_id=mid, matter_reference=ref, matter_title=title,
            client_name=client, balance=balance,
        )
        for mid, ref, title, client, balance in rows
    ]


@router.post("/trust/transactions", response_model=TrustTransactionOut, status_code=201)
async def create_trust_transaction(
    body: TrustTransactionIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    matter = await get_owned_matter(db, user, body.matter_id)
    if body.kind == "withdrawal":
        balance = await _trust_balance(db, user.tenant_id, body.matter_id)
        if body.amount > balance:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Insufficient client funds: balance is {balance:.2f}",
            )
    txn = TrustTransaction(
        tenant_id=user.tenant_id,
        created_by_id=user.id,
        contact_id=matter.client_id,
        **body.model_dump(),
    )
    db.add(txn)
    await db.flush()
    # AML (Law 05/L-096 art. 25): deposits at/over 10,000 EUR are flagged in
    # the audit trail; the UI shows a source-of-funds warning
    large_cash = body.kind == "deposit" and body.amount >= 10_000
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="trust.transaction",
        entity_type="trust_transaction", entity_id=str(txn.id),
        details={
            "kind": body.kind, "amount": str(body.amount), "matter": matter.reference,
            **({"aml_large_amount": True} if large_cash else {}),
            **({"source_of_funds": body.source_of_funds} if body.source_of_funds else {}),
        },
    )
    await db.commit()
    await db.refresh(txn)
    return txn


@router.delete("/trust/transactions/{transaction_id}", status_code=204)
async def delete_trust_transaction(
    transaction_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    txn = await db.get(TrustTransaction, transaction_id)
    if txn is None or txn.tenant_id != user.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    # Deleting a deposit must not push the matter balance negative
    if txn.kind == "deposit":
        balance = await _trust_balance(db, user.tenant_id, txn.matter_id)
        if balance - txn.amount < 0:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Deleting this deposit would make the balance negative"
            )
    await db.delete(txn)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="trust.transaction.delete",
        entity_type="trust_transaction", entity_id=str(transaction_id),
    )
    await db.commit()


# ---------- Bar association fee tariff ----------

@router.get("/fee-tariff", response_model=list[FeeTariffItemOut])
async def list_fee_tariff(
    jurisdiction_code: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if jurisdiction_code:
        jurisdiction = (
            await db.execute(select(Jurisdiction).where(Jurisdiction.code == jurisdiction_code))
        ).scalar_one_or_none()
        if jurisdiction is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Jurisdiction not found")
    else:
        jurisdiction = await jurisdiction_row_for_tenant(db, user.tenant_id)
    return (
        await db.execute(
            select(FeeTariffItem)
            .where(FeeTariffItem.jurisdiction_id == jurisdiction.id)
            .order_by(FeeTariffItem.code)
        )
    ).scalars().all()


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


# ---------- RVG calculator (DE offices, D-037) ----------


class RvgCalcIn(BaseModel):
    value_eur: Decimal = Field(gt=0, le=Decimal("100000000"))
    items: list[str] = Field(min_length=1, max_length=8)
    # VV 2300 is a Rahmengebühr (0.5-2.5); the default 1.3 can be overridden
    geschaeftsgebuehr_rate: Decimal | None = Field(
        default=None, ge=Decimal("0.5"), le=Decimal("2.5")
    )
    vat_rate: int = Field(default=19, ge=0, le=30)


async def _require_de_tenant(db: AsyncSession, user: User) -> None:
    tenant = await db.get(Tenant, user.tenant_id)
    if tenant is None or tenant.country != "DE":
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "RVG calculator is for German offices"
        )


@router.get("/fee-calc/rvg")
async def rvg_catalogue(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """The VV items the calculator offers (localized names, default rates)."""
    await _require_de_tenant(db, user)
    from app.seeds.germany import DE_RVG_TABLE, DE_RVG_VV_ITEMS

    return {"items": DE_RVG_VV_ITEMS, "legal_basis": DE_RVG_TABLE["legal_basis"]}


@router.post("/fee-calc/rvg")
async def rvg_calc(
    body: RvgCalcIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Statutory fee lines for a Gegenstandswert — ready to become invoice items."""
    await _require_de_tenant(db, user)
    from app.services import rvg

    return rvg.compute(
        body.value_eur,
        body.items,
        geschaeftsgebuehr_rate=body.geschaeftsgebuehr_rate,
        vat_rate=body.vat_rate,
    )


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
    loc = pick_locale(contact.locale, tenant.default_locale)
    body = (
        tr(loc, "email_greeting", name=contact.display_name)
        + "\n\n"
        + tr(
            loc, "email_invoice_attached",
            number=invoice.number,
            total=f"{invoice.total_with_vat:.2f}",
            currency=invoice.currency,
        )
        + (
            tr(loc, "email_invoice_due", due=f"{invoice.due_on:%d.%m.%Y}")
            if invoice.due_on
            else ""
        )
        + ".\n"
        + (
            "\n" + tr(loc, "email_invoice_paylink", link=invoice.payment_link) + "\n"
            if invoice.payment_link
            else ""
        )
        + f"\n{tr(loc, 'email_signoff')}\n{user.full_name}\n{tenant.name}\n"
    )
    sent = await send_email(
        contact.email,
        tr(loc, "email_invoice_subject", number=invoice.number, firm=tenant.name),
        body,
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


@router.post("/invoices/{invoice_id}/payment-link", response_model=InvoiceOut)
async def create_invoice_payment_link(
    invoice_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a card-payment link (Stripe Checkout) for the invoice. The link
    is stored on the invoice and included in the email sent to the client."""
    if not payments_enabled():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Card payments are not configured (Stripe)"
        )
    invoice = await _load_invoice(db, user, invoice_id)
    if invoice.status in ("paid", "void"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invoice is already settled")
    contact = await db.get(Contact, invoice.contact_id) if invoice.contact_id else None
    tenant = await db.get(Tenant, user.tenant_id)
    amount_cents = int(invoice.total_with_vat * 100)
    if amount_cents <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invoice total must be positive")
    try:
        url, session_id = await create_payment_link(
            invoice_id=str(invoice.id),
            invoice_number=invoice.number,
            amount_cents=amount_cents,
            currency=invoice.currency,
            description=f"Fatura {invoice.number} — {tenant.name}",
            customer_email=contact.email if contact else None,
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))
    invoice.payment_link = url
    invoice.stripe_session_id = session_id
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="invoice.payment_link",
        entity_type="invoice", entity_id=str(invoice.id), details={"session": session_id},
    )
    await db.commit()
    return await _load_invoice(db, user, invoice_id)


@router.get("/payments-config")
async def payments_config(user: User = Depends(get_current_user)):
    """Lets the UI decide which payment-link actions to offer: the automated
    provider button only makes sense when a provider is configured."""
    return {"auto_provider": payments_enabled()}


class ManualPayLinkIn(BaseModel):
    # Bank pay-by-link URLs (Raiffeisen/TEB) that the lawyer generates in
    # their own merchant portal — the realistic card path in Kosovo today,
    # where Stripe cannot onboard local businesses.
    url: str | None = Field(default=None, max_length=1000)


@router.put("/invoices/{invoice_id}/payment-link", response_model=InvoiceOut)
async def set_invoice_payment_link(
    invoice_id: uuid.UUID,
    body: ManualPayLinkIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Attach (or clear) a manually created payment URL to the invoice. It is
    shown in the client portal and embedded in the invoice email — same slot
    an automated provider would fill."""
    invoice = await _load_invoice(db, user, invoice_id)
    if invoice.status in ("paid", "void"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invoice is already settled")
    url = (body.url or "").strip() or None
    if url and not url.startswith("https://"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment link must be an https:// URL")
    invoice.payment_link = url
    # A manual link is not a Stripe session; drop any stale session id so the
    # webhook can never mis-match it
    invoice.stripe_session_id = None
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="invoice.payment_link_manual",
        entity_type="invoice", entity_id=str(invoice.id), details={"set": bool(url)},
    )
    await db.commit()
    return await _load_invoice(db, user, invoice_id)


@public_router.post("/stripe/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Stripe calls this when a checkout completes; marks the invoice paid.
    Handles client invoices (invoice_id), the tenant's own platform
    subscription invoices (platform_invoice_id) and consultation bookings
    (booking_id)."""
    from app.models import ConsultBooking, PlatformInvoice

    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    event = verify_webhook_signature(payload, signature)
    if event is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid signature")
    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata") or {}
        reference = f"Stripe {session.get('payment_intent', '')}"[:128]
        invoice_id = metadata.get("invoice_id")
        platform_invoice_id = metadata.get("platform_invoice_id")
        booking_id = metadata.get("booking_id")
        if booking_id:
            from app.api.bookings import _notify_lawyer_new_booking

            booking = await db.get(ConsultBooking, uuid.UUID(booking_id))
            if booking is not None and booking.status == "pending_payment":
                booking.status = "pending"
                await log_action(
                    db, tenant_id=booking.tenant_id, user_id=None,
                    action="booking.paid_online",
                    entity_type="consult_booking", entity_id=str(booking.id),
                    details={"session": session.get("id"), "reference": reference},
                )
                await db.commit()
                background.add_task(_notify_lawyer_new_booking, booking.id)
            return {"received": True}
        if invoice_id:
            invoice = await db.get(Invoice, uuid.UUID(invoice_id))
            if invoice is not None and invoice.status != "paid":
                invoice.status = "paid"
                invoice.paid_on = date.today()
                invoice.payment_reference = reference
                await log_action(
                    db, tenant_id=invoice.tenant_id, user_id=None, action="invoice.paid_online",
                    entity_type="invoice", entity_id=str(invoice.id),
                    details={"session": session.get("id")},
                )
                await db.commit()
        elif platform_invoice_id:
            pinv = await db.get(PlatformInvoice, uuid.UUID(platform_invoice_id))
            if pinv is not None and pinv.status == "open":
                pinv.status = "paid"
                pinv.paid_on = date.today()
                pinv.payment_reference = reference
                await log_action(
                    db, tenant_id=pinv.tenant_id, user_id=None,
                    action="subscription.paid_online",
                    entity_type="platform_invoice", entity_id=str(pinv.id),
                    details={"session": session.get("id")},
                )
                await db.commit()
    return {"received": True}


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
