"""Streaming latency eval for the local LLM (launch-gate item 3, criterion 5).

The formal eval (`eval_de_quality.py`) measures FULL-response latency and
fails only on criterion 5 (p95 <= 5s) while all quality criteria pass. But
the product experience is streaming (assistant UI + public Ava stream
tokens as they arrive), so the user-perceived latency is the time to the
FIRST token, not the full answer. This script measures exactly that, over
the same 20 questions with the same production prompt assembly (real RAG
context, limit=6, language="de"):

  - ttft_s        time to the first visible content token ("delta")
  - ttfs_s        time to the first signal of any kind (incl. "thinking")
  - full_s        time to stream completion (matches the old metric)

Output: table + p50/p95 summary, JSON to data/eval_de_ttft_<date>.json.
Decision input for the owner: if p95 ttft <= 5s, criterion 5 can be
re-framed as a streaming metric and gate item 3 closes without new
hardware; otherwise a dedicated GPU (option b) remains the path.

    cd backend && .venv/bin/python scripts/eval_de_ttft.py
"""
import asyncio
import json
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.llm.base import ChatMessage  # noqa: E402
from app.llm.local import LocalProvider  # noqa: E402
from app.models import Jurisdiction  # noqa: E402
from app.services import rag  # noqa: E402
from app.services.assistant import SYSTEM_PROMPT, _source_label  # noqa: E402

from eval_de_quality import (  # noqa: E402  (same question set)
    CASES,
    CITATION_CASES,
    LIMIT,
    _p95,
)

ALL_CASES = CASES + CITATION_CASES


async def _measure(db, provider, jurisdiction_id, question: str) -> dict:
    hits = await rag.search_corpus(
        db, jurisdiction_id, question, limit=LIMIT, language="de"
    )
    blocks = [f"[{_source_label(h)}]\n{h['text']}" for h in hits]
    user_content = (
        "MATERIALET E LËNDËS DHE BAZA LIGJORE:\n\n"
        + "\n\n---\n\n".join(blocks)
        + f"\n\n=== PYETJA E AVOKATIT ===\n{question}"
    )
    messages = [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_content),
    ]
    t0 = time.monotonic()
    ttfs = ttft = None
    chars = 0
    try:
        async for kind, text in provider.chat_stream(messages):
            now = time.monotonic() - t0
            if ttfs is None:
                ttfs = now
            if kind == "delta":
                if ttft is None:
                    ttft = now
                chars += len(text)
    except Exception as exc:  # noqa: BLE001 — eval must not die on one failure
        return {"question": question, "error": f"{type(exc).__name__}: {exc}",
                "full_s": time.monotonic() - t0}
    return {
        "question": question,
        "ttfs_s": ttfs,
        "ttft_s": ttft,
        "full_s": time.monotonic() - t0,
        "answer_chars": chars,
    }


async def main() -> None:
    provider = LocalProvider()
    if not provider.is_configured():
        print("Local provider not configured (LOCAL_LLM_MODEL empty)")
        return
    async with SessionLocal() as db:
        de = (
            await db.execute(select(Jurisdiction).where(Jurisdiction.code == "DE"))
        ).scalars().first()
        results = []
        print(f"model={settings.local_llm_model}  questions={len(ALL_CASES)}")
        # Warmup: the first request after idle pays model/context load —
        # that is a deploy property (keep-alive), not a per-question latency.
        print("warmup…", flush=True)
        await _measure(db, provider, de.id, "Was regelt § 1 BGB?")
        for i, (question, ref, section) in enumerate(ALL_CASES, start=1):
            r = await _measure(db, provider, de.id, question)
            results.append(r)
            if "error" in r:
                print(f"[{i:>2}/{len(ALL_CASES)}] ERR  {r['error']}  {question[:60]}")
            else:
                print(f"[{i:>2}/{len(ALL_CASES)}] ttft={r['ttft_s']:>5.2f}s "
                      f"full={r['full_s']:>5.1f}s  {question[:60]}", flush=True)

    ok = [r for r in results if "error" not in r and r.get("ttft_s") is not None]
    ttfts = [r["ttft_s"] for r in ok]
    ttfss = [r["ttfs_s"] for r in ok]
    fulls = [r["full_s"] for r in ok]
    summary = {
        "date": str(date.today()),
        "model": settings.local_llm_model,
        "n": len(results), "ok": len(ok),
        "ttft_p50": round(sorted(ttfts)[len(ttfts) // 2], 2) if ttfts else None,
        "ttft_p95": round(_p95(ttfts), 2),
        "ttfs_p95": round(_p95(ttfss), 2),
        "full_p95": round(_p95(fulls), 2),
    }
    print("\n===== STREAMING LATENCY SUMMARY =====")
    print(f"  first content token (TTFT): p50={summary['ttft_p50']}s  "
          f"p95={summary['ttft_p95']}s   (gate criterion: <=5s?)")
    print(f"  first signal (incl. thinking): p95={summary['ttfs_p95']}s")
    print(f"  full response:               p95={summary['full_p95']}s "
          f"(old metric)")
    out = Path(__file__).resolve().parents[1].parent / "data" / (
        f"eval_de_ttft_{date.today()}.json")
    out.write_text(json.dumps({"summary": summary, "results": results},
                              ensure_ascii=False, indent=1))
    print(f"\nJSON: {out}")


if __name__ == "__main__":
    asyncio.run(main())
