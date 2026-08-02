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
