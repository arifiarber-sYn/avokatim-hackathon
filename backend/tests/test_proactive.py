"""Proactive AI (D-054 F3): briefing prompt shape and config defaults."""

from app.config import settings
from app.services.proactive import (
    _CASELAW_MAX_DISTANCE,
    BRIEFING_PROMPT,
)


def test_briefing_prompt_has_placeholders():
    text = BRIEFING_PROMPT.format(locale="de", data="- Test")
    assert "de" in text
    assert "- Test" in text
    assert "{" not in text.replace("{}", "")  # nothing left unformatted


def test_briefing_hour_default():
    assert 0 <= settings.briefing_hour <= 12


def test_caselaw_threshold_sane():
    # Cosine distance: 0 = identical; anything above ~0.6 is noise
    assert 0.2 <= _CASELAW_MAX_DISTANCE <= 0.6


def test_file_quality_audit_exists_and_is_wired():
    """Advancement #7 (audit 2026-09-18): the nightly file-quality audit is
    part of the proactive layer and runs in the reminder loop."""
    import inspect

    from app.services import notifications, proactive

    assert inspect.iscoroutinefunction(proactive.run_file_quality_audit)
    assert inspect.iscoroutinefunction(proactive._file_quality_findings)
    # wired into the nightly monitors block
    src = inspect.getsource(notifications)
    assert "run_file_quality_audit" in src
