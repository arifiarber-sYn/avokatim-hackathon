"""Tests for the Kosovo litigation cost-risk calculator (UA 03/2025 +
Tarifa e OAK, loser-pays per LPK)."""
from decimal import Decimal

from app.seeds.kosovo import XK_COST_RISK_INSTANCES, XK_COURT_FEE_TABLE
from app.services.xk_cost_risk import (
    cost_risk,
    court_fee_first_instance,
    oak_action_fee,
)


class TestCourtFee:
    def test_civil_bands(self):
        assert court_fee_first_instance(Decimal("1000")) == Decimal("60.00")
        assert court_fee_first_instance(Decimal("5000")) == Decimal("60.00")
        assert court_fee_first_instance(Decimal("5001")) == Decimal("150.00")
        assert court_fee_first_instance(Decimal("25000")) == Decimal("150.00")
        assert court_fee_first_instance(Decimal("40000")) == Decimal("200.00")
        assert court_fee_first_instance(Decimal("100000")) == Decimal("300.00")

    def test_civil_above_percentage_and_cap(self):
        # 0.5% of 200,000 = 1,000
        assert court_fee_first_instance(Decimal("200000")) == Decimal("1000.00")
        # capped at 2,500 (0.5% of 1M would be 5,000)
        assert court_fee_first_instance(Decimal("1000000")) == Decimal("2500.00")

    def test_commercial_bands_and_cap(self):
        fee = court_fee_first_instance
        assert fee(Decimal("1000"), "commercial") == Decimal("200.00")
        assert fee(Decimal("50000"), "commercial") == Decimal("300.00")
        assert fee(Decimal("100000"), "commercial") == Decimal("500.00")
        assert fee(Decimal("500000"), "commercial") == Decimal("1000.00")
        # 0.5% of 800k = 4,000; cap is 10,000
        assert fee(Decimal("800000"), "commercial") == Decimal("4000.00")
        assert fee(Decimal("5000000"), "commercial") == Decimal("10000.00")


class TestOakActionFee:
    def test_bands(self):
        assert oak_action_fee(Decimal("2000")) == Decimal("60.00")
        assert oak_action_fee(Decimal("3000")) == Decimal("60.00")
        assert oak_action_fee(Decimal("9000")) == Decimal("80.00")
        assert oak_action_fee(Decimal("50000")) == Decimal("160.00")


class TestCostRisk:
    def test_first_instance_math(self):
        # value 8,000: court 150; lawyer action 80: padi 80 + 2 seanca 160
        # = 240 + paushall 30% (72) = 312 net, VAT 18% = 56.16 → 368.16
        r = cost_risk(Decimal("8000"))
        first = r["instances"][0]
        assert first["court_fee"] == "150.00"
        assert first["own_lawyer"]["net"] == "312.00"
        assert first["own_lawyer"]["total"] == "368.16"
        # lose = 2 × 368.16 + 150 = 886.32
        assert first["total_if_lose"] == "886.32"

    def test_appeal_is_half_court_fee_no_hearings(self):
        r = cost_risk(Decimal("8000"))
        appeal = r["instances"][1]
        assert appeal["code"] == "apeli"
        assert appeal["court_fee"] == "75.00"  # 50% e 150
        # ankesa 80 + paushall 24 = 104 net, +18% = 122.72
        assert appeal["own_lawyer"]["total"] == "122.72"

    def test_cumulative_and_total(self):
        r = cost_risk(Decimal("8000"))
        last = r["instances"][-1]
        assert r["total_risk"] == last["cumulative_if_lose"]
        assert r["court_fee_advance"] == "150.00"
        assert "UA Nr. 03/2025" in r["legal_basis"]
        assert "OAK" in r["legal_basis"]

    def test_commercial_track(self):
        r = cost_risk(Decimal("8000"), track="commercial")
        assert r["track"] == "commercial"
        assert r["instances"][0]["court_fee"] == "200.00"

    def test_unknown_track_falls_back_to_civil(self):
        assert cost_risk(Decimal("8000"), track="penal")["track"] == "civil"

    def test_instance_selection(self):
        r = cost_risk(Decimal("8000"), instance_codes=["shkalla_e_pare"])
        assert len(r["instances"]) == 1


def test_seed_shape():
    assert set(XK_COURT_FEE_TABLE["tracks"]) == {"civil", "commercial"}
    for track in XK_COURT_FEE_TABLE["tracks"].values():
        assert track["bands"] and track["above"]
        for lang in ("sq", "en", "de", "zh", "sr", "tr", "bs"):
            assert track["name"].get(lang)
    codes = [i["code"] for i in XK_COST_RISK_INSTANCES]
    assert codes == ["shkalla_e_pare", "apeli", "revizioni"]
