"""Region (Bundesland) dimension — D-035: Länder registry, city prefill,
Land holidays and the region plumbing on public Ava."""
from datetime import date

from app.jurisdictions import is_valid_region, profile_for, region_for_city
from app.seeds.germany import _buss_und_bettag, de_holidays


def test_de_profile_has_all_16_laender():
    regions = profile_for("DE").regions
    assert len(regions) == 16
    assert regions["NW"] == "Nordrhein-Westfalen"
    assert regions["BY"] == "Bayern"


def test_is_valid_region():
    assert is_valid_region("DE", "NW")
    assert is_valid_region("DE", "by")  # case-insensitive
    assert not is_valid_region("DE", "XX")
    assert not is_valid_region("XK", "NW")  # XK has no regions
    assert not is_valid_region("DE", None)


def test_region_for_city_prefill():
    assert region_for_city("DE", "Köln") == "NW"
    assert region_for_city("DE", "  münchen ") == "BY"
    assert region_for_city("DE", "Unbekanntes Dorf") is None
    assert region_for_city("XK", "Prishtinë") is None


def test_de_holidays_federal_rows_have_no_region():
    federal = [h for h in de_holidays(2026) if h[2] is None]
    assert len(federal) == 9  # the nine nationwide holidays


def test_de_holidays_land_rows():
    rows = {(d, region) for d, _, region in de_holidays(2027)}
    # Allerheiligen (Nov 1) is a holiday in NW but not in Niedersachsen
    assert (date(2027, 11, 1), "NW") in rows
    assert (date(2027, 11, 1), "NI") not in rows
    # Reformationstag (Oct 31) in the northern/eastern Länder
    assert (date(2027, 10, 31), "SH") in rows
    assert (date(2027, 10, 31), "BY") not in rows


def test_buss_und_bettag_is_wednesday_before_nov_23():
    for year in (2026, 2027, 2028):
        d = _buss_und_bettag(year)
        assert d.weekday() == 2  # Wednesday
        assert date(year, 11, 16) <= d <= date(year, 11, 22)


def test_ava_ask_accepts_region():
    from app.api.marketplace import AvaAskIn

    body = AvaAskIn(question="Wie hoch darf die Hecke sein?", region="NW")
    assert body.region == "NW"
