"""Passive time capture (D-032) — pure-logic unit tests."""
from types import SimpleNamespace

import pytest

from app.i18n import CATALOG
from app.services.time_capture import (
    ACTION_MINUTES,
    MAX_SUGGESTED_MINUTES,
    _ACTION_LABEL,
    _matter_for_log,
)

ALL_LOCALES = ["sq", "sr", "tr", "bs", "en", "zh"]


def test_every_scored_action_has_a_label():
    assert set(ACTION_MINUTES) == set(_ACTION_LABEL)
    assert all(m > 0 for m in ACTION_MINUTES.values())


def test_minutes_are_conservative_and_capped():
    # A single action never suggests more than the cap
    assert max(ACTION_MINUTES.values()) <= MAX_SUGGESTED_MINUTES
    # A hyperactive day (30 uploads) is capped, not billed linearly
    total = min(30 * ACTION_MINUTES["document.upload"], MAX_SUGGESTED_MINUTES)
    assert total == MAX_SUGGESTED_MINUTES


@pytest.mark.anyio
async def test_matter_resolution_from_audit_row():
    import uuid

    matter_id = uuid.uuid4()
    log = SimpleNamespace(entity_type="matter", entity_id=str(matter_id))
    assert await _matter_for_log(None, log) == matter_id

    # Garbage entity ids never raise
    bad = SimpleNamespace(entity_type="matter", entity_id="not-a-uuid")
    assert await _matter_for_log(None, bad) is None
    empty = SimpleNamespace(entity_type="matter", entity_id=None)
    assert await _matter_for_log(None, empty) is None

    # Unknown entity types are ignored (no matter to bill against)
    other = SimpleNamespace(entity_type="conversation", entity_id=str(uuid.uuid4()))
    assert await _matter_for_log(None, other) is None


def test_review_request_email_in_all_languages():
    for code in ALL_LOCALES:
        for key in ("case_review_request_subject", "case_review_request_body"):
            assert key in CATALOG[code], f"{code} missing {key}"
        assert "{url}" in CATALOG[code]["case_review_request_body"]
