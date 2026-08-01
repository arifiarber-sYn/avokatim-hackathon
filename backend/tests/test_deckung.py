"""Rechtsschutz cover tracking seeds and constants (D-045)."""

from app.api.matters import INSURANCE_STATUSES
from app.seeds.germany import DE_INSURERS, INSURANCE_FOLLOWUP_DAYS


def test_insurer_codes_are_unique():
    codes = [i["code"] for i in DE_INSURERS]
    assert len(codes) == len(set(codes))


def test_insurers_have_contact_data():
    for insurer in DE_INSURERS:
        assert insurer["name"]
        assert "@" in insurer["email"]
        assert insurer["website"].startswith("https://")


def test_status_vocabulary():
    assert INSURANCE_STATUSES == ("angefragt", "bestaetigt", "abgelehnt")
    assert INSURANCE_FOLLOWUP_DAYS > 0
