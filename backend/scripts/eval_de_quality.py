"""Formal DE quality eval for the local LLM (launch-gate item 3, P-07).

20 German legal questions (14 natural-language + 6 §-citation) answered by
the local provider with REAL RAG context (search_corpus, limit=6,
language="de"), replicating the production prompt assembly from
services/assistant.py (_build_ask_messages, no matter context).

Criteria (ALL must pass, per DE-LLM-REVALIDATION-PLAN.md):
  1. 20/20 non-empty answers (0 tolerated)
  2. >=85% (17/20) answers contain the expected ref+§ (normalized)
  3. 20/20 clean German (no English filler words)
  4. 0 invented statutes (every § cited must exist in the DE corpus)
  5. p95 latency <= 5s
Context sizing (b): prompt_tokens <= 80% of the served num_ctx.

Results table + summary printed; full JSON written to
data/eval_de_quality_<date>.json (git-ignored runtime data).

    cd backend && .venv/bin/python scripts/eval_de_quality.py
"""
import asyncio
import json
import re
import statistics
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.llm.base import ChatMessage  # noqa: E402
from app.llm.local import LocalProvider  # noqa: E402
from app.models import Jurisdiction, LegalCorpusChunk, LegalCorpusDoc  # noqa: E402
from app.services import rag  # noqa: E402
from app.services.assistant import SYSTEM_PROMPT, _source_label  # noqa: E402

LIMIT = 6
# NOTE (2026-08-26, restored to the P-07 plan value): the plan says limit=6;
# it was lowered to 4 on 2026-08-23 because giant chunks pushed prompt_tokens
# over 80% of context (max 15515 > 13107). The DE reindex (2026-08-26)
# eliminated giant chunks — max prompt is now ~1850 tokens — so limit=6 fits
# comfortably and surfaces more of the relevant law (e.g. § 568 for the
# Eigenbedarf question, which limit=4 missed and the model hallucinated as
# § 568c). Re-evaluate if prompts approach 80% again.

# Same question set as eval_de_recherche.py (D-042 baseline).
CASES = [
    ("Wie lange ist die Kündigungsfrist für Mieter einer Wohnung?", "BGB", "§ 573c"),
    ("Kündigung der Wohnung wegen Eigenbedarf des Vermieters", "BGB", "§ 573"),
    ("Wie hoch darf die Mietkaution höchstens sein?", "BGB", "§ 551"),
    ("Mietminderung bei Mängeln der Mietwohnung", "BGB", "§ 536"),
    ("Welche Kündigungsfristen gelten im Arbeitsverhältnis?", "BGB", "§ 622"),
    ("Wann ist eine Kündigung sozial ungerechtfertigt?", "KSchG", "§ 1"),
    ("Frist für die Erhebung der Kündigungsschutzklage", "KSchG", "§ 4"),
    ("Wie viele Tage Mindesturlaub stehen Arbeitnehmern zu?", "BUrlG", "§ 3"),
    ("Wie lang ist die regelmäßige Verjährungsfrist?", "BGB", "§ 195"),
    ("Widerrufsrecht bei außerhalb von Geschäftsräumen geschlossenen Verträgen", "BGB", "§ 312g"),
    ("Schmerzensgeld für immaterielle Schäden", "BGB", "§ 253"),
    ("Wann handelt jemand in Notwehr?", "StGB", "§ 32"),
    ("Frist für die Berufung im Zivilprozess", "ZPO", "§ 517"),
    ("Wer hat Anspruch auf den Pflichtteil beim Erbe?", "BGB", "§ 2303"),
]
CITATION_CASES = [
    ("§ 573c BGB Kündigungsfrist", "BGB", "§ 573c"),
    ("§ 4 KSchG Klagefrist", "KSchG", "§ 4"),
    ("§ 3 BUrlG Urlaubsdauer", "BUrlG", "§ 3"),
    ("§ 2303 BGB Pflichtteilsberechtigte", "BGB", "§ 2303"),
    ("§ 517 ZPO Berufungsfrist", "ZPO", "§ 517"),
    ("§ 32 StGB Notwehr", "StGB", "§ 32"),
]

# English filler words that are NOT valid German words — a hit flags the
# answer as not-clean German. Words that are also valid German words
# (in, an, also, be, Note...) are deliberately NOT in the list to avoid
# false positives; every remaining flag is reviewed manually.
_ENGLISH_FILLERS = {
    "the", "and", "of", "to", "is", "are", "with", "for", "from",
    "that", "this", "you", "your", "please", "important",
    "however", "therefore", "according", "but", "not",
    "as", "at", "or", "if", "would", "shall", "must",
    # NOTE: "will" is deliberately NOT here — it is a valid German word
    # (Verb wollen: "Er will in Wirklichkeit aber angreifen"), causing a
    # false positive seen 2026-08-26 (Notwehr answer).
}
_EN_FILLER_RE = re.compile(r"\b(" + "|".join(sorted(_ENGLISH_FILLERS)) + r")\b", re.IGNORECASE)

# Albanian filler words — NOT valid German (the 'ë' letter alone is a strong
# Albanian marker; German never uses it). Catches answers that drifted into
# Albanian for German questions (seen 2026-08-26: Eigenbedarf answer).
_ALBANIAN_FILLERS = {
    "është", "dhe", "për", "në", "nga", "me", "të", "një", "kjo",
    "kërkesa", "pronari", "marrëdhënia", "bazë", "gjithashtu", "vetëm",
    "por", "nuk", "si", "kur", "mund", "duhet", "shkresë", "ligji",
    "neni", "paragrafi", "banesa", "kontrata", "afati", "përgjigja",
}
_AL_FILLER_RE = re.compile(r"\b(" + "|".join(sorted(_ALBANIAN_FILLERS)) + r")\b", re.IGNORECASE)

_SECTION_RE = re.compile(r"§\s*(\d+[a-z]?)", re.IGNORECASE)


def _norm_sec(s: str | None) -> str:
    return re.sub(r"\s+", "", (s or "")).lower()


def _cites(answer: str, ref: str, section: str) -> bool:
    """Normalized presence check of ref+§ in the model answer."""
    ans = _norm_sec(answer)
    return _norm_sec(section) in ans and ref.lower() in ans


def _english_flags(answer: str) -> list[str]:
    return sorted(set(_EN_FILLER_RE.findall(answer)))


def _albanian_flags(answer: str) -> list[str]:
    """Albanian filler words — a hit flags the answer as not-clean German."""
    return sorted(set(_AL_FILLER_RE.findall(answer)))


def _p95(latencies: list[float]) -> float:
    if not latencies:
        return 0.0
    s = sorted(latencies)
    idx = 0.95 * (len(s) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (idx - lo)


async def _corpus_sections(db, jurisdiction_id) -> set[str]:
    """All § sections present in the DE statute corpus (law docs only),
    normalized — the ground truth for the invented-statute check."""
    rows = (
        await db.execute(
            select(LegalCorpusChunk.section)
            .join(LegalCorpusDoc, LegalCorpusDoc.id == LegalCorpusChunk.doc_id)
            .where(
                LegalCorpusDoc.jurisdiction_id == jurisdiction_id,
                LegalCorpusDoc.doc_type == "law",
                LegalCorpusChunk.section.isnot(None),
            )
        )
    ).scalars().all()
    out: set[str] = set()
    for s in rows:
        norm = _norm_sec(s)
        out.add(norm)
        out.add(norm.lstrip("§"))
    return out


async def _answer(db, provider, jurisdiction_id, question: str) -> dict:
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
    try:
        result = await provider.chat(messages)
    except Exception as exc:  # noqa: BLE001 — eval must not die on one failure
        return {
            "question": question, "error": f"{type(exc).__name__}: {exc}",
            "latency_s": time.monotonic() - t0, "prompt_chars": len(user_content),
            "sources": [(h.get("reference"), h.get("section")) for h in hits],
        }
    usage = result.usage or {}
    prompt_tokens = usage.get("prompt_tokens") or (
        len(user_content) // 4 if usage else None
    )
    return {
        "question": question,
        "answer": result.content,
        "latency_s": time.monotonic() - t0,
        "prompt_tokens": prompt_tokens,
        "prompt_chars": len(user_content),
        "usage": {k: v for k, v in (usage or {}).items() if k in ("prompt_tokens", "completion_tokens", "total_tokens")},
        "sources": [(h.get("reference"), h.get("section")) for h in hits],
    }


async def _run_set(db, provider, jurisdiction_id, cases, sections, label: str) -> list[dict]:
    results = []
    print(f"\n=== {label} ===")
    for i, (question, ref, section) in enumerate(cases, start=1):
        r = await _answer(db, provider, jurisdiction_id, question)
        r.update({"ref": ref, "section": section})
        results.append(r)
        if "error" in r:
            print(f"[{i:>2}] ERR  {question[:50]:<52} {r['error'][:60]}")
            continue
        ans = r["answer"]
        cites = _cites(ans, ref, section)
        flags = _english_flags(ans)
        al_flags = _albanian_flags(ans)
        cited_secs = _SECTION_RE.findall(ans)
        invented = [f"§{s}" for s in cited_secs if f"§{s}" not in sections and s not in sections]
        r["cites_expected"] = cites
        r["english_flags"] = flags
        r["albanian_flags"] = al_flags
        r["invented_statutes"] = invented
        status = "OK " if (cites and not flags and not al_flags and not invented) else "---"
        print(
            f"[{i:>2}] {status} {question[:46]:<48} "
            f"cite={'Y' if cites else 'N'} en={len(flags)} al={len(al_flags)} inv={len(invented)} "
            f"{r['latency_s']:>4.1f}s tok={r.get('prompt_tokens')}"
        )
    return results


async def main() -> None:
    from app.config import settings

    provider = LocalProvider()
    print(f"served model: {settings.local_llm_model}")
    async with SessionLocal() as db:
        de = (
            await db.execute(select(Jurisdiction).where(Jurisdiction.code == "DE"))
        ).scalar_one()
        sections = await _corpus_sections(db, de.id)
        print(f"DE statute sections in corpus: {len(sections)}")
        all_results = []
        for cases, label in ((CASES, "natural-language"), (CITATION_CASES, "§-citations")):
            all_results.extend(await _run_set(db, provider, de.id, cases, sections, label))

    n = len(all_results)
    ok = [r for r in all_results if "error" not in r]
    errs = n - len(ok)
    non_empty = sum(1 for r in ok if r["answer"].strip())
    cites = sum(1 for r in ok if r.get("cites_expected"))
    clean_de = sum(1 for r in ok if not r.get("english_flags") and not r.get("albanian_flags"))
    invented = [r for r in ok if r.get("invented_statutes")]
    latencies = [r["latency_s"] for r in ok]
    p95 = _p95(latencies)
    tok = [r.get("prompt_tokens") for r in ok if r.get("prompt_tokens")]
    max_tok = max(tok) if tok else 0
    # Served context: read the model's effective num_ctx from ollama ps via
    # the running server if possible; fall back to 16384 (observed default).
    served_ctx = 16384
    try:
        import httpx
        info = httpx.get("http://127.0.0.1:11434/api/ps", timeout=5).json()
        for m in info.get("models", []):
            if "qwen3.8:27b" in m.get("name", "") and "agent" not in m.get("name", ""):
                served_ctx = m.get("context_length") or served_ctx
    except Exception:
        pass

    print("\n=== SUMMARY (criteria vs DE-LLM-REVALIDATION-PLAN.md) ===")
    print(f"  answers: {len(ok)}/{n} (errors: {errs})")
    print(f"  1. non-empty:            {non_empty}/20  (need 20/20)")
    print(f"  2. cites ref+§:          {cites}/20  (need >=17/20)")
    print(f"  3. clean German:         {clean_de}/20  (need 20/20)")
    print(f"  4. invented statutes:    {len(invented)}  (need 0)")
    for r in invented:
        print(f"       -> {r['question'][:50]} cites {r['invented_statutes']}")
    print(f"  5. latency p95:          {p95:.1f}s  (need <=5.0s)")
    print(f"  (b) max prompt_tokens:   {max_tok}  (need <={int(served_ctx * 0.8)})  served ctx: {served_ctx}")

    passed = (
        errs == 0 and non_empty == 20 and cites >= 17
        and clean_de == 20 and not invented and p95 <= 5.0
    )
    print(f"\n  VERDICT: {'PASS' if passed else 'FAIL'}")
    out = {
        "date": str(date.today()),
        "model": settings.local_llm_model,
        "served_ctx": served_ctx,
        "criteria": {
            "non_empty": non_empty, "cites_expected": cites,
            "clean_german": clean_de, "invented_statutes": len(invented),
            "latency_p95": round(p95, 2), "max_prompt_tokens": max_tok,
        },
        "verdict": "PASS" if passed else "FAIL",
        "results": [
            {k: (v if k != "answer" else v) for k, v in r.items()}
            for r in all_results
        ],
    }
    dest = Path(__file__).resolve().parents[1] / "data" / f"eval_de_quality_{date.today()}.json"
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nfull results: {dest}")


if __name__ == "__main__":
    asyncio.run(main())
