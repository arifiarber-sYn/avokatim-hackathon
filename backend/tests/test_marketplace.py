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
    "sos_alert_subject",
    "sos_alert_body",
    "verify_approved_subject",
    "verify_approved_body",
    "verify_rejected_subject",
    "verify_rejected_body",
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


def test_ava_quota_keys_separate_anon_and_citizen():
    from types import SimpleNamespace

    from app.api.marketplace import (
        AVA_ANON_DAILY_LIMIT,
        AVA_CITIZEN_DAILY_LIMIT,
        _ava_quota_key,
    )

    citizen = SimpleNamespace(id=uuid.uuid4())
    anon_key, anon_limit = _ava_quota_key(None, "1.2.3.4", "sess1")
    cit_key, cit_limit = _ava_quota_key(citizen, "1.2.3.4", "sess1")
    assert anon_key != cit_key
    assert anon_limit == AVA_ANON_DAILY_LIMIT
    assert cit_limit == AVA_CITIZEN_DAILY_LIMIT
    # citizens keep their quota across devices/IPs
    cit_key2, _ = _ava_quota_key(citizen, "5.6.7.8", None)
    assert cit_key == cit_key2


def test_public_ava_prompt_is_information_not_advice():
    from app.api.marketplace import PUBLIC_AVA_SYSTEM_PROMPT

    assert "INFORMIM" in PUBLIC_AVA_SYSTEM_PROMPT
    assert "JO këshillë" in PUBLIC_AVA_SYSTEM_PROMPT
    assert "Më lidh me avokat" in PUBLIC_AVA_SYSTEM_PROMPT


def test_sos_is_a_valid_urgency():
    from app.models.marketplace import CASE_URGENCIES

    assert "sos" in CASE_URGENCIES


def test_sos_input_requires_meaningful_description():
    from pydantic import ValidationError

    from app.api.marketplace import SosIn

    with pytest.raises(ValidationError):
        SosIn(description="ndihme")
    ok = SosIn(description="Më ndaloi policia në Prishtinë, kam nevojë për avokat")
    assert ok.city is None


@pytest.mark.anyio
async def test_lead_quota_paid_plans_are_unlimited():
    from types import SimpleNamespace

    from app.api.marketplace import TRIAL_MONTHLY_LEAD_LIMIT, _lead_quota

    assert TRIAL_MONTHLY_LEAD_LIMIT > 0
    for plan in ("solo", "firm"):
        quota = await _lead_quota(None, SimpleNamespace(plan=plan))
        assert quota == {"plan": plan, "limit": None, "used": None, "remaining": None}


def test_livekit_token_disabled_without_keys(monkeypatch):
    from app.services import livekit

    monkeypatch.setattr(settings, "livekit_api_key", "")
    monkeypatch.setattr(settings, "livekit_api_secret", "")
    assert livekit.livekit_enabled() is False
    assert livekit.room_token("sos-x", "lawyer-1", "Test") is None


def test_livekit_token_payload_grants_only_one_room(monkeypatch):
    from app.services import livekit

    monkeypatch.setattr(settings, "livekit_api_key", "APItest")
    monkeypatch.setattr(settings, "livekit_api_secret", "secret-test")
    case_id = uuid.uuid4()
    room = livekit.sos_room_name(case_id)
    token = livekit.room_token(room, f"citizen-{case_id}", "Qytetari")
    payload = pyjwt.decode(token, "secret-test", algorithms=["HS256"])
    assert payload["iss"] == "APItest"
    assert payload["video"]["room"] == f"sos-{case_id}"
    assert payload["video"]["roomJoin"] is True
    assert payload["exp"] - payload["iat"] == livekit.TOKEN_TTL_MINUTES * 60


def test_verification_statuses_cover_lifecycle():
    from app.models.marketplace import VERIFICATION_STATUSES

    assert VERIFICATION_STATUSES == ["none", "pending", "verified", "rejected"]


def test_review_ratings_bounded_one_to_five():
    from pydantic import ValidationError

    from app.api.marketplace import ReviewIn

    ok = ReviewIn(rating_communication=5, rating_speed=4, rating_clarity=3)
    assert ok.comment is None
    with pytest.raises(ValidationError):
        ReviewIn(rating_communication=0, rating_speed=4, rating_clarity=3)
    with pytest.raises(ValidationError):
        ReviewIn(rating_communication=5, rating_speed=6, rating_clarity=3)


def test_case_reviewable_only_after_engagement_concluded():
    from types import SimpleNamespace

    from app.api.marketplace import _case_reviewable

    tenant = uuid.uuid4()
    assert _case_reviewable(SimpleNamespace(claimed_by_tenant_id=tenant, status="closed"))
    assert _case_reviewable(SimpleNamespace(claimed_by_tenant_id=tenant, status="converted"))
    assert not _case_reviewable(SimpleNamespace(claimed_by_tenant_id=tenant, status="claimed"))
    assert not _case_reviewable(SimpleNamespace(claimed_by_tenant_id=None, status="closed"))


def test_marketplace_i18n_keys_in_all_languages():
    for code in ALL_LOCALES:
        for key in MARKETPLACE_KEYS:
            assert key in CATALOG[code], f"{code} missing {key}"
    # Placeholder substitution works
    from app.i18n import tr

    body = tr("sq", "case_claimed_body", firm="Zyra Test", url="https://x")
    assert "Zyra Test" in body and "https://x" in body
