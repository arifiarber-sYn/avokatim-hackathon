from collections.abc import AsyncIterator

from app.config import settings
from app.llm.base import ChatMessage, ChatResult, LLMProvider, StreamChunk
from app.llm.deepseek import DeepSeekProvider
from app.llm.local import LocalProvider
from app.llm.pseudonymize import Pseudonymizer, current_pii_terms, split_safe_emit

_PROVIDERS: dict[str, LLMProvider] = {
    "deepseek": DeepSeekProvider(),
    "local": LocalProvider(),
}


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


_WRAPPED: dict[str, PseudonymizingProvider] = {}


def get_provider(name: str | None = None) -> LLMProvider:
    provider = _PROVIDERS.get(name or settings.llm_provider)
    if provider is None:
        raise ValueError(f"Unknown LLM provider: {name}")
    if not provider.is_configured():
        raise RuntimeError(
            f"LLM provider '{provider.name}' is not configured "
            "(check backend/.env)"
        )
    if settings.llm_pseudonymize and provider.name != "local":
        if provider.name not in _WRAPPED:
            _WRAPPED[provider.name] = PseudonymizingProvider(provider)
        return _WRAPPED[provider.name]
    return provider


def list_providers() -> list[dict]:
    return [
        {"name": p.name, "configured": p.is_configured()}
        for p in _PROVIDERS.values()
    ]
