"""Slot math for consultation booking (Phase 4)."""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.api.bookings import SLOT_MINUTES, _free_slots


def _profile(slots: list[dict]) -> SimpleNamespace:
    # _free_slots only reads .booking_slots — a stub avoids ORM instrumentation
    return SimpleNamespace(booking_slots=slots)


def test_no_windows_no_slots():
    assert _free_slots(_profile([]), set()) == []


def test_slots_generated_within_window_and_future_only():
    # All-day windows every day guarantee slots regardless of when tests run
    windows = [{"day": d, "start": "00:00", "end": "23:30"} for d in range(7)]
    now = datetime.now(UTC).astimezone()
    slots = _free_slots(_profile(windows), set())
    assert slots, "expected free slots for an all-day schedule"
    assert all(s > now for s in slots)
    assert slots == sorted(slots)
    # 30-minute grid
    assert all(s.minute in (0, 30) and s.second == 0 for s in slots)


def test_taken_slots_are_excluded():
    windows = [{"day": d, "start": "00:00", "end": "23:30"} for d in range(7)]
    all_free = _free_slots(_profile(windows), set())
    first = all_free[0]
    remaining = _free_slots(_profile(windows), {first})
    assert first not in remaining
    assert len(remaining) == len(all_free) - 1


def test_window_end_is_exclusive_for_slot_start():
    # A 60-minute window fits exactly two 30-minute slots
    tomorrow = (datetime.now(UTC).astimezone() + timedelta(days=1)).date()
    windows = [{"day": tomorrow.weekday(), "start": "09:00", "end": "10:00"}]
    slots = [s for s in _free_slots(_profile(windows), set()) if s.date() == tomorrow]
    assert [(s.hour, s.minute) for s in slots] == [(9, 0), (9, 30)]
    assert SLOT_MINUTES == 30
