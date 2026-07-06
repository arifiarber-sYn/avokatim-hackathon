"""Practice dashboard: workload, upcoming deadlines, financial snapshot."""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import Deadline, IntakeRequest, Invoice, InvoiceItem, Matter, TimeEntry, User

router = APIRouter(prefix="/reports", tags=["reports"])


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

    return {
        "matters_by_status": matters_by_status,
        "deadlines_next_7_days": deadlines_7d,
        "deadlines_overdue": overdue,
        "intakes_pending": new_intakes,
        "hours_this_month": round(minutes_this_month / 60, 1),
        "unpaid_invoices_total": float(unpaid_total),
    }
