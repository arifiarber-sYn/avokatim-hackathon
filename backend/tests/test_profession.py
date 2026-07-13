"""The second paying profession (notary offices): signup validation and
the automatic match against the scraped ONK registry."""
import pytest
from pydantic import ValidationError

from app.api import platform as platform_api
from app.api import public_tools
from app.schemas.auth import SignupRequest


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


FAKE_REGISTRY = {
    "notaries": [
        {
            "name": "Vlora Këpuska",
            "email": "vlora.kepuska@noteria-ks.org",
            "city": "Prishtinë",
        },
        {"name": "Argjend Çoçaj", "email": "", "city": "Prizren"},
    ]
}


def test_onk_match_by_email(monkeypatch):
    monkeypatch.setattr(public_tools, "_load_notaries", lambda: FAKE_REGISTRY)
    match = platform_api._onk_match("Emër Tjetër", "VLORA.KEPUSKA@noteria-ks.org")
    assert match is not None
    assert match["matched_by"] == "email"
    assert match["city"] == "Prishtinë"


def test_onk_match_by_normalized_name(monkeypatch):
    monkeypatch.setattr(public_tools, "_load_notaries", lambda: FAKE_REGISTRY)
    # Diacritics and extra spaces must not break the match
    match = platform_api._onk_match("argjend  cocaj", "tjeter@example.com")
    assert match is not None
    assert match["matched_by"] == "name"


def test_onk_match_none(monkeypatch):
    monkeypatch.setattr(public_tools, "_load_notaries", lambda: FAKE_REGISTRY)
    assert platform_api._onk_match("Askush Fare", "askush@example.com") is None
