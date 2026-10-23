"""LLM provider abstraction. All providers speak the same interface so the
lawyer can switch between DeepSeek (external) and a local model per request."""
import json
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    role: str  # system | user | assistant
    content: str


@dataclass
class ChatResult:
    content: str
    provider: str
    model: str
    usage: dict = field(default_factory=dict)


# Streaming chunk: ("thinking", text) for reasoning tokens (kept off-record),
# ("delta", text) for answer tokens.
StreamChunk = tuple[str, str]


def parse_sse_data(line: str) -> dict | None:
    """Parse one 'data: {...}' line of an OpenAI-compatible SSE stream."""
    line = line.strip()
    if not line.startswith("data:"):
        return None
    payload = line[5:].strip()
    if not payload or payload == "[DONE]":
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> ChatResult: ...

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream the answer as it is generated. Default: no real streaming —
        one chunk with the full answer (providers override this)."""
        result = await self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        yield ("delta", result.content)

    @abstractmethod
    def is_configured(self) -> bool: ...
