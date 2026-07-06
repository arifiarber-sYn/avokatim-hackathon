"""Local LLM provider via any OpenAI-compatible server (Ollama, vLLM).
Phase 2 option: full privacy — nothing leaves this machine."""
import httpx

from app.config import settings
from app.llm.base import ChatMessage, ChatResult, LLMProvider


class LocalProvider(LLMProvider):
    name = "local"

    def is_configured(self) -> bool:
        return bool(settings.local_llm_model)

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> ChatResult:
        async with httpx.AsyncClient(timeout=600) as client:
            resp = await client.post(
                f"{settings.local_llm_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.local_llm_api_key}"},
                json={
                    "model": settings.local_llm_model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens or 4096,
                },
            )
        resp.raise_for_status()
        data = resp.json()
        return ChatResult(
            content=data["choices"][0]["message"].get("content") or "",
            provider=self.name,
            model=data.get("model", settings.local_llm_model),
            usage=data.get("usage", {}),
        )
