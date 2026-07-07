"""Practice dashboard: workload, upcoming deadlines, financial snapshot."""
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import Deadline, IntakeRequest, Invoice, InvoiceItem, Matter, TimeEntry, User

router = APIRouter(prefix="/reports", tags=["reports"])

AGING_BUCKETS = ((0, 30), (31, 60), (61, 90), (91, None))


def _month_starts(now: datetime, count: int) -> list[datetime]:
    """First day of the last `count` months, oldest first (current month last)."""
    first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    months: list[datetime] = [first]
    for _ in range(count - 1):
        prev_last_day = months[0] - timedelta(days=1)
        months.insert(0, prev_last_day.replace(day=1))
    return months


@router.get("/dashboard")
async def dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant = user.tenant_id
    now = datetime.now(UTC)

    matters_by_status = dict(
        (
            await db.execute(
                select(Matter.status, func.count(Matter.id))
                .where(Matter.tenant_id == tenant)
                .group_by(Matter.status)
            )
        ).all()
    )

    deadlines_7d = (
        await db.execute(
            select(func.count(Deadline.id)).where(
                Deadline.tenant_id == tenant,
                Deadline.status == "pending",
                Deadline.due_at <= now + timedelta(days=7),
            )
        )
    ).scalar_one()

    overdue = (
        await db.execute(
            select(func.count(Deadline.id)).where(
                Deadline.tenant_id == tenant,
                Deadline.status == "pending",
                Deadline.due_at < now,
            )
        )
    ).scalar_one()

    new_intakes = (
        await db.execute(
            select(func.count(IntakeRequest.id)).where(
                IntakeRequest.tenant_id == tenant,
                IntakeRequest.status.in_(["new", "conflict"]),
            )
        )
    ).scalar_one()

    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    minutes_this_month = (
        await db.execute(
            select(func.coalesce(func.sum(TimeEntry.minutes), 0)).where(
                TimeEntry.tenant_id == tenant, TimeEntry.started_at >= month_start
            )
        )
    ).scalar_one()

    unpaid_total = (
        await db.execute(
            select(
                func.coalesce(func.sum(InvoiceItem.quantity * InvoiceItem.unit_price), 0)
            )
            .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
            .where(Invoice.tenant_id == tenant, Invoice.status == "sent")
        )
    ).scalar_one()

    # --- Today's agenda: hearings, deadlines and meetings due today ---
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    agenda_rows = (
        await db.execute(
            select(Deadline, Matter.reference, Matter.title)
            .join(Matter, Matter.id == Deadline.matter_id)
            .where(
                Deadline.tenant_id == tenant,
                Deadline.status == "pending",
                Deadline.due_at >= day_start,
                Deadline.due_at < day_end,
            )
            .order_by(Deadline.due_at)
        )
    ).all()
    today_agenda = [
        {
            "id": str(d.id),
            "matter_id": str(d.matter_id),
            "matter_reference": ref,
            "matter_title": title,
            "kind": d.kind,
            "title": d.title,
            "due_at": d.due_at.isoformat(),
            "legal_basis": d.legal_basis,
        }
        for d, ref, title in agenda_rows
    ]

    # --- A/R aging: unpaid (sent) invoices bucketed by age since issue ---
    sent_invoices = (
        await db.execute(
            select(
                func.coalesce(Invoice.issued_on, func.date(Invoice.created_at)),
                func.coalesce(func.sum(InvoiceItem.quantity * InvoiceItem.unit_price), 0),
            )
            .join(InvoiceItem, InvoiceItem.invoice_id == Invoice.id)
            .where(Invoice.tenant_id == tenant, Invoice.status == "sent")
            .group_by(Invoice.id)
        )
    ).all()
    aging = {f"{lo}_{hi if hi else 'plus'}": 0.0 for lo, hi in AGING_BUCKETS}
    today = now.date()
    for issued_on, total in sent_invoices:
        age = (today - issued_on).days if isinstance(issued_on, date) else 0
        for lo, hi in AGING_BUCKETS:
            if age >= lo and (hi is None or age <= hi):
                aging[f"{lo}_{hi if hi else 'plus'}"] += float(total)
                break

    # --- 6-month trend: worked hours and billed revenue per month ---
    months = _month_starts(now, 6)
    horizon = months[0]

    month_lit = literal_column("'month'")
    worked_month = func.date_trunc(month_lit, TimeEntry.started_at)
    minutes_by_month = dict(
        (
            await db.execute(
                select(worked_month, func.sum(TimeEntry.minutes))
                .where(TimeEntry.tenant_id == tenant, TimeEntry.started_at >= horizon)
                .group_by(worked_month)
            )
        ).all()
    )

    billed_on = func.coalesce(Invoice.issued_on, func.date(Invoice.created_at))
    billed_month = func.date_trunc(month_lit, billed_on)
    billed_by_month = dict(
        (
            await db.execute(
                select(billed_month, func.sum(InvoiceItem.quantity * InvoiceItem.unit_price))
                .join(InvoiceItem, InvoiceItem.invoice_id == Invoice.id)
                .where(
                    Invoice.tenant_id == tenant,
                    Invoice.status.in_(["sent", "paid"]),
                    billed_on >= horizon.date(),
                )
                .group_by(billed_month)
            )
        ).all()
    )

    def _month_lookup(data: dict, month: datetime):
        for key, value in data.items():
            if key.year == month.year and key.month == month.month:
                return value
        return 0

    monthly_trend = [
        {
            "month": m.strftime("%Y-%m"),
            "hours": round(int(_month_lookup(minutes_by_month, m)) / 60, 1),
            "billed": float(_month_lookup(billed_by_month, m)),
        }
        for m in months
    ]

    return {
        "matters_by_status": matters_by_status,
        "deadlines_next_7_days": deadlines_7d,
        "deadlines_overdue": overdue,
        "intakes_pending": new_intakes,
        "hours_this_month": round(minutes_this_month / 60, 1),
        "unpaid_invoices_total": float(unpaid_total),
        "today_agenda": today_agenda,
        "ar_aging": aging,
        "monthly_trend": monthly_trend,
    }
