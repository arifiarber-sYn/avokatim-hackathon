"""Passkeys (D-054 F5): route registration and RP config derivation."""

from app.api.passkeys import _origins, _rp_id, router


def test_routes_registered():
    paths = {r.path for r in router.routes}
    assert "/auth/passkeys/register-options" in paths
    assert "/auth/passkeys/register" in paths
    assert "/auth/passkeys/login-options" in paths
    assert "/auth/passkeys/login" in paths
    assert "/auth/passkeys" in paths


def test_rp_id_derived_from_base_url():
    # Default config: public_base_url hostname (or explicit override)
    assert _rp_id()
    assert "/" not in _rp_id()


def test_origins_include_base_and_dev():
    origins = _origins()
    assert any(o.startswith("http") for o in origins)
    # dev origins from the default extra list
    assert "http://localhost:3000" in origins
