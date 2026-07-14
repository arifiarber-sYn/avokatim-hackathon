"""The outreach campaign script: daily-batch guard and notary letter."""
import importlib.util
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "oak_outreach_campaign.py"

spec = importlib.util.spec_from_file_location("oak_outreach_campaign", SCRIPT)
outreach = importlib.util.module_from_spec(spec)
sys.modules["oak_outreach_campaign"] = outreach
spec.loader.exec_module(outreach)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def test_sent_today_guard_blocks_second_run():
    rows = [{"sent_at": _iso(datetime.now(UTC))}]
    assert outreach.sent_today(rows) is True


def test_sent_today_guard_allows_next_day():
    rows = [
        {"sent_at": _iso(datetime.now(UTC) - timedelta(days=1, hours=2))},
        {"sent_at": "garbage"},  # malformed rows must not crash the guard
        {},
    ]
    assert outreach.sent_today(rows) is False


def test_notary_letter_has_notary_specifics():
    body = outreach.NOTARY_BODY.format(
        name="Test Noteri", region_line=" e qytetit tuaj (Pejë)"
    )
    assert "regjistrohu?profesioni=noter" in body
    assert "06/L-010" in body
    assert "per-noteret" in body
    assert "STOP" in body


def test_lawyer_letter_unchanged_essentials():
    body = outreach.LAWYER_BODY.format(name="Test Avokati", region_line="")
    assert "regjistrohu" in body
    assert "per-avokatet" in body
    assert "STOP" in body


def test_registries_load_and_are_prioritized():
    lawyers = outreach.load_lawyers()
    notaries = outreach.load_notaries()
    assert len(lawyers) > 1000
    assert len(notaries) > 100
    # Prishtinë (highest demand) must come first in both lists
    assert lawyers[0]["region"] == "Prishtinë"
    assert notaries[0]["city"] == "Prishtinë"
