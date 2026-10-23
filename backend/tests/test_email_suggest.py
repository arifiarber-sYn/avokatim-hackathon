"""Token-less email classification (D-043 F4): sender parsing + matter pick."""
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from types import SimpleNamespace

from app.services.email_ingest import _best_matter, _sender_address


def _msg(from_header: str | None) -> EmailMessage:
    msg = EmailMessage()
    if from_header is not None:
        msg["From"] = from_header
    return msg


def test_sender_address_parses_and_normalizes():
    assert _sender_address(_msg("Max Mustermann <Max@Example.DE>")) == "max@example.de"
    assert _sender_address(_msg("plain@example.com")) == "plain@example.com"
    assert _sender_address(_msg(None)) == ""


NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def _matter(status: str, days_ago: int):
    return SimpleNamespace(status=status, updated_at=NOW - timedelta(days=days_ago))


def test_best_matter_prefers_open_then_recency():
    closed_recent = _matter("closed", 1)
    open_old = _matter("open", 30)
    open_recent = _matter("open", 2)
    assert _best_matter([closed_recent, open_old, open_recent]) is open_recent
    # Only closed matters: still suggest the most recent one
    closed_old = _matter("closed", 90)
    assert _best_matter([closed_old, closed_recent]) is closed_recent
    assert _best_matter([]) is None
