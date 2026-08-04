"""Citation verification for Ava's answers (D-059 F6).

LLM answers cite laws (\"§ 573 BGB\", \"neni 176 i LPK\") and case law
(\"BGH, VIII ZR 285/18\"). This module extracts those citations with regex
and checks them against the indexed legal corpus, so the lawyer sees per
citation whether it exists in our sources (\"verified\") or must be checked
by hand (\"unverifiable\"). It runs AFTER the answer is complete — never in
the critical path of the stream.

Verification levels:
  - statute:  the law code/name must match a corpus doc (reference/title);
    when a section is cited we also require a chunk of that doc to mention
    the section (chunk.section or full text).
  - case:     the Aktenzeichen / case number must appear in a corpus doc's
    reference or title (German decisions are indexed that way).

A citation that only fails the section check still names the law, so it is
reported as level \"law\" (the law exists, the exact section wasn't found).
"""

from __future__ import annotations

import logging
import re
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LegalCorpusChunk, LegalCorpusDoc

logger = logging.getLogger(__name__)

# How many citations we verify per answer — keeps the post-answer DB work
# bounded even for very long research syntheses.
MAX_CITATIONS = 25

# --- German statutes: "§ 573 BGB", "§§ 573, 574 BGB", "§ 573 Abs. 2 BGB",
# "Art. 12 GG". The code is 2–15 letters, optionally with roman/arabic
# suffix (SGB V, StVO...).
_DE_STATUTE_RE = re.compile(
    r"(?:§§?\s*(?P<de_sec>\d+[a-z]?(?:\s*(?:Abs\.|Absatz)\s*\d+)?(?:\s*(?:S\.|Satz)\s*\d+)?)"
    r"|Art(?:ikel|\.)\s*(?P<de_art>\d+[a-z]?))"
    r"[^\S\n]+(?P<de_code>(?:[A-ZÄÖÜ][A-Za-zÄÖÜäöüß]{1,14})(?:\s+(?:[IVX]+|\d+))?)"
)

# --- German case numbers (Aktenzeichen): "VIII ZR 285/18", "2 BvR 1444/00",
# "6 AZR 190/22" — optionally preceded by the court.
_DE_CASE_RE = re.compile(
    r"(?P<de_case>(?:[IVX]{1,5}|\d{1,2})\s+[A-Za-z]{1,5}[A-Za-z ()]{0,10}?\s+\d{1,5}/\d{2})"
)

# --- Albanian statutes: "neni 176 i LPK", "neni 176 LPK", "sipas nenit 322
# të LMD", "Ligji Nr. 03/L-006". Law names may be abbreviations (LPK, LMD,
# KPRK) or "Ligji Nr. ...".
_XK_ARTICLE_RE = re.compile(
    r"nen(?:i|it|in)\s+(?P<xk_sec>\d+[a-z]?)"
    r"(?:\s*(?:par\.|paragrafi)\s*\d+)?"
    r"(?:\s+(?:i|të|te|i\s+Ligjit|të\s+Ligjit))?\s+"
    r"(?P<xk_code>(?:[A-Z]{2,6}\b|Ligj\w*\s+[Nn]r\.?\s*[\d/L\-]+|Kod\w*\s+[A-Za-zë ]{3,40}))",
    re.IGNORECASE,
)
_XK_LAW_RE = re.compile(r"(?P<xk_law>Ligji\s+[Nn]r\.?\s*\d{2}/L-\d{1,4})")

# Words the statute regex may capture that are never law codes
_CODE_STOPWORDS = {
    "Abs", "Satz", "Nr", "Nummer", "Alt", "Var", "Halbs", "Rn", "Ziff",
    "UND", "ODER", "DER", "DES", "DIE",
}


def extract_citations(text: str) -> list[dict]:
    """All legal citations in an answer, deduplicated, in order of first
    appearance. Each: {kind: statute|case|law, cite, code?, section?}."""
    found: list[dict] = []
    seen: set[str] = set()

    def _add(item: dict) -> None:
        key = item["cite"].lower()
        if key not in seen:
            seen.add(key)
            found.append(item)

    for m in _DE_STATUTE_RE.finditer(text):
        code = m.group("de_code").strip()
        if code.split()[0] in _CODE_STOPWORDS:
            continue
        section = (m.group("de_sec") or m.group("de_art") or "").strip()
        prefix = "Art." if m.group("de_art") else "§"
        _add({
            "kind": "statute",
            "cite": f"{prefix} {section} {code}",
            "code": code,
            "section": section.split()[0] if section else "",
        })

    for m in _DE_CASE_RE.finditer(text):
        case_no = re.sub(r"\s+", " ", m.group("de_case").strip())
        # Avoid false positives like "10 km 5/20" — register letters are
        # uppercase in real Aktenzeichen (ZR, BvR, AZR, StR, C...)
        letters = case_no.split()[1]
        if not any(ch.isupper() for ch in letters):
            continue
        _add({"kind": "case", "cite": case_no, "code": case_no, "section": ""})

    for m in _XK_ARTICLE_RE.finditer(text):
        code = re.sub(r"\s+", " ", m.group("xk_code").strip())
        section = m.group("xk_sec")
        _add({
            "kind": "statute",
            "cite": f"neni {section} {code}",
            "code": code,
            "section": section,
        })

    for m in _XK_LAW_RE.finditer(text):
        law = re.sub(r"\s+", " ", m.group("xk_law").strip())
        _add({"kind": "law", "cite": law, "code": law, "section": ""})

    return found[:MAX_CITATIONS]


async def _find_docs(
    db: AsyncSession, jurisdiction_id: uuid.UUID, code: str
) -> list[LegalCorpusDoc]:
    """Corpus docs whose reference or title mentions the cited code/number."""
    needle = f"%{code.lower()}%"
    rows = await db.execute(
        select(LegalCorpusDoc)
        .where(
            LegalCorpusDoc.jurisdiction_id == jurisdiction_id,
            or_(
                func.lower(func.coalesce(LegalCorpusDoc.reference, "")).like(needle),
                func.lower(LegalCorpusDoc.title).like(needle),
            ),
        )
        .limit(5)
    )
    return list(rows.scalars())


async def _section_in_doc(
    db: AsyncSession, doc_ids: list[uuid.UUID], kind_prefixes: list[str], section: str
) -> bool:
    """Does any chunk of these docs mention the cited section? Checks the
    chunk's `section` label first, then the text itself."""
    conditions = []
    for prefix in kind_prefixes:
        token = f"{prefix}{section}".lower()
        conditions.append(
            func.lower(func.coalesce(LegalCorpusChunk.section, "")).like(f"%{token}%")
        )
        conditions.append(func.lower(LegalCorpusChunk.text).like(f"%{token}%"))
    row = await db.execute(
        select(LegalCorpusChunk.id)
        .where(LegalCorpusChunk.doc_id.in_(doc_ids), or_(*conditions))
        .limit(1)
    )
    return row.first() is not None


async def verify_citations(
    db: AsyncSession, jurisdiction_id: uuid.UUID | None, answer: str
) -> list[dict]:
    """Extract + verify. Each result:
    {cite, kind, status: verified|law_found|unverified, source_title?}."""
    citations = extract_citations(answer)
    if not citations or jurisdiction_id is None:
        return []

    results: list[dict] = []
    for c in citations:
        try:
            docs = await _find_docs(db, jurisdiction_id, c["code"])
        except Exception:  # never break the answer over a check
            logger.exception("citation check failed for %s", c["cite"])
            continue
        if not docs:
            results.append({"cite": c["cite"], "kind": c["kind"], "status": "unverified"})
            continue
        source_title = docs[0].title
        if c["kind"] in ("case", "law") or not c["section"]:
            results.append({
                "cite": c["cite"], "kind": c["kind"],
                "status": "verified", "source_title": source_title,
            })
            continue
        # Statute with section: require the section inside the matched law
        prefixes = ["§ ", "§", "art. ", "art.", "artikel ", "neni ", "nenin ", "neni"]
        ok = await _section_in_doc(db, [d.id for d in docs], prefixes, c["section"])
        results.append({
            "cite": c["cite"], "kind": c["kind"],
            "status": "verified" if ok else "law_found",
            "source_title": source_title,
        })
    return results
