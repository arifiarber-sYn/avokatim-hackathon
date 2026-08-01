"""Before/after eval for the DE hybrid retrieval (D-042, F3).

14 typical German legal questions, each with the § the answer lives in.
For every question we run two retrievals over the DE corpus:

    vector  — dense cosine only (the pre-F3 behaviour)
    hybrid  — production search_corpus (cosine + FTS, RRF-fused)

A question is a *hit* when the expected law + § appears in the top-6.
Results are printed as a table; document the numbers in JOURNAL.md.

    cd backend && .venv/bin/python scripts/eval_de_recherche.py
"""
import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import Jurisdiction, LegalCorpusChunk, LegalCorpusDoc  # noqa: E402
from app.services import rag  # noqa: E402

LIMIT = 6

# (question, expected law reference/jurabk, expected §)
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

# Lawyer-style queries with explicit § citations — the vector model is weak
# on these; the FTS legs are what should catch them.
CITATION_CASES = [
    ("§ 573c BGB Kündigungsfrist", "BGB", "§ 573c"),
    ("§ 4 KSchG Klagefrist", "KSchG", "§ 4"),
    ("§ 3 BUrlG Urlaubsdauer", "BUrlG", "§ 3"),
    ("§ 2303 BGB Pflichtteilsberechtigte", "BGB", "§ 2303"),
    ("§ 517 ZPO Berufungsfrist", "ZPO", "§ 517"),
    ("§ 32 StGB Notwehr", "StGB", "§ 32"),
]


def _norm_sec(s: str | None) -> str:
    return re.sub(r"\s+", "", (s or "")).lower()


def _is_hit(hits: list[dict], ref: str, section: str) -> bool:
    want = _norm_sec(section)
    for h in hits:
        if (h.get("reference") or "").lower() != ref.lower():
            continue
        if _norm_sec(h.get("section")) == want:
            return True
    return False


async def _vector_only(db, jurisdiction_id, query: str) -> list[dict]:
    """Replicates the pre-F3 retrieval: cosine over embeddings, no FTS."""
    vectors = rag.embed([query])
    if not vectors:
        return []
    stmt = (
        select(LegalCorpusChunk, LegalCorpusDoc)
        .join(LegalCorpusDoc, LegalCorpusDoc.id == LegalCorpusChunk.doc_id)
        .where(
            LegalCorpusDoc.jurisdiction_id == jurisdiction_id,
            LegalCorpusDoc.language == "de",
            LegalCorpusDoc.region.is_(None),
            LegalCorpusChunk.embedding.isnot(None),
        )
        .order_by(LegalCorpusChunk.embedding.cosine_distance(vectors[0]))
        .limit(LIMIT)
    )
    rows = (await db.execute(stmt)).all()
    return [
        {"section": c.section, "reference": d.reference, "doc_title": d.title}
        for c, d in rows
    ]


async def _run_set(db, jurisdiction_id, cases, label: str) -> None:
    vec_hits = hyb_hits = 0
    print(f"{'question':<58} {'expect':<16} {'vec':<4} hybrid")
    for question, ref, section in cases:
        vec = await _vector_only(db, jurisdiction_id, question)
        hyb = await rag.search_corpus(
            db, jurisdiction_id, question, limit=LIMIT, language="de"
        )
        v = _is_hit(vec, ref, section)
        h = _is_hit(hyb, ref, section)
        vec_hits += v
        hyb_hits += h
        print(f"{question[:56]:<58} {ref + ' ' + section:<16} "
              f"{'HIT' if v else '-':<4} {'HIT' if h else '-'}")
    n = len(cases)
    print(f"\n{label} — vector-only: {vec_hits}/{n} ({vec_hits / n:.0%})   "
          f"hybrid: {hyb_hits}/{n} ({hyb_hits / n:.0%})\n")


async def main() -> None:
    async with SessionLocal() as db:
        de = (
            await db.execute(select(Jurisdiction).where(Jurisdiction.code == "DE"))
        ).scalar_one()
        await _run_set(db, de.id, CASES, "natural-language")
        await _run_set(db, de.id, CITATION_CASES, "§-citations")


if __name__ == "__main__":
    asyncio.run(main())
