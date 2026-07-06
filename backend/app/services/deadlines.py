"""Generic deadline engine. Rules are data (per jurisdiction); this module
only does date math."""
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeadlineRule, Holiday


async def _holiday_set(db: AsyncSession, jurisdiction_id) -> set[date]:
    rows = await db.execute(select(Holiday.day).where(Holiday.jurisdiction_id == jurisdiction_id))
    return {r[0] for r in rows}


def _is_business_day(d: date, holidays: set[date]) -> bool:
    return d.weekday() < 5 and d not in holidays


async def compute_due_date(
    db: AsyncSession, rule: DeadlineRule, trigger_date: date
) -> date:
    holidays = await _holiday_set(db, rule.jurisdiction_id)

    if rule.day_type == "business":
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
