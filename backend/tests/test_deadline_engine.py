"""Unit tests for the deadline engine date math (no DB needed for the core)."""
from datetime import date, timedelta

from app.services.deadlines import _is_business_day, add_months


def test_weekend_detection():
    assert not _is_business_day(date(2026, 7, 4), set())  # Saturday
    assert not _is_business_day(date(2026, 7, 5), set())  # Sunday
    assert _is_business_day(date(2026, 7, 6), set())  # Monday


def test_holiday_detection():
    holidays = {date(2026, 2, 17)}  # Kosovo Independence Day (Tuesday)
    assert not _is_business_day(date(2026, 2, 17), holidays)
    assert _is_business_day(date(2026, 2, 18), holidays)


def test_add_months_same_day_number():
    # § 188 Abs. 2 BGB: served March 15 + 1 month -> April 15
    assert add_months(date(2026, 3, 15), 1) == date(2026, 4, 15)
    assert add_months(date(2026, 3, 15), 2) == date(2026, 5, 15)


def test_add_months_missing_day_falls_to_month_end():
    # § 188 Abs. 3 BGB: Jan 31 + 1 month -> Feb 28 (2026 is not a leap year)
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)  # leap year
    assert add_months(date(2026, 3, 31), 1) == date(2026, 4, 30)


def test_add_months_year_rollover():
    assert add_months(date(2026, 12, 10), 1) == date(2027, 1, 10)
    assert add_months(date(2026, 11, 30), 3) == date(2027, 2, 28)


def test_add_months_is_not_30_day_approximation():
    # The old approximation gave Feb 1 + 30 days = Mar 3; exact math says Mar 1
    assert add_months(date(2026, 2, 1), 1) == date(2026, 3, 1)
    assert add_months(date(2026, 2, 1), 1) != date(2026, 2, 1) + timedelta(days=30)
