"""Office-level Ava (D-032): the fixed tool registry and payment provider
dispatch — no LLM and no DB required."""
import pytest
from pydantic import ValidationError

from app.config import settings
from app.services.office_ask import OFFICE_TOOLS, _extract_json
from app.services.payments import payments_enabled


def test_registry_has_the_promised_tools():
    expected = {
        "debts_by_client",
        "week_deadlines",
        "stale_matters",
        "hours_by_user",
        "revenue_by_area",
        "ar_aging",
        "upcoming_bookings",
        "intake_stats",
    }
    assert set(OFFICE_TOOLS) == expected
    for spec in OFFICE_TOOLS.values():
        assert callable(spec["run"])
        assert spec["description"]


def test_classifier_json_extraction():
    assert _extract_json('bla {"tool": "ar_aging"} bla') == {"tool": "ar_aging"}
    assert _extract_json("no json here") is None
    assert _extract_json("{broken") is None


def test_payments_provider_dispatch(monkeypatch):
    # Stripe (default): enabled only with a secret key
    monkeypatch.setattr(settings, "payments_provider", "stripe")
    monkeypatch.setattr(settings, "stripe_secret_key", "")
    assert payments_enabled() is False
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_x")
    assert payments_enabled() is True

    # Raiffeisen: needs base URL + api key; a configured Stripe key is ignored
    monkeypatch.setattr(settings, "payments_provider", "raiffeisen")
    monkeypatch.setattr(settings, "raiffeisen_api_base", "")
    monkeypatch.setattr(settings, "raiffeisen_api_key", "")
    assert payments_enabled() is False
    monkeypatch.setattr(settings, "raiffeisen_api_base", "https://gw.example")
    monkeypatch.setattr(settings, "raiffeisen_api_key", "key")
    assert payments_enabled() is True


def test_flat_services_validation():
    from app.api.marketplace import FlatServiceIn, ProfileIn

    ok = FlatServiceIn(title="Përpilim kontrate qiraje", price_eur=50)
    assert ok.price_eur == 50
    with pytest.raises(ValidationError):
        FlatServiceIn(title="ab", price_eur=50)  # title too short
    with pytest.raises(ValidationError):
        FlatServiceIn(title="Kontratë", price_eur=0)  # price must be >= 1
    with pytest.raises(ValidationError):
        ProfileIn(
            flat_services=[
                {"title": f"Shërbimi {i}", "price_eur": 10} for i in range(11)
            ]
        )  # max 10 items
