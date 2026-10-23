"""Generic deadline engine. Rules are data (per jurisdiction); this module
only does date math."""
import calendar
from datetime import date, datetime, time, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeadlineRule, Holiday


async def _holiday_set(
    db: AsyncSession, jurisdiction_id, region: str | None = None
) -> set[date]:
    """Nation-wide holidays, plus the region's own when one is given (DE:
    court deadlines depend on the Bundesland's holidays, § 222 ZPO)."""
    stmt = select(Holiday.day).where(
        Holiday.jurisdiction_id == jurisdiction_id,
        Holiday.region.is_(None)
        if region is None
        else or_(Holiday.region.is_(None), Holiday.region == region),
    )
    rows = await db.execute(stmt)
    return {r[0] for r in rows}


def _is_business_day(d: date, holidays: set[date]) -> bool:
    return d.weekday() < 5 and d not in holidays


def add_months(d: date, months: int) -> date:
    """Calendar-month deadline end per § 188 (2)-(3) BGB (same rule in
    Kosovo's LPK art. 124): the period ends on the day of the target month
    bearing the same number as the trigger day; when that month is shorter,
    on its last day (Jan 31 + 1 month -> Feb 28/29)."""
    month_index = d.month - 1 + months
    year, month = d.year + month_index // 12, month_index % 12 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


async def compute_due_date(
    db: AsyncSession, rule: DeadlineRule, trigger_date: date,
    region: str | None = None,
) -> date:
    holidays = await _holiday_set(db, rule.jurisdiction_id, region)

    if rule.day_type == "months":
        # `days` holds the month count for month-based statutory periods
        # (ZPO/VwGO/AO "ein Monat"); exact math, not a 30-day approximation.
        d = add_months(trigger_date, rule.days)
    elif rule.day_type == "business":
        d = trigger_date
        remaining = rule.days
        while remaining > 0:
            d += timedelta(days=1)
            if _is_business_day(d, holidays):
                remaining -= 1
    else:
        d = trigger_date + timedelta(days=rule.days)

    if rule.extend_to_business_day:
        while not _is_business_day(d, holidays):
            d += timedelta(days=1)
    return d


def due_datetime(d: date) -> datetime:
    """Deadlines are due end-of-business (16:00 local) on the computed day."""
    return datetime.combine(d, time(16, 0))
