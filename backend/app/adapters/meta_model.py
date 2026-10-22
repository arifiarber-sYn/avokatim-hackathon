"""Meta Model API adapter (Muse / SAM) for the Meta Global AI Developer Hackathon.

The endpoint and key come from Meta's onboarding for approved participants, so
nothing is hardcoded here: base_url and api_key are configuration. Until the key
exists the adapter reports available() == False and callers must degrade
gracefully (the demo shows the retrieval layer, not a pretend model call).

Wire format is assumed OpenAI-compatible (chat/completions). If Meta's endpoint
differs, only _payload() changes — the rest of the system keeps seeing text plus
usage numbers.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.adapters.base import AdapterError
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Completion:
    text: str
    model: str
    tokens_in: int
    tokens_out: int
    ms: int


class MetaModelAdapter:
    name = "meta_model"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.meta_model_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.meta_model_api_key
        self.model = model or settings.meta_model_name

    def available(self) -> bool:
        return bool(self.base_url and self.api_key)

    async def complete(self, prompt: str, system: str | None = None) -> Completion:
        if not self.available():
            raise AdapterError("meta_model: base_url/api_key not configured")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model, "messages": messages, "temperature": 0.2}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        import time

        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions", json=payload, headers=headers
            )
        ms = int((time.perf_counter() - started) * 1000)
        if resp.status_code >= 400:
            raise AdapterError(f"meta_model: HTTP {resp.status_code} {resp.text[:120]}")
        data = resp.json()
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage") or {}
        return Completion(
            text=text,
            model=data.get("model") or self.model,
            tokens_in=int(usage.get("prompt_tokens") or 0),
            tokens_out=int(usage.get("completion_tokens") or 0),
            ms=ms,
        )


class StubModel:
    """Deterministic stand-in for tests and offline demos. Never pretends to be live."""

    name = "meta_model_stub"

    def __init__(self, text: str = "Përgjigje provë.") -> None:
        self.text = text

    def available(self) -> bool:
        return True

    async def complete(self, prompt: str, system: str | None = None) -> Completion:
        return Completion(text=self.text, model="stub", tokens_in=len(prompt.split()), tokens_out=len(self.text.split()), ms=0)

