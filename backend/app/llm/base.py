"""LLM provider abstraction. All providers speak the same interface so the
lawyer can switch between DeepSeek (external) and a local model per request."""
from abc import ABC, abstractmethod
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

    @abstractmethod
    def is_configured(self) -> bool: ...
