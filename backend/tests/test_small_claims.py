"""Small-claims wizard data (LPK arts. 484-491): template integrity, the
municipality -> Basic Court map, and the deterministic render. The public
/small-claims endpoints only validate + compute over this data."""
from decimal import Decimal

from jinja2 import Template

from app.seeds.citizen_docs import XK_SMALL_CLAIM_TEMPLATE
from app.seeds.kosovo import XK_BASIC_COURTS, XK_SMALL_CLAIM_LIMIT_EUR
from app.services.xk_cost_risk import court_fee_first_instance

ALL_LOCALES = ["sq", "sr", "tr", "bs", "en", "zh"]
BASIC_COURT_SEATS = {
    "Prishtinë", "Gjilan", "Prizren", "Gjakovë", "Pejë", "Ferizaj", "Mitrovicë",
}


def test_limit_is_lpk_485():
    assert XK_SMALL_CLAIM_LIMIT_EUR == 500


def test_template_fields_localized():
    assert XK_SMALL_CLAIM_TEMPLATE["code"] == "padia_vlere_vogel"
    for locale in ALL_LOCALES:
        assert XK_SMALL_CLAIM_TEMPLATE["name"][locale]
    keys = [f["key"] for f in XK_SMALL_CLAIM_TEMPLATE["fields"]]
    assert keys == [
        "sender_name", "sender_address", "sender_phone",
        "defendant_name", "defendant_address",
        "claim_amount", "claim_basis", "evidence",
    ]
    for field in XK_SMALL_CLAIM_TEMPLATE["fields"]:
        for locale in ALL_LOCALES:
            assert field["label"][locale], (field["key"], locale)


def test_every_municipality_maps_to_a_real_court():
    assert len(XK_BASIC_COURTS) >= 35  # all Kosovo municipalities covered
    for city, (seat, branch) in XK_BASIC_COURTS.items():
        assert seat in BASIC_COURT_SEATS, city
        assert branch is None or isinstance(branch, str)
    # the 7 seats map to themselves without a branch
    for seat in BASIC_COURT_SEATS:
        assert XK_BASIC_COURTS[seat] == (seat, None)


def test_small_claim_court_fee_is_first_band():
    # UA 03/2025 civil track: 0-5000 EUR -> 60 EUR, so every small claim
    # (<= 500 EUR) costs exactly 60 EUR.
    assert court_fee_first_instance(Decimal("500")) == Decimal("60.00")
    assert court_fee_first_instance(Decimal("120.50")) == Decimal("60.00")


def test_body_renders_court_fee_and_claim():
    text = Template(XK_SMALL_CLAIM_TEMPLATE["body_sq"]).render(
        sender_name="Filan Fisteku",
        sender_address="Rr. e Re 1, Vushtrri",
        sender_phone="+383 44 123 456",
        defendant_name="NTSH Shembulli",
        defendant_address="Rr. Industriale 5, Vushtrri",
        claim_amount="450",
        claim_basis="Pagesa e faturës nr. 12 nuk u krye.",
        evidence="Fatura nr. 12; mesazhet e datës 01.09.2026.",
        city="Vushtrri",
        court_name="Mitrovicë",
        court_branch_line="Dega në Vushtrri\n",
        court_fee="60.00",
        date="18.09.2026",
    )
    assert "GJYKATA THEMELORE NË MITROVICË" in text
    assert "Dega në Vushtrri" in text
    assert "450 €" in text
    assert "60.00 €" in text
    assert "nenet 484–491" in text
    assert "Filan Fisteku" in text
