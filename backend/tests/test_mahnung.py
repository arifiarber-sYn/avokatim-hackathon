"""Dunning (Mahnwesen, D-043 F4) email texts and level conventions."""
from app.api.billing import MAHNUNG_GRACE_DAYS, MAHNUNG_MAX_LEVEL
from app.i18n import tr

LOCALES = ["sq", "sr", "tr", "bs", "en", "zh", "de"]
ARGS = {
    "number": "F-2026-0001",
    "total": "1190.00",
    "currency": "EUR",
    "due": "01.07.2026",
    "new_due": "15.08.2026",
}


def test_mahnung_texts_format_in_every_locale_and_level():
    for code in LOCALES:
        for level in (1, 2, 3):
            subject = tr(code, f"email_mahnung_subject_{level}", **ARGS)
            body = tr(code, f"email_mahnung_body_{level}", **ARGS)
            assert "F-2026-0001" in subject, (code, level)
            assert "1190.00" in body and "15.08.2026" in body, (code, level)
            # No leftover unformatted placeholders
            assert "{" not in subject and "{" not in body, (code, level)


def test_texts_escalate_per_level():
    """Each level must be worded differently (reminder → firm → final)."""
    for code in LOCALES:
        bodies = {tr(code, f"email_mahnung_body_{lvl}", **ARGS) for lvl in (1, 2, 3)}
        assert len(bodies) == 3, code


def test_german_levels_follow_convention():
    assert tr("de", "email_mahnung_subject_1", **ARGS).startswith("Zahlungserinnerung")
    assert tr("de", "email_mahnung_subject_2", **ARGS).startswith("Mahnung")
    assert tr("de", "email_mahnung_subject_3", **ARGS).startswith("Letzte Mahnung")
    # The final level announces possible legal steps
    assert "rechtliche Schritte" in tr("de", "email_mahnung_body_3", **ARGS)


def test_level_constants():
    assert MAHNUNG_MAX_LEVEL == 3
    assert MAHNUNG_GRACE_DAYS > 0
