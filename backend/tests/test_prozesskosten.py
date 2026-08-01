"""Litigation cost-risk math: § 34 GKG / Anlage 2 table (KostBRÄG 2025),
per-instance RVG + GKG composition, § 91 ZPO loser-pays totals."""
from decimal import Decimal

from app.services.prozesskosten import cost_risk, court_fee_unit


def test_gkg_unit_fee_matches_published_2025_table():
    # Reference values from the published Anlage 2 GKG (KostBRÄG 2025,
    # in force 2025-06-01); 1,000,000 continues per § 34 Abs. 1 (+210/50k).
    expected = {
        "500": "40.00",
        "501": "61.00",  # started step
        "1000": "61.00",
        "2000": "103.00",
        "5000": "170.50",
        "10000": "283.00",
        "25000": "435.50",
        "50000": "638.00",
        "200000": "2038.00",
        "500000": "4138.00",
        "1000000": "6238.00",
    }
    for value, fee in expected.items():
        assert court_fee_unit(Decimal(value)) == Decimal(fee), value


def test_first_instance_at_5000():
    result = cost_risk(Decimal("5000"), ["erste_instanz"])
    inst = result["instances"][0]
    # Court: 3.0 x 170.50 (KV 1210)
    assert inst["court_fee"] == "511.50"
    # Lawyer: VG 1.3 (460.85) + TG 1.2 (425.40) + VV 7002 (20) = 906.25 net,
    # 1078.44 gross — same statutory amounts as the invoice-side RVG calc.
    assert inst["own_lawyer"]["net"] == "906.25"
    assert inst["own_lawyer"]["total"] == "1078.44"
    # Loser pays both lawyers + court: 2 x 1078.44 + 511.50
    assert inst["total_if_lose"] == "2668.38"
    # Plaintiff's filing advance (§ 12 GKG) = the 3.0 first-instance fee
    assert result["court_fee_advance"] == "511.50"


def test_three_instances_cumulative_at_5000():
    result = cost_risk(Decimal("5000"))
    by_code = {i["code"]: i for i in result["instances"]}
    # Berufung: VG 1.6 (567.20) + TG 1.2 (425.40) + 20 = 1012.60 net ->
    # 1204.99 gross; court 4.0 x 170.50 = 682.00
    assert by_code["berufung"]["court_fee"] == "682.00"
    assert by_code["berufung"]["own_lawyer"]["total"] == "1204.99"
    assert by_code["berufung"]["total_if_lose"] == "3091.98"
    # Revision (BGH): VG 2.3 (815.35) + TG 1.5 (531.75) + 20 = 1367.10 net ->
    # 1626.85 gross; court 5.0 x 170.50 = 852.50
    assert by_code["revision"]["own_lawyer"]["total"] == "1626.85"
    assert by_code["revision"]["total_if_lose"] == "4106.20"
    # Worst case through all three instances
    assert result["total_risk"] == "9866.56"
    assert by_code["revision"]["cumulative_if_lose"] == result["total_risk"]


def test_unknown_instance_codes_are_ignored():
    result = cost_risk(Decimal("5000"), ["erste_instanz", "nope"])
    assert [i["code"] for i in result["instances"]] == ["erste_instanz"]
