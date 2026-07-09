"""Local LLM provider via any OpenAI-compatible server (Ollama, vLLM).
Phase 2 option: full privacy — nothing leaves this machine."""
from collections.abc import AsyncIterator

import httpx

from app.config import settings
from app.llm.base import ChatMessage, ChatResult, LLMProvider, StreamChunk, parse_sse_data


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

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> AsyncIterator[StreamChunk]:
        timeout = httpx.Timeout(connect=30, read=300, write=30, pool=30)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{settings.local_llm_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.local_llm_api_key}"},
                json={
                    "model": settings.local_llm_model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens or 4096,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    data = parse_sse_data(line)
                    if not data:
                        continue
                    choices = data.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    if delta.get("reasoning_content"):
                        yield ("thinking", delta["reasoning_content"])
                    if delta.get("content"):
                        yield ("delta", delta["content"])
