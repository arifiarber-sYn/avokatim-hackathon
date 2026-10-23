"""DeepSeek V4 provider (OpenAI-compatible chat completions API).

Mirrors the working TotoTrading integration: deepseek-v4-pro with thinking
mode. When thinking is enabled the API ignores temperature, and reasoning
tokens count toward max_tokens, so the budget must cover chain-of-thought
plus the final answer.
"""
import logging
from collections.abc import AsyncIterator

import httpx

from app.config import settings
from app.llm.base import ChatMessage, ChatResult, LLMProvider, StreamChunk, parse_sse_data

logger = logging.getLogger(__name__)


class DeepSeekProvider(LLMProvider):
    name = "deepseek"

    def is_configured(self) -> bool:
        return bool(settings.deepseek_api_key)

    def _payload(
        self, messages: list[ChatMessage], temperature: float, max_tokens: int | None
    ) -> dict:
        payload: dict = {
            "model": settings.deepseek_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens or settings.deepseek_max_tokens,
        }
        if settings.deepseek_thinking_enabled:
            payload["thinking"] = {"type": "enabled"}
        else:
            payload["temperature"] = temperature
        return payload

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> ChatResult:
        payload = self._payload(messages, temperature, max_tokens)

        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                f"{settings.deepseek_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                json=payload,
            )
        resp.raise_for_status()
        data = resp.json()
        choice = data["choices"][0]["message"]
        return ChatResult(
            content=choice.get("content") or "",
            provider=self.name,
            model=data.get("model", settings.deepseek_model),
            usage=data.get("usage", {}),
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> AsyncIterator[StreamChunk]:
        payload = self._payload(messages, temperature, max_tokens)
        payload["stream"] = True

        # No read timeout between chunks would hang forever on a dead
        # connection; 120s per chunk is generous even for thinking pauses.
        timeout = httpx.Timeout(connect=30, read=120, write=30, pool=30)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{settings.deepseek_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                json=payload,
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
