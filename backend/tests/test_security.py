import pytest

from app.security import (
    create_access_token,
    create_purpose_token,
    decode_purpose_token,
    decode_token,
    hash_password,
    new_totp_secret,
    password_fingerprint,
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


def test_purpose_token_roundtrip():
    import uuid

    uid = uuid.uuid4()
    token = create_purpose_token("reset_password", uid, minutes=30, fingerprint="abcd")
    payload = decode_purpose_token(token, "reset_password")
    assert payload["sub"] == str(uid)
    assert payload["fp"] == "abcd"


def test_purpose_token_wrong_purpose_rejected():
    import uuid

    token = create_purpose_token("verify_email", uuid.uuid4(), minutes=30)
    with pytest.raises(ValueError):
        decode_purpose_token(token, "reset_password")


def test_purpose_token_expired_rejected():
    import uuid

    import jwt

    token = create_purpose_token("invite", uuid.uuid4(), minutes=-1)
    with pytest.raises(jwt.PyJWTError):
        decode_purpose_token(token, "invite")


def test_password_fingerprint_changes_with_hash():
    h1 = hash_password("password-one-long")
    h2 = hash_password("password-two-long")
    assert password_fingerprint(h1) != password_fingerprint(h2)


def test_totp_secret_encrypted_at_rest():
    from app.config import settings
    from app.security import (
        _totp_fernet,
        new_totp_secret,
        protect_totp_secret,
        reveal_totp_secret,
        verify_totp,
    )

    if not settings.doc_encryption_key:
        # test env without a key: passthrough mode
        s = new_totp_secret()
        assert protect_totp_secret(s) == s
        return
    _totp_fernet.cache_clear()
    secret = new_totp_secret()
    stored = protect_totp_secret(secret)
    assert stored.startswith("enc:v1:") and secret not in stored
    assert reveal_totp_secret(stored) == secret
    # legacy plaintext rows keep working
    assert reveal_totp_secret(secret) == secret
    import pyotp

    assert verify_totp(reveal_totp_secret(stored), pyotp.TOTP(secret).now())
