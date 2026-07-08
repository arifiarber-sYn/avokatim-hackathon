"""Practice dashboard: workload, upcoming deadlines, financial snapshot."""
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.matters import restricted_visibility_filter
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
                restricted_visibility_filter(user),
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


@router.get("/analytics")
async def analytics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Financial practice analytics: utilization, realization, collection,
    intake conversion funnel, and profitability by practice area."""
    tenant = user.tenant_id
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    window_90 = now - timedelta(days=90)
    window_180 = now - timedelta(days=180)

    # --- Utilization: billable hours this month vs the user's monthly target ---
    billable_minutes_mtd = (
        await db.execute(
            select(func.coalesce(func.sum(TimeEntry.minutes), 0)).where(
                TimeEntry.tenant_id == tenant,
                TimeEntry.billable.is_(True),
                TimeEntry.started_at >= month_start,
            )
        )
    ).scalar_one()
    target = user.billable_hours_target_monthly or 120
    billable_hours_mtd = round(int(billable_minutes_mtd) / 60, 1)

    # --- Realization: share of worked billable time that has been invoiced (90d) ---
    worked_minutes, billed_minutes = (
        await db.execute(
            select(
                func.coalesce(func.sum(TimeEntry.minutes), 0),
                func.coalesce(
                    func.sum(TimeEntry.minutes).filter(TimeEntry.invoice_id.is_not(None)), 0
                ),
            ).where(
                TimeEntry.tenant_id == tenant,
                TimeEntry.billable.is_(True),
                TimeEntry.started_at >= window_90,
            )
        )
    ).one()

    # --- Collection: paid vs issued invoice value (180d) ---
    issued_total, paid_total = (
        await db.execute(
            select(
                func.coalesce(func.sum(InvoiceItem.quantity * InvoiceItem.unit_price), 0),
                func.coalesce(
                    func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).filter(
                        Invoice.status == "paid"
                    ),
                    0,
                ),
            )
            .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
            .where(
                Invoice.tenant_id == tenant,
                Invoice.status.in_(["sent", "paid"]),
                func.coalesce(Invoice.issued_on, func.date(Invoice.created_at))
                >= window_180.date(),
            )
        )
    ).one()

    # --- Intake funnel (90d): statuses + conversion per source ---
    intake_rows = (
        await db.execute(
            select(IntakeRequest.source, IntakeRequest.status, func.count(IntakeRequest.id))
            .where(IntakeRequest.tenant_id == tenant, IntakeRequest.created_at >= window_90)
            .group_by(IntakeRequest.source, IntakeRequest.status)
        )
    ).all()
    funnel = {"total": 0, "accepted": 0, "declined": 0, "pending": 0}
    by_source: dict[str, dict] = {}
    for source, status_, count in intake_rows:
        funnel["total"] += count
        if status_ == "accepted":
            funnel["accepted"] += count
        elif status_ == "declined":
            funnel["declined"] += count
        else:
            funnel["pending"] += count
        src = source or "other"
        bucket = by_source.setdefault(src, {"source": src, "total": 0, "accepted": 0})
        bucket["total"] += count
        if status_ == "accepted":
            bucket["accepted"] += count
    decided = funnel["accepted"] + funnel["declined"]
    funnel["conversion_pct"] = round(funnel["accepted"] / decided * 100, 1) if decided else None
    funnel["by_source"] = sorted(by_source.values(), key=lambda b: -b["total"])

    # --- Profitability by practice area (180d) ---
    area_time = (
        await db.execute(
            select(
                Matter.practice_area,
                func.coalesce(func.sum(TimeEntry.minutes), 0),
                func.coalesce(
                    func.sum(
                        TimeEntry.minutes / 60.0 * func.coalesce(TimeEntry.hourly_rate, 0)
                    ),
                    0,
                ),
            )
            .join(Matter, Matter.id == TimeEntry.matter_id)
            .where(TimeEntry.tenant_id == tenant, TimeEntry.started_at >= window_180)
            .group_by(Matter.practice_area)
        )
    ).all()
    area_billed = dict(
        (
            await db.execute(
                select(
                    Matter.practice_area,
                    func.coalesce(func.sum(InvoiceItem.quantity * InvoiceItem.unit_price), 0),
                )
                .join(Invoice, Invoice.matter_id == Matter.id)
                .join(InvoiceItem, InvoiceItem.invoice_id == Invoice.id)
                .where(
                    Invoice.tenant_id == tenant,
                    Invoice.status.in_(["sent", "paid"]),
                    func.coalesce(Invoice.issued_on, func.date(Invoice.created_at))
                    >= window_180.date(),
                )
                .group_by(Matter.practice_area)
            )
        ).all()
    )
    profitability = [
        {
            "practice_area": area,
            "hours": round(int(minutes) / 60, 1),
            "worked_value": round(float(worked_value), 2),
            "billed_value": round(float(area_billed.get(area, 0)), 2),
        }
        for area, minutes, worked_value in area_time
    ]
    profitability.sort(key=lambda p: -p["billed_value"])

    # --- Firm view: per-lawyer workload (MTD hours vs target, matters, 90d worked) ---
    members = (
        await db.execute(
            select(User).where(User.tenant_id == tenant, User.is_active.is_(True))
        )
    ).scalars().all()
    by_lawyer = []
    if len(members) > 1:
        mtd_by_user = dict(
            (
                await db.execute(
                    select(
                        TimeEntry.user_id,
                        func.coalesce(func.sum(TimeEntry.minutes), 0),
                    )
                    .where(
                        TimeEntry.tenant_id == tenant,
                        TimeEntry.billable.is_(True),
                        TimeEntry.started_at >= month_start,
                    )
                    .group_by(TimeEntry.user_id)
                )
            ).all()
        )
        matters_by_user = dict(
            (
                await db.execute(
                    select(Matter.responsible_user_id, func.count(Matter.id))
                    .where(
                        Matter.tenant_id == tenant,
                        Matter.status.in_(["open", "intake", "on_hold"]),
                    )
                    .group_by(Matter.responsible_user_id)
                )
            ).all()
        )
        for m in members:
            m_target = m.billable_hours_target_monthly or 120
            hours_mtd = round(int(mtd_by_user.get(m.id, 0)) / 60, 1)
            by_lawyer.append(
                {
                    "user_id": str(m.id),
                    "full_name": m.full_name,
                    "role": m.role,
                    "open_matters": int(matters_by_user.get(m.id, 0)),
                    "billable_hours_mtd": hours_mtd,
                    "target_monthly": m_target,
                    "utilization_pct": round(hours_mtd / m_target * 100, 1) if m_target else None,
                }
            )
        by_lawyer.sort(key=lambda r: -r["billable_hours_mtd"])

    return {
        "utilization": {
            "billable_hours_mtd": billable_hours_mtd,
            "target_monthly": target,
            "pct": round(billable_hours_mtd / target * 100, 1) if target else None,
        },
        "realization": {
            "worked_hours_90d": round(int(worked_minutes) / 60, 1),
            "billed_hours_90d": round(int(billed_minutes) / 60, 1),
            "pct": round(int(billed_minutes) / int(worked_minutes) * 100, 1)
            if worked_minutes
            else None,
        },
        "collection": {
            "issued_180d": float(issued_total),
            "paid_180d": float(paid_total),
            "pct": round(float(paid_total) / float(issued_total) * 100, 1)
            if issued_total
            else None,
        },
        "intake_funnel": funnel,
        "profitability_by_area": profitability,
        "by_lawyer": by_lawyer,
    }
