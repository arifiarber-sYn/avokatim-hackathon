"""Unit tests for the deadline engine date math (no DB needed for the core)."""
from datetime import date

from app.services.deadlines import _is_business_day


def test_weekend_detection():
    assert not _is_business_day(date(2026, 7, 4), set())  # Saturday
    assert not _is_business_day(date(2026, 7, 5), set())  # Sunday
    assert _is_business_day(date(2026, 7, 6), set())  # Monday


def test_holiday_detection():
    holidays = {date(2026, 2, 17)}  # Kosovo Independence Day (Tuesday)
    assert not _is_business_day(date(2026, 2, 17), holidays)
    assert _is_business_day(date(2026, 2, 18), holidays)
