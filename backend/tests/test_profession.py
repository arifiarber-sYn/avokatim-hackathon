"""The second paying profession (notary offices): signup validation and
the automatic match against the public chamber registries (OAK/ONK)."""
import pytest
from pydantic import ValidationError

from app.api import public_tools
from app.schemas.auth import SignupRequest
from app.services import license_verify


BASE = {
    "practice_name": "Zyra Test",
    "full_name": "Test Person",
    "email": "test@example.com",
    "password": "x" * 12,
    "accept_tos": True,
}


def test_signup_profession_defaults_to_lawyer():
    req = SignupRequest(**BASE)
    assert req.profession == "lawyer"


def test_signup_profession_accepts_notary():
    req = SignupRequest(**BASE, profession="notary")
    assert req.profession == "notary"


def test_signup_profession_rejects_unknown():
    with pytest.raises(ValidationError):
        SignupRequest(**BASE, profession="judge")


FAKE_ONK = {
    "notaries": [
        {
            "name": "Vlora Këpuska",
            "email": "vlora.kepuska@noteria-ks.org",
            "city": "Prishtinë",
        },
        {"name": "Argjend Çoçaj", "email": "", "city": "Prizren"},
    ]
}

FAKE_OAK = [
    {"name": "Arben Rrahmani", "email": "arbenrrahmani90@gmail.com", "city": "Prishtinë"},
    {"name": "Hysen Rrahmani", "email": "prof-h@hotmail.com", "city": "Ferizaj"},
]


def test_onk_match_by_email(monkeypatch):
    monkeypatch.setattr(public_tools, "_load_notaries", lambda: FAKE_ONK)
    match = license_verify.registry_match(
        "notary", "Emër Tjetër", "VLORA.KEPUSKA@noteria-ks.org"
    )
    assert match is not None
    assert match["matched_by"] == "email"
    assert match["city"] == "Prishtinë"


def test_onk_match_by_normalized_name(monkeypatch):
    monkeypatch.setattr(public_tools, "_load_notaries", lambda: FAKE_ONK)
    # Diacritics and extra spaces must not break the match
    match = license_verify.registry_match("notary", "argjend  cocaj", "tjeter@example.com")
    assert match is not None
    assert match["matched_by"] == "name"


def test_onk_match_none(monkeypatch):
    monkeypatch.setattr(public_tools, "_load_notaries", lambda: FAKE_ONK)
    assert (
        license_verify.registry_match("notary", "Askush Fare", "askush@example.com")
        is None
    )


def test_oak_match_by_email(monkeypatch):
    monkeypatch.setattr(license_verify, "load_oak_registry", lambda: FAKE_OAK)
    match = license_verify.registry_match(
        "lawyer", "Emër Tjetër", "ArbenRrahmani90@gmail.com"
    )
    assert match is not None
    assert match["matched_by"] == "email"
    assert match["name"] == "Arben Rrahmani"


def test_oak_name_only_match_is_flagged_not_email(monkeypatch):
    # A name-only hit must never look like the auto-approvable email match
    monkeypatch.setattr(license_verify, "load_oak_registry", lambda: FAKE_OAK)
    match = license_verify.registry_match(
        "lawyer", "hysen rrahmani", "dikush.tjeter@gmail.com"
    )
    assert match is not None
    assert match["matched_by"] == "name"


def test_oak_match_none(monkeypatch):
    monkeypatch.setattr(license_verify, "load_oak_registry", lambda: FAKE_OAK)
    assert (
        license_verify.registry_match("lawyer", "Askush Fare", "askush@gmail.com")
        is None
    )
