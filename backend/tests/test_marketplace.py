"""Marketplace unit tests: citizen tokens, name masking, i18n coverage."""
import uuid

import jwt as pyjwt
import pytest

from app.api.marketplace import _citizen_token, _masked_name
from app.config import settings
from app.i18n import CATALOG
from app.security import create_purpose_token, decode_purpose_token

ALL_LOCALES = ["sq", "sr", "tr", "bs", "en", "zh"]

MARKETPLACE_KEYS = [
    "citizen_verify_subject",
    "citizen_verify_body",
    "case_claimed_subject",
    "case_claimed_body",
    "case_directed_subject",
    "case_directed_body",
    "case_message_subject",
    "case_message_body",
    "case_portal_ready_subject",
    "case_portal_ready_body",
]


def test_citizen_token_roundtrip():
    citizen_id = uuid.uuid4()
    token = _citizen_token(citizen_id)
    payload = pyjwt.decode(token, settings.secret_key, algorithms=["HS256"])
    assert payload["citizen"] == str(citizen_id)
    assert payload["exp"] > payload["iat"]


def test_citizen_token_is_not_a_lawyer_token():
    """A citizen token must never pass the lawyer-auth payload shape."""
    token = _citizen_token(uuid.uuid4())
    payload = pyjwt.decode(token, settings.secret_key, algorithms=["HS256"])
    assert "sub" not in payload and "tenant" not in payload


def test_citizen_verify_purpose_token():
    citizen_id = uuid.uuid4()
    token = create_purpose_token("citizen_verify", citizen_id, minutes=60)
    payload = decode_purpose_token(token, "citizen_verify")
    assert payload["sub"] == str(citizen_id)
    with pytest.raises(ValueError):
        decode_purpose_token(token, "verify_email")


def test_masked_name_hides_surname():
    assert _masked_name("Filan Fisteku") == "Filan F."
    assert _masked_name("Ana Maria Krasniqi") == "Ana K."
    assert _masked_name("Mono") == "Mono"
    assert _masked_name("") == "?"


def test_marketplace_i18n_keys_in_all_languages():
    for code in ALL_LOCALES:
        for key in MARKETPLACE_KEYS:
            assert key in CATALOG[code], f"{code} missing {key}"
    # Placeholder substitution works
    from app.i18n import tr

    body = tr("sq", "case_claimed_body", firm="Zyra Test", url="https://x")
    assert "Zyra Test" in body and "https://x" in body
