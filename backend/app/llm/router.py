import logging
from collections.abc import AsyncIterator

from app.config import settings
from app.llm.base import ChatMessage, ChatResult, LLMProvider, StreamChunk
from app.llm.deepseek import DeepSeekProvider
from app.llm.local import LocalProvider
from app.llm.pseudonymize import Pseudonymizer, current_pii_terms, split_safe_emit

logger = logging.getLogger(__name__)

_PROVIDERS: dict[str, LLMProvider] = {
    "deepseek": DeepSeekProvider(),
    "local": LocalProvider(),
}

# Provider name for a PRIVACY-enforced local model (tenant switch
# `allow_external_ai=false`, Law 06/L-082 art. 49 / DSGVO): never rerouted
# to an external provider by task routing and never given an external
# fallback — unlike a plain "local", which is a preference, not a mandate.
LOCAL_PINNED = "local-pinned"


class PseudonymizingProvider(LLMProvider):
    """Wraps an EXTERNAL provider so personal data never leaves the machine
    (D-059 F1). Prompts are stripped to placeholders before the call, the
    answer is restored afterwards — streamed answers buffer any partially
    emitted placeholder across chunks. Local providers are never wrapped."""

    def __init__(self, inner: LLMProvider):
        self._inner = inner
        self.name = inner.name  # callers log/display the real provider name

    def is_configured(self) -> bool:
        return self._inner.is_configured()

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> ChatResult:
        p = Pseudonymizer(current_pii_terms())
        result = await self._inner.chat(
            p.strip_messages(messages), temperature=temperature, max_tokens=max_tokens
        )
        if p.has_replacements:
            result.content = p.restore(result.content)
        return result

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> AsyncIterator[StreamChunk]:
        p = Pseudonymizer(current_pii_terms())
        stream = self._inner.chat_stream(
            p.strip_messages(messages), temperature=temperature, max_tokens=max_tokens
        )
        if not p.has_replacements:
            async for chunk in stream:
                yield chunk
            return
        # One holdback buffer per chunk kind, so a placeholder split across
        # chunks is restored whole — in the answer AND the thinking trace
        buffers: dict[str, str] = {}
        async for kind, text in stream:
            buffers[kind] = buffers.get(kind, "") + text
            emit, buffers[kind] = split_safe_emit(buffers[kind])
            if emit:
                yield (kind, p.restore(emit))
        for kind, rest in buffers.items():
            if rest:
                yield (kind, p.restore(rest))


class FallbackProvider(LLMProvider):
    """Local model first; if the local server errors out (down, OOM,
    timeout) the call transparently retries on the external default —
    pseudonymized — so users never see an outage (D-060). A stream only
    falls back while nothing has been emitted yet; a partially delivered
    answer cannot be restarted without duplicating text."""

    def __init__(self, primary: LLMProvider, secondary: LLMProvider):
        self._primary = primary
        self._secondary = secondary
        self.name = primary.name  # callers log/display the intended provider

    def is_configured(self) -> bool:
        return self._primary.is_configured()

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> ChatResult:
        try:
            return await self._primary.chat(
                messages, temperature=temperature, max_tokens=max_tokens
            )
        except Exception:
            logger.warning(
                "local LLM failed — falling back to %s", self._secondary.name
            )
            return await self._secondary.chat(
                messages, temperature=temperature, max_tokens=max_tokens
            )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> AsyncIterator[StreamChunk]:
        emitted = False
        try:
            async for chunk in self._primary.chat_stream(
                messages, temperature=temperature, max_tokens=max_tokens
            ):
                emitted = True
                yield chunk
            return
        except Exception:
            if emitted:
                raise
            logger.warning(
                "local LLM stream failed — falling back to %s",
                self._secondary.name,
            )
        async for chunk in self._secondary.chat_stream(
            messages, temperature=temperature, max_tokens=max_tokens
        ):
            yield chunk


_WRAPPED: dict[str, PseudonymizingProvider] = {}


def _wrapped(provider: LLMProvider) -> LLMProvider:
    """The pseudonymizing wrapper for external providers (D-059 F1)."""
    if settings.llm_pseudonymize and provider.name != "local":
        if provider.name not in _WRAPPED:
            _WRAPPED[provider.name] = PseudonymizingProvider(provider)
        return _WRAPPED[provider.name]
    return provider


def _external_default() -> LLMProvider | None:
    """The configured external default (settings.llm_provider) — the target
    of task routing and the safety net under the local model."""
    provider = _PROVIDERS.get(settings.llm_provider)
    if provider is None or provider.name == "local" or not provider.is_configured():
        return None
    return provider


def get_provider(name: str | None = None, purpose: str = "chat") -> LLMProvider:
    """Resolve a provider by name, with D-060 routing on top:

    - `purpose="json"` / `"research"`: structured-output and deep-research
      calls need the strongest model — when the resolved provider is the
      local one by preference (country profile / user choice), they are
      routed to the external default instead, pseudonymized.
    - a plain-local resolution otherwise gets the external default as a
      transparent fallback if the local server errors out.
    - `name=LOCAL_PINNED` (tenant privacy switch): plain local, no
      rerouting, no external fallback — data must not leave the machine.
    """
    pinned = name == LOCAL_PINNED
    provider = _PROVIDERS.get("local" if pinned else (name or settings.llm_provider))
    if provider is None:
        raise ValueError(f"Unknown LLM provider: {name}")

    if provider.name == "local" and not pinned:
        external = _external_default()
        if external is not None:
            if settings.llm_task_routing and purpose in ("json", "research"):
                return _wrapped(external)
            if settings.llm_local_fallback and provider.is_configured():
                return FallbackProvider(provider, _wrapped(external))

    if not provider.is_configured():
        raise RuntimeError(
            f"LLM provider '{provider.name}' is not configured "
            "(check backend/.env)"
        )
    return _wrapped(provider)


def list_providers() -> list[dict]:
    return [
        {"name": p.name, "configured": p.is_configured()}
        for p in _PROVIDERS.values()
    ]
