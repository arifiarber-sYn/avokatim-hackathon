"""Meterless adapter: local model execution plus usage accounting.

The point of the hackathon entry is that confidential case documents never
leave the machine. Meterless (Nightshift) gives us a local model hotspot; this
adapter sends the request there and writes one line per call to a usage log so
the UI can show what an answer actually cost.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.adapters.base import AdapterError
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Usage:
    job_id: str
    model: str
    tokens_in: int
    tokens_out: int
    ms: int
    ok: bool
    ts: str

    def as_dict(self) -> dict:
        return asdict(self)


class MeterlessAdapter:
    name = "meterless"

    def __init__(self, base_url: str | None = None, usage_log: Path | None = None) -> None:
        self.base_url = (base_url or settings.meterless_base_url).rstrip("/")
        self.usage_log = usage_log or Path(settings.hackathon_usage_log)

    def available(self) -> bool:
        return bool(self.base_url)

    async def chat(self, prompt: str, model: str = "local") -> tuple[str, Usage]:
        if not self.available():
            raise AdapterError("meterless: base_url not configured")
        started = time.perf_counter()
        job_id = f"ml-{int(started * 1000)}"
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json={"model": model, "messages": [{"role": "user", "content": prompt}]},
            )
        ms = int((time.perf_counter() - started) * 1000)
        ok = resp.status_code < 400
        text = ""
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
        if ok:
            data = resp.json()
            text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage") or usage
        record = Usage(
            job_id=job_id,
            model=model,
            tokens_in=int(usage.get("prompt_tokens") or 0),
            tokens_out=int(usage.get("completion_tokens") or 0),
            ms=ms,
            ok=ok,
            ts=datetime.now(timezone.utc).isoformat(),
        )
        self._write(record)
        if not ok:
            raise AdapterError(f"meterless: HTTP {resp.status_code}")
        return text, record

    def _write(self, record: Usage) -> None:
        self.usage_log.parent.mkdir(parents=True, exist_ok=True)
        with self.usage_log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.as_dict(), ensure_ascii=False) + chr(10))
