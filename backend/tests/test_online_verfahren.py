"""Online-Verfahren eligibility logic (D-041): pilot-court matching, value
cap, flight-case detection, reduced court fees."""
from decimal import Decimal

from app.services.online_verfahren import (
    check_eligibility,
    looks_like_flight_case,
    match_court,
)


def test_match_court_name_variants():
    assert match_court("Amtsgericht Frankfurt am Main")["state"] == "HE"
    assert match_court("AG Leipzig")["scope"] == "payment"
    assert match_court("Landgericht Berlin") is None
    assert match_court(None) is None


def test_value_cap():
    ok = check_eligibility(value_eur=Decimal("9500"), court_name="AG Bremen")
    assert ok["eligible"] is True
    over = check_eligibility(value_eur=Decimal("12000"), court_name="AG Bremen")
    assert over["eligible"] is False
    assert any(c["code"] == "value_too_high" for c in over["checks"])


def test_flight_only_court_needs_flight_case():
    generic = check_eligibility(
        value_eur=Decimal("400"), court_name="AG Erding", title="Kaufpreisklage"
    )
    assert generic["eligible"] is False
    flight = check_eligibility(
        value_eur=Decimal("400"),
        court_name="AG Erding",
        title="Fluggastrechte: Annullierung LH123",
    )
    assert flight["eligible"] is True
    assert flight["suggested_template"] == "civil.ov_fluggastrechte"


def test_flight_detection_and_default_template():
    assert looks_like_flight_case("Verspäteter Flug nach Rom") is True
    result = check_eligibility(value_eur=Decimal("2000"), title="Mietrückstand")
    assert result["suggested_template"] == "civil.ov_klageschrift"


def test_reduced_ov_fees_at_5000():
    result = check_eligibility(value_eur=Decimal("5000"))
    # service.justiz.de: regular advance 511.50 €, online procedure 341 €
    assert result["fees"]["regular_advance"] == "511.50"
    assert result["fees"]["ov_advance"] == "341.00"
    assert result["fees"]["saving"] == "170.50"


def test_unknown_value_and_court_stay_open():
    result = check_eligibility(value_eur=None)
    assert result["eligible"] is True  # nothing disqualifying yet
    codes = {c["code"] for c in result["checks"]}
    assert "value_unknown" in codes and "court_unknown" in codes
    assert len(result["courts"]) == 18
