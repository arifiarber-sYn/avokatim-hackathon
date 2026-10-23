"""Meterless adapter: local model execution plus usage accounting.

The point of the hackathon entry is that confidential case documents never
leave the machine. Meterless (Nightshift) gives us a local model hotspot; this
adapter sends the request there and writes one line per call to a usage log so
the UI can show what an answer actually cost.

Cost model: the model runs on this machine, so the marginal price is zero. The
two price knobs (USD per 1M tokens) exist so the same accounting keeps working
when Nightshift is pointed at a paid backend; with the defaults every call
costs $0.000000, which is exactly the claim the demo makes.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.adapters.base import AdapterError
from app.config import settings

logger = logging.getLogger(__name__)


def cost_of(tokens_in: int, tokens_out: int, price_in: float, price_out: float) -> float:
    """USD for one call; prices are USD per 1M tokens."""
    return round((tokens_in / 1_000_000) * price_in + (tokens_out / 1_000_000) * price_out, 6)


@dataclass(slots=True)
class Usage:
    job_id: str
    model: str
    tokens_in: int
    tokens_out: int
    ms: int
    ok: bool
    ts: str
    cost_usd: float = 0.0

    def as_dict(self) -> dict:
        return asdict(self)


class MeterlessAdapter:
    name = "meterless"

    def __init__(
        self,
        base_url: str | None = None,
        usage_log: Path | None = None,
        price_in: float | None = None,
        price_out: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.meterless_base_url).rstrip("/")
        self.usage_log = usage_log or Path(settings.hackathon_usage_log)
        self.price_in = (
            settings.meterless_price_in_per_mtok if price_in is None else price_in
        )
        self.price_out = (
            settings.meterless_price_out_per_mtok if price_out is None else price_out
        )

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
        tokens_in = int(usage.get("prompt_tokens") or 0)
        tokens_out = int(usage.get("completion_tokens") or 0)
        record = Usage(
            job_id=job_id,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            ms=ms,
            ok=ok,
            ts=datetime.now(timezone.utc).isoformat(),
            cost_usd=cost_of(tokens_in, tokens_out, self.price_in, self.price_out),
        )
        self._write(record)
        if not ok:
            raise AdapterError(f"meterless: HTTP {resp.status_code}")
        return text, record

    def _write(self, record: Usage) -> None:
        self.usage_log.parent.mkdir(parents=True, exist_ok=True)
        with self.usage_log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.as_dict(), ensure_ascii=False) + chr(10))


def summarize(usage_log: Path | str, last: int = 20) -> dict[str, Any]:
    """Aggregate usage.jsonl for the UI. Corrupt lines are counted, never fatal."""
    path = Path(usage_log)
    records: list[dict] = []
    corrupt = 0
    if path.exists():
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    records.append(json.loads(raw))
                except json.JSONDecodeError:
                    corrupt += 1
    tokens_in = sum(int(r.get("tokens_in") or 0) for r in records)
    tokens_out = sum(int(r.get("tokens_out") or 0) for r in records)
    ms_total = sum(int(r.get("ms") or 0) for r in records)
    ok_calls = sum(1 for r in records if r.get("ok"))
    by_model: dict[str, int] = {}
    for r in records:
        by_model[str(r.get("model") or "?")] = by_model.get(str(r.get("model") or "?"), 0) + 1
    return {
        "log": str(path),
        "calls": len(records),
        "ok_calls": ok_calls,
        "failed_calls": len(records) - ok_calls,
        "corrupt_lines": corrupt,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tokens_total": tokens_in + tokens_out,
        "cost_usd": round(sum(float(r.get("cost_usd") or 0.0) for r in records), 6),
        "ms_total": ms_total,
        "ms_avg": int(ms_total / len(records)) if records else 0,
        "by_model": by_model,
        "last": records[-max(1, last):],
    }
