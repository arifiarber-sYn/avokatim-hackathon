"""Platform subscription billing (D-016).

The revenue model: lawyers pay a flat per-seat monthly subscription
(Tenant.plan_price_eur, default 24 EUR) which includes the whole practice
platform plus unlimited marketplace leads. Citizens never pay. The platform
never takes a share of lawyer fees (fee splitting is an ethics violation —
it killed Avvo Legal Services).

Lifecycle:
- signup -> plan="trial" for TRIAL_DAYS (365 = the "first year free" pilot)
- upgrade (self-service or operator) -> plan=solo/firm, invoices start
- a PlatformInvoice is generated idempotently per tenant per calendar month
  by the daily billing loop (or on demand from the platform panel)
- payment: bank transfer (operator marks paid) or Stripe Checkout when
  configured; unpaid past due+grace -> marketplace claims are blocked
  (the lawyer NEVER loses access to their own data), chronic non-payment
  is handled by the operator via suspend.
"""
import asyncio
import logging
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import redis.asyncio as aioredis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import SessionLocal
from app.i18n import pick_locale, tr
from app.models import PlatformInvoice, Tenant, User
from app.services.notifications import send_email

logger = logging.getLogger(__name__)

# Days a new tenant runs free before needing a paid plan ("viti i parë
# falas" — extended from 90 on 2026-07-28 so early offices fully adopt the
# system before ever seeing an invoice)
TRIAL_DAYS = 365
# Days between issuing an invoice and its due date
INVOICE_DUE_DAYS = 14
# Days past due before marketplace claims are blocked
GRACE_DAYS = 14
# Check interval for the background loop
BILLING_CHECK_HOURS = 12

PAID_PLANS = ("solo", "firm")


def month_start(day: date | None = None) -> date:
    d = day or date.today()
    return d.replace(day=1)


def _month_end(start: date) -> date:
    nxt = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return nxt - timedelta(days=1)


async def active_seats(db: AsyncSession, tenant_id: uuid.UUID) -> int:
    count = (
        await db.execute(
            select(func.count(User.id)).where(
                User.tenant_id == tenant_id, User.is_active.is_(True)
            )
        )
    ).scalar_one()
    return max(1, count)


async def _next_number(db: AsyncSession) -> str:
    year = date.today().year
    prefix = f"P-{year}-"
    count = (
        await db.execute(
            select(func.count(PlatformInvoice.id)).where(
                PlatformInvoice.number.like(f"{prefix}%")
            )
        )
    ).scalar_one()
    return f"{prefix}{count + 1:04d}"


def tenant_is_billable(tenant: Tenant) -> bool:
    return (
        tenant.status == "active"
        and tenant.plan in PAID_PLANS
        and (tenant.plan_price_eur or Decimal("0")) > 0
    )


async def generate_invoice(
    db: AsyncSession, tenant: Tenant, period: date | None = None
) -> PlatformInvoice | None:
    """Create the subscription invoice for one calendar month. Idempotent:
    returns None when the tenant is not billable or the period is already
    invoiced."""
    if not tenant_is_billable(tenant):
        return None
    start = month_start(period)
    existing = (
        await db.execute(
            select(PlatformInvoice).where(
                PlatformInvoice.tenant_id == tenant.id,
                PlatformInvoice.period_start == start,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return None
    seats = await active_seats(db, tenant.id)
    unit = Decimal(tenant.plan_price_eur)
    invoice = PlatformInvoice(
        tenant_id=tenant.id,
        number=await _next_number(db),
        period_start=start,
        period_end=_month_end(start),
        plan=tenant.plan,
        seats=seats,
        unit_price_eur=unit,
        amount_eur=(unit * seats).quantize(Decimal("0.01")),
        issued_on=date.today(),
        due_on=date.today() + timedelta(days=INVOICE_DUE_DAYS),
    )
    db.add(invoice)
    await db.flush()
    return invoice


async def _tenant_admins(db: AsyncSession, tenant_id: uuid.UUID) -> list[User]:
    return list(
        (
            await db.execute(
                select(User).where(
                    User.tenant_id == tenant_id,
                    User.role == "admin",
                    User.is_active.is_(True),
                )
            )
        ).scalars()
    )


async def _email_invoice(db: AsyncSession, tenant: Tenant, invoice: PlatformInvoice) -> None:
    bank = settings.platform_bank_details or "-"
    for admin in await _tenant_admins(db, tenant.id):
        loc = pick_locale(admin.locale, tenant.default_locale)
        await send_email(
            admin.email,
            tr(loc, "platform_invoice_subject", number=invoice.number),
            tr(
                loc, "platform_invoice_body",
                number=invoice.number,
                period=f"{invoice.period_start:%m/%Y}",
                seats=invoice.seats,
                price=f"{invoice.unit_price_eur:.2f}",
                amount=f"{invoice.amount_eur:.2f}",
                due=f"{invoice.due_on:%d.%m.%Y}",
                bank=bank,
                url=f"{settings.public_base_url}/settings",
            ),
        )


async def email_invoice_by_id(invoice_id: uuid.UUID) -> None:
    """Background-task entry point: emails one invoice with its own session."""
    async with SessionLocal() as db:
        invoice = await db.get(PlatformInvoice, invoice_id)
        if invoice is None:
            return
        tenant = await db.get(Tenant, invoice.tenant_id)
        if tenant is not None:
            await _email_invoice(db, tenant, invoice)


async def has_past_due(db: AsyncSession, tenant_id: uuid.UUID) -> bool:
    """True when an open subscription invoice is beyond due date + grace —
    the point where marketplace claiming is paused."""
    cutoff = date.today() - timedelta(days=GRACE_DAYS)
    overdue = (
        await db.execute(
            select(func.count(PlatformInvoice.id)).where(
                PlatformInvoice.tenant_id == tenant_id,
                PlatformInvoice.status == "open",
                PlatformInvoice.due_on < cutoff,
            )
        )
    ).scalar_one()
    return overdue > 0


def invoice_out(invoice: PlatformInvoice) -> dict:
    return {
        "id": str(invoice.id),
        "number": invoice.number,
        "period_start": invoice.period_start.isoformat(),
        "period_end": invoice.period_end.isoformat(),
        "plan": invoice.plan,
        "seats": invoice.seats,
        "unit_price_eur": float(invoice.unit_price_eur),
        "amount_eur": float(invoice.amount_eur),
        "status": invoice.status,
        "issued_on": invoice.issued_on.isoformat(),
        "due_on": invoice.due_on.isoformat(),
        "paid_on": invoice.paid_on.isoformat() if invoice.paid_on else None,
        "payment_reference": invoice.payment_reference,
        "payment_link": invoice.payment_link,
    }


async def _run_billing_cycle(redis: aioredis.Redis) -> None:
    today = date.today()
    async with SessionLocal() as db:
        tenants = (await db.execute(select(Tenant))).scalars().all()

        # 1. Current-month invoices for every billable tenant
        for tenant in tenants:
            invoice = await generate_invoice(db, tenant)
            if invoice is not None:
                await db.commit()
                logger.info(
                    "Platform invoice %s for %s: %s EUR",
                    invoice.number, tenant.name, invoice.amount_eur,
                )
                await _email_invoice(db, tenant, invoice)

        # 2. Dunning: weekly reminder for every overdue open invoice
        overdue = (
            (
                await db.execute(
                    select(PlatformInvoice).where(
                        PlatformInvoice.status == "open",
                        PlatformInvoice.due_on < today,
                    )
                )
            ).scalars().all()
        )
        for invoice in overdue:
            try:
                fresh = await redis.set(
                    f"avokatim:dunning:{invoice.id}", "1", nx=True, ex=7 * 24 * 3600
                )
            except Exception:
                fresh = True
            if not fresh:
                continue
            tenant = await db.get(Tenant, invoice.tenant_id)
            if tenant is None:
                continue
            days_over = (today - invoice.due_on).days
            for admin in await _tenant_admins(db, tenant.id):
                loc = pick_locale(admin.locale, tenant.default_locale)
                await send_email(
                    admin.email,
                    tr(loc, "platform_overdue_subject", number=invoice.number),
                    tr(
                        loc, "platform_overdue_body",
                        number=invoice.number,
                        amount=f"{invoice.amount_eur:.2f}",
                        days=days_over,
                        grace=GRACE_DAYS,
                        url=f"{settings.public_base_url}/settings",
                    ),
                )

        # 3. Trials ending within 7 days: one conversion nudge
        soon = datetime.now(UTC) + timedelta(days=7)
        ending = [
            t for t in tenants
            if t.plan == "trial" and t.status == "active"
            and t.trial_ends_at is not None
            and datetime.now(UTC) < t.trial_ends_at <= soon
        ]
        for tenant in ending:
            try:
                fresh = await redis.set(
                    f"avokatim:trialend:{tenant.id}:{tenant.trial_ends_at:%Y%m%d}",
                    "1", nx=True, ex=14 * 24 * 3600,
                )
            except Exception:
                fresh = True
            if not fresh:
                continue
            days_left = max(0, (tenant.trial_ends_at - datetime.now(UTC)).days)
            for admin in await _tenant_admins(db, tenant.id):
                loc = pick_locale(admin.locale, tenant.default_locale)
                await send_email(
                    admin.email,
                    tr(loc, "trial_ending_subject", days=days_left),
                    tr(
                        loc, "trial_ending_body",
                        days=days_left,
                        price=f"{Decimal(tenant.plan_price_eur):.2f}",
                        url=f"{settings.public_base_url}/settings",
                    ),
                )


async def billing_loop() -> None:
    """Background task started from the app lifespan: generates monthly
    subscription invoices, sends dunning reminders and trial-ending nudges."""
    redis = aioredis.from_url(settings.redis_url)
    logger.info("Platform billing loop started (every %sh)", BILLING_CHECK_HOURS)
    while True:
        try:
            await _run_billing_cycle(redis)
        except Exception as exc:
            logger.warning("Platform billing cycle failed: %s", exc)
        await asyncio.sleep(BILLING_CHECK_HOURS * 3600)
