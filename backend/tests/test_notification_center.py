"""Notification center (D-054): interrupt-budget prefs and route registration."""

from app.api.notifications import router
from app.models import User
from app.models.notifications import NOTIFICATION_KINDS
from app.services.notification_center import _wants_push


def _user(prefs) -> User:
    u = User(email="t@t", full_name="T", password_hash="x")
    u.notification_prefs = prefs
    return u


def test_default_is_push():
    assert _wants_push(_user({}), "deadline")
    assert _wants_push(_user(None), "invoice")


def test_center_only_pref_blocks_push():
    u = _user({"invoice": "center", "message": "push"})
    assert not _wants_push(u, "invoice")
    assert _wants_push(u, "message")
    assert _wants_push(u, "deadline")  # untouched kind falls back to push


def test_routes_registered():
    paths = {r.path for r in router.routes}
    assert "/notifications" in paths
    assert "/notifications/unread-count" in paths
    assert "/notifications/stream" in paths
    assert "/notifications/prefs" in paths
    assert "/notifications/read-all" in paths


def test_kinds_catalog_stable():
    # Settings UI iterates this — keep the well-known kinds present
    for kind in ("deadline", "suggestion", "email", "booking", "message", "intake"):
        assert kind in NOTIFICATION_KINDS
