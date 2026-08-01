"""RVG fee math (§ 13 table KostBRÄG 2025, VV items, Anrechnung, VV 7002)."""
from decimal import Decimal

from app.services.rvg import base_fee, compute


def test_base_fee_matches_published_2025_table():
    # Reference values from the published § 13 Abs. 1 RVG table (KostBRÄG 2025)
    expected = {
        "500": "51.50",
        "501": "93.00",  # started step
        "1000": "93.00",
        "2000": "176.00",
        "5000": "354.50",
        "10000": "652.00",
        "25000": "927.00",
        "50000": "1357.00",
        "200000": "2352.00",
        "500000": "3752.00",
        "1000000": "5502.00",
    }
    for value, fee in expected.items():
        assert base_fee(Decimal(value)) == Decimal(fee), value


def test_minimum_fee():
    assert base_fee(Decimal("1")) == Decimal("51.50")  # table base, not minimum
    result = compute(Decimal("10"), ["termingebuehr"])  # 1.2 x 51.50 = 61.80
    assert Decimal(result["lines"][0]["amount"]) >= Decimal("15.00")


def test_geschaeftsgebuehr_1_3_at_5000():
    result = compute(Decimal("5000"), ["geschaeftsgebuehr"])
    line = result["lines"][0]
    assert line["vv"] == "VV 2300"
    assert line["amount"] == "460.85"  # 354.50 x 1.3
    # VV 7002 capped at 20 €
    pauschale = [l for l in result["lines"] if l["vv"] == "VV 7002"]
    assert len(pauschale) == 1 and pauschale[0]["amount"] == "20.00"


def test_anrechnung_when_both_matters_selected():
    result = compute(Decimal("5000"), ["geschaeftsgebuehr", "verfahrensgebuehr"])
    codes = {l["code"]: l for l in result["lines"]}
    # Half of 1.3 = 0.65 credited: 354.50 x 0.65 = 230.425 -> 230.43
    assert codes["anrechnung"]["amount"] == "-230.43"
    # Two Angelegenheiten -> two VV 7002 lines
    assert sum(1 for l in result["lines"] if l["vv"] == "VV 7002") == 2


def test_anrechnung_capped_at_0_75():
    result = compute(
        Decimal("5000"),
        ["geschaeftsgebuehr", "verfahrensgebuehr"],
        geschaeftsgebuehr_rate=Decimal("2.0"),
    )
    codes = {l["code"]: l for l in result["lines"]}
    assert codes["geschaeftsgebuehr"]["amount"] == "709.00"  # 354.50 x 2.0
    assert codes["anrechnung"]["rate"] == "0.75"


def test_small_value_pauschale_below_cap():
    # 500 € value, one hearing fee: 1.2 x 51.50 = 61.80; 20 % = 12.36 < 20
    result = compute(Decimal("500"), ["termingebuehr"])
    pauschale = [l for l in result["lines"] if l["vv"] == "VV 7002"][0]
    assert pauschale["amount"] == "12.36"


def test_totals_and_vat():
    result = compute(Decimal("5000"), ["verfahrensgebuehr", "termingebuehr"])
    # 460.85 + 425.40 + 20.00 = 906.25 net; VAT 19 % = 172.19
    assert result["net"] == "906.25"
    assert result["vat"] == "172.19"
    assert result["total"] == "1078.44"
