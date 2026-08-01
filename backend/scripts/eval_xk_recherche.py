"""Before/after eval for XK retrieval around the case-law import (D-050, B3).

Two measurements over the XK corpus, mirroring eval_de_recherche.py:

1. LAW_CASES / CITATION_CASES — 12 Albanian questions whose answer lives in
   a specific statute article (verified against the corpus text). A question
   is a *hit* when the expected law + neni appears in the production
   search_corpus top-6. This must NOT regress when judgments join the corpus
   (the max_judgments cap in _rrf_fuse guards the statute slots).

2. JUDGMENT_CASES — case-law-flavored questions. Reported metric: how many
   retrieve at least one judgment chunk in the top-6. Before the import this
   is 0/4 by definition; after it should rise.

    cd backend && .venv/bin/python scripts/eval_xk_recherche.py
"""
import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import Jurisdiction  # noqa: E402
from app.services import rag  # noqa: E402

LIMIT = 6

# (question, expected law reference, expected neni) — sections verified
# against the seeded corpus chunks.
LAW_CASES = [
    ("Sa është afati i ankesës kundër aktgjykimit në kontest civil?", "03/L-006", "Neni 176"),
    ("Brenda sa ditësh paraqitet revizioni kundër aktgjykimit të shkallës së dytë?", "03/L-006", "Neni 211"),
    ("Afati për përgjigje në padi", "03/L-006", "Neni 395"),
    ("Kush i paguan shpenzimet gjyqësore kur e humb procesin?", "03/L-006", "Neni 452"),
    ("Çfarë përfshijnë shpenzimet procedurale?", "03/L-006", "Neni 449"),
    ("Kur mund ta ndërpresë punëdhënësi kontratën e punës?", "03/L-212", "Neni 70"),
    ("Koha e njoftimit për ndërprerjen e kontratës së punës", "03/L-212", "Neni 71"),
    ("Kërkesa e punëtorit te punëdhënësi për mbrojtjen e të drejtave", "03/L-212", "Neni 78"),
    ("Padia e punëtorit në gjykatë kundër vendimit të punëdhënësit", "03/L-212", "Neni 79"),
]

# Lawyer-style queries with explicit citations — the FTS legs should catch.
CITATION_CASES = [
    ("LPK neni 176 ankesa", "03/L-006", "Neni 176"),
    ("neni 452 LPK shpenzimet e procedurës", "03/L-006", "Neni 452"),
    ("Ligji i Punës neni 70 ndërprerja e kontratës", "03/L-212", "Neni 70"),
]

# Case-law-flavored questions: hit = at least one judgment chunk in top-6.
JUDGMENT_CASES = [
    "praktika gjyqësore për zbutjen e dënimit penal",
    "aktgjykim i Gjykatës Supreme për revizion në kontest pronësor",
    "vendim gjyqësor për kompensimin e dëmit nga marrëdhënia e punës",
    "praktika e Gjykatës Supreme për parashkrimin e kërkesës",
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


async def _run_law_set(db, jurisdiction_id, cases, label: str) -> None:
    hits = 0
    print(f"{'question':<62} {'expect':<22} hit")
    for question, ref, section in cases:
        found = await rag.search_corpus(
            db, jurisdiction_id, question, limit=LIMIT, language="sq"
        )
        ok = _is_hit(found, ref, section)
        hits += ok
        print(f"{question[:60]:<62} {ref + ' ' + section:<22} {'HIT' if ok else '-'}")
    n = len(cases)
    print(f"\n{label}: {hits}/{n} ({hits / n:.0%})\n")


async def _run_judgment_set(db, jurisdiction_id) -> None:
    with_judgment = 0
    print(f"{'question':<62} judgments in top-6")
    for question in JUDGMENT_CASES:
        found = await rag.search_corpus(
            db, jurisdiction_id, question, limit=LIMIT, language="sq"
        )
        j = [h for h in found if h.get("doc_type") == "judgment"]
        with_judgment += bool(j)
        sample = f" (p.sh. {j[0].get('reference')})" if j else ""
        print(f"{question[:60]:<62} {len(j)}{sample}")
    n = len(JUDGMENT_CASES)
    print(f"\ncase-law presence: {with_judgment}/{n} questions with ≥1 judgment\n")


async def main() -> None:
    async with SessionLocal() as db:
        xk = (
            await db.execute(select(Jurisdiction).where(Jurisdiction.code == "XK"))
        ).scalar_one()
        await _run_law_set(db, xk.id, LAW_CASES, "natural-language (statutes)")
        await _run_law_set(db, xk.id, CITATION_CASES, "neni-citations")
        await _run_judgment_set(db, xk.id)


if __name__ == "__main__":
    asyncio.run(main())
