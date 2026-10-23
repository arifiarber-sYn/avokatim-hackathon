"""Operator assistant (OpenClaw) event push: silent when unconfigured,
correct payload when configured, never raises into caller flows."""
import pytest

from app.services import ops_notify


@pytest.mark.anyio
async def test_disabled_without_token(monkeypatch):
    monkeypatch.setattr(ops_notify.settings, "openclaw_hook_token", "")
    assert ops_notify.ops_notify_enabled() is False
    assert await ops_notify.notify_ops("test", "hello") is False


@pytest.mark.anyio
async def test_posts_event_with_bearer_token(monkeypatch):
    monkeypatch.setattr(ops_notify.settings, "openclaw_hook_token", "sekret")
    monkeypatch.setattr(
        ops_notify.settings, "openclaw_hook_url", "http://127.0.0.1:1/hooks/agent"
    )
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, json=None, headers=None):
            captured.update(url=url, json=json, headers=headers)
            return FakeResponse()

    monkeypatch.setattr(ops_notify.httpx, "AsyncClient", FakeClient)
    assert await ops_notify.notify_ops("sos", "Urgjencë në Prishtinë", urgent=True)
    assert captured["headers"]["Authorization"] == "Bearer sekret"
    assert "lloji=sos" in captured["json"]["message"]
    assert "urgjente=PO" in captured["json"]["message"]
    assert "Urgjencë në Prishtinë" in captured["json"]["message"]
    assert captured["json"]["name"] == "AvokatIM"


@pytest.mark.anyio
async def test_never_raises_on_network_error(monkeypatch):
    monkeypatch.setattr(ops_notify.settings, "openclaw_hook_token", "sekret")
    monkeypatch.setattr(
        # Nothing listens on this port — must swallow the connection error
        ops_notify.settings, "openclaw_hook_url", "http://127.0.0.1:1/hooks/agent"
    )
    assert await ops_notify.notify_ops("test", "x") is False
