"""Social login (Google/Apple/Meta) unit tests: provider gating, state
tokens, redirect safety and the Apple client-secret JWT."""
import jwt as pyjwt
import pytest
from fastapi import HTTPException

from app.api.oauth_citizen import (
    _apple_client_secret,
    _finish,
    _make_state,
    _read_state,
    _redirect_uri,
    _safe_next,
    enabled_providers,
)
from app.config import settings

_ALL_OAUTH_SETTINGS = [
    "oauth_google_client_id",
    "oauth_google_client_secret",
    "oauth_apple_client_id",
    "oauth_apple_team_id",
    "oauth_apple_key_id",
    "oauth_apple_private_key",
    "oauth_meta_client_id",
    "oauth_meta_client_secret",
]


@pytest.fixture
def no_oauth(monkeypatch):
    """Real credentials live in backend/.env now; gating tests need a
    clean slate independent of the developer's environment."""
    for name in _ALL_OAUTH_SETTINGS:
        monkeypatch.setattr(settings, name, "")


def test_no_providers_without_credentials(no_oauth):
    """Fresh install: no OAuth credentials -> no buttons, endpoints 404."""
    assert enabled_providers() == []


def test_google_enabled_when_configured(no_oauth, monkeypatch):
    monkeypatch.setattr(settings, "oauth_google_client_id", "cid")
    monkeypatch.setattr(settings, "oauth_google_client_secret", "sec")
    assert enabled_providers() == ["google"]


def test_apple_requires_all_four_settings(no_oauth, monkeypatch):
    monkeypatch.setattr(settings, "oauth_apple_client_id", "ai.avokatiim.signin")
    monkeypatch.setattr(settings, "oauth_apple_team_id", "TEAM123")
    monkeypatch.setattr(settings, "oauth_apple_key_id", "KEY123")
    assert "apple" not in enabled_providers()  # private key still missing
    monkeypatch.setattr(settings, "oauth_apple_private_key", "-----BEGIN...")
    assert "apple" in enabled_providers()


def test_safe_next_blocks_open_redirects():
    assert _safe_next("/posto-rastin") == "/posto-rastin"
    assert _safe_next("//evil.com") == "/kycu"
    assert _safe_next("https://evil.com") == "/kycu"
    assert _safe_next(None) == "/kycu"
    assert _safe_next("") == "/kycu"


def test_state_roundtrip_keeps_locale_and_next():
    state = _make_state("sr", "/posto-rastin")
    payload = _read_state(state)
    assert payload["locale"] == "sr"
    assert payload["next"] == "/posto-rastin"


def test_state_rejects_foreign_and_wrong_purpose_tokens():
    with pytest.raises(HTTPException):
        _read_state("garbage")
    # A valid app JWT with a different purpose must not pass as OAuth state
    other = pyjwt.encode(
        {"purpose": "citizen_verify"}, settings.secret_key, algorithm="HS256"
    )
    with pytest.raises(HTTPException):
        _read_state(other)


def test_redirect_uri_matches_documented_pattern():
    assert (
        _redirect_uri("google")
        == f"{settings.public_base_url}/api/public/oauth/google/callback"
    )


def test_finish_puts_token_in_fragment_not_query():
    """Fragments never reach server logs — the token must live there."""
    resp = _finish("/kycu", "citizen_token=abc")
    assert resp.status_code == 303  # turns Apple's form POST into a GET
    location = resp.headers["location"]
    assert location.endswith("/kycu#citizen_token=abc")
    assert "?" not in location.split("#")[0].replace("://", "")


def test_apple_client_secret_is_es256_with_team_claims(monkeypatch):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    monkeypatch.setattr(settings, "oauth_apple_client_id", "ai.avokatiim.signin")
    monkeypatch.setattr(settings, "oauth_apple_team_id", "TEAM123")
    monkeypatch.setattr(settings, "oauth_apple_key_id", "KEY123")
    monkeypatch.setattr(settings, "oauth_apple_private_key", pem)

    token = _apple_client_secret()
    header = pyjwt.get_unverified_header(token)
    assert header["alg"] == "ES256"
    assert header["kid"] == "KEY123"
    claims = pyjwt.decode(
        token, key.public_key(), algorithms=["ES256"],
        audience="https://appleid.apple.com",
    )
    assert claims["iss"] == "TEAM123"
    assert claims["sub"] == "ai.avokatiim.signin"
