"""Public API tokens (personal access tokens) — pure-logic unit tests."""
from app.services.api_tokens import (
    DISPLAY_PREFIX_LEN,
    MAX_ACTIVE_TOKENS_PER_USER,
    READ_METHODS,
    SCOPES,
    display_prefix,
    generate_token,
    hash_token,
    is_api_token,
    scope_allows,
)


def test_generate_token_format_and_uniqueness():
    t1, t2 = generate_token(), generate_token()
    assert t1.startswith("avk_") and t2.startswith("avk_")
    assert len(t1) == 4 + 40  # avk_ + 40 hex
    assert t1 != t2
    int(t1[4:], 16)  # hex payload


def test_hash_is_sha256_and_stable():
    t = "avk_" + "ab" * 20
    h = hash_token(t)
    assert len(h) == 64
    assert h == hash_token(t)
    assert h != hash_token(t + "x")


def test_display_prefix_identifies_without_revealing():
    t = generate_token()
    p = display_prefix(t)
    assert t.startswith(p)
    assert len(p) == DISPLAY_PREFIX_LEN
    # far too short to reconstruct the 40-hex secret
    assert len(p) < len(t) // 2


def test_is_api_token_distinguishes_jwt():
    assert is_api_token(generate_token())
    assert not is_api_token("eyJhbGciOiJIUzI1NiJ9.payload.sig")


def test_read_scope_blocks_mutations():
    for method in READ_METHODS:
        assert scope_allows("read", method)
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        assert not scope_allows("read", method)
        assert scope_allows("read_write", method)


def test_scope_check_is_case_insensitive():
    assert scope_allows("read", "get")
    assert not scope_allows("read", "post")


def test_constants_sane():
    assert set(SCOPES) == {"read", "read_write"}
    assert MAX_ACTIVE_TOKENS_PER_USER >= 1


def test_deps_routes_avk_tokens_to_api_path():
    # get_current_user must dispatch avk_ credentials to the API-token
    # resolver before any JWT decoding.
    import inspect

    from app import deps

    src = inspect.getsource(deps.get_current_user)
    assert "is_api_token" in src
    assert src.index("is_api_token") < src.index("decode_token")


def test_api_token_model_stores_only_hash():
    from app.models import ApiToken

    cols = {c.name for c in ApiToken.__table__.columns}
    assert "token_hash" in cols
    assert "token" not in cols  # plaintext is never persisted
    assert {"prefix", "scope", "revoked_at", "last_used_at"} <= cols
