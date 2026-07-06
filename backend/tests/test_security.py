import pytest

from app.security import (
    create_access_token,
    decode_token,
    hash_password,
    new_totp_secret,
    verify_password,
    verify_totp,
)


def test_password_hash_roundtrip():
    h = hash_password("super-secret-password")
    assert verify_password("super-secret-password", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip():
    import uuid

    uid, tid = uuid.uuid4(), uuid.uuid4()
    token = create_access_token(uid, tid)
    payload = decode_token(token)
    assert payload["sub"] == str(uid)
    assert payload["tenant"] == str(tid)
    assert payload["pre_2fa"] is False


def test_pre_2fa_flag():
    import uuid

    token = create_access_token(uuid.uuid4(), uuid.uuid4(), pre_2fa=True)
    assert decode_token(token)["pre_2fa"] is True


def test_totp():
    import pyotp

    secret = new_totp_secret()
    code = pyotp.TOTP(secret).now()
    assert verify_totp(secret, code)
    assert not verify_totp(secret, "000000")
