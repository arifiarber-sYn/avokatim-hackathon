"""D-060 LLM routing: task routing (json/research → external default),
transparent fallback under the local model, and the LOCAL_PINNED privacy
name that disables both (tenant switch allow_external_ai=false)."""
import pytest

from app.llm import router
from app.llm.base import ChatMessage, ChatResult, LLMProvider
from app.llm.router import LOCAL_PINNED, FallbackProvider, get_provider


class FakeProvider(LLMProvider):
    def __init__(self, name: str, fail: bool = False):
        self.name = name
        self.fail = fail
        self.calls = 0

    def is_configured(self) -> bool:
        return True

    async def chat(self, messages, *, temperature=0.3, max_tokens=None):
        self.calls += 1
        if self.fail:
            raise RuntimeError("provider down")
        return ChatResult(content=f"ok-{self.name}", provider=self.name, model="m")

    async def chat_stream(self, messages, *, temperature=0.3, max_tokens=None):
        self.calls += 1
        if self.fail:
            raise RuntimeError("provider down")
        yield ("delta", f"ok-{self.name}")


@pytest.fixture
def providers(monkeypatch):
    local = FakeProvider("local")
    external = FakeProvider("deepseek")
    monkeypatch.setattr(router, "_PROVIDERS", {"local": local, "deepseek": external})
    monkeypatch.setattr(router, "_WRAPPED", {})
    monkeypatch.setattr(router.settings, "llm_provider", "deepseek")
    monkeypatch.setattr(router.settings, "llm_task_routing", True)
    monkeypatch.setattr(router.settings, "llm_local_fallback", True)
    # keep assertions simple: the pseudonymizing wrapper is tested elsewhere
    monkeypatch.setattr(router.settings, "llm_pseudonymize", False)
    return local, external


MSG = [ChatMessage(role="user", content="test")]


def test_external_default_unchanged(providers):
    _, external = providers
    assert get_provider(None) is external
    assert get_provider("deepseek", purpose="json") is external


def test_json_purpose_routes_local_to_external(providers):
    _, external = providers
    assert get_provider("local", purpose="json") is external
    assert get_provider("local", purpose="research") is external


def test_task_routing_flag_off_keeps_local(providers, monkeypatch):
    monkeypatch.setattr(router.settings, "llm_task_routing", False)
    p = get_provider("local", purpose="json")
    # no rerouting — but the fallback safety net still applies
    assert isinstance(p, FallbackProvider) and p.name == "local"


def test_chat_purpose_gets_fallback_wrapper(providers):
    p = get_provider("local")
    assert isinstance(p, FallbackProvider)
    assert p.name == "local"


def test_pinned_is_plain_local(providers):
    local, _ = providers
    assert get_provider(LOCAL_PINNED) is local
    # even for json/research work the pinned provider never goes external
    assert get_provider(LOCAL_PINNED, purpose="json") is local
    assert get_provider(LOCAL_PINNED, purpose="research") is local


@pytest.mark.anyio
async def test_fallback_chat_retries_external(providers):
    local, external = providers
    local.fail = True
    result = await get_provider("local").chat(MSG)
    assert result.content == "ok-deepseek"
    assert local.calls == 1 and external.calls == 1


@pytest.mark.anyio
async def test_fallback_not_used_when_local_healthy(providers):
    local, external = providers
    result = await get_provider("local").chat(MSG)
    assert result.content == "ok-local"
    assert external.calls == 0


@pytest.mark.anyio
async def test_stream_falls_back_before_first_chunk(providers):
    local, external = providers
    local.fail = True
    chunks = [c async for c in get_provider("local").chat_stream(MSG)]
    assert chunks == [("delta", "ok-deepseek")]


@pytest.mark.anyio
async def test_stream_does_not_fall_back_mid_answer(providers):
    local, _ = providers

    async def half_stream(messages, *, temperature=0.3, max_tokens=None):
        yield ("delta", "partial")
        raise RuntimeError("died mid-stream")

    local.chat_stream = half_stream
    stream = get_provider("local").chat_stream(MSG)
    assert await stream.__anext__() == ("delta", "partial")
    with pytest.raises(RuntimeError):
        await stream.__anext__()


@pytest.mark.anyio
async def test_pinned_chat_raises_without_fallback(providers):
    local, external = providers
    local.fail = True
    with pytest.raises(RuntimeError):
        await get_provider(LOCAL_PINNED).chat(MSG)
    assert external.calls == 0
