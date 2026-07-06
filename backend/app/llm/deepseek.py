"""DeepSeek V4 provider (OpenAI-compatible chat completions API).

Mirrors the working TotoTrading integration: deepseek-v4-pro with thinking
mode. When thinking is enabled the API ignores temperature, and reasoning
tokens count toward max_tokens, so the budget must cover chain-of-thought
plus the final answer.
"""
import logging

import httpx

from app.config import settings
from app.llm.base import ChatMessage, ChatResult, LLMProvider

logger = logging.getLogger(__name__)


class DeepSeekProvider(LLMProvider):
    name = "deepseek"

    def is_configured(self) -> bool:
        return bool(settings.deepseek_api_key)

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> ChatResult:
        payload: dict = {
            "model": settings.deepseek_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens or settings.deepseek_max_tokens,
        }
        if settings.deepseek_thinking_enabled:
            payload["thinking"] = {"type": "enabled"}
        else:
            payload["temperature"] = temperature

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
