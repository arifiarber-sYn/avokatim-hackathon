"""Citation verification for Ava's answers (D-059 F6; v2 audit 2026-09-18).

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

v2 (Protégé lesson, adapted from the HagaDosja AVOKATI verifier): when the
answer QUOTES text next to a citation (\"...\" brenda së njëjtës fjali), the
quote itself is verified against the matched doc's chunks with word 5-gram
shingle coverage. Statuses gain \"approx\" (quote found approximately) and
results carry doc_id/chunk_id so the UI can deep-link to the source. A
single repair round (api/assistant.py) can then ask the model to correct or
drop citations whose quotes were not found.
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
    r"(?:\s+(?:i|të|te))?\s+"
    # bare code must be REAL uppercase (LPK, LMD, KPP…) — scoped (?-i:) so
    # words like "Ligjit" never pass as a code (eval finding 2026-09-18)
    r"(?P<xk_code>(?-i:[A-ZËÇ]{2,6})(?=[-\s.,;)]|$)"
    r"|Ligj\w*\s+[Nn]r\.?\s*[\d/L\-]+"
    # named law: "neni 34 i Ligjit për Familjen" / "të Ligjit të Punës"
    r"|Ligj\w*\s+(?:për|e|i|të)\s+\w[\wë]*(?:\s+(?-i:[A-ZËÇa-zëç])[\wë]*){0,3}"
    r"|Kod\w*\s+[A-Za-zë ]{3,40})",
    re.IGNORECASE,
)
_XK_LAW_RE = re.compile(r"(?P<xk_law>Ligji\s+[Nn]r\.?\s*\d{2}/L-\d{1,4})")
# The bare law number ("03/L-006") — that is how `reference` is stored in
# the corpus, so lookups must use it, not the full "Ligji Nr. …" phrase.
_XK_LAW_NO_RE = re.compile(r"\d{2}/L-\d{1,4}")

# Words the statute regex may capture that are never law codes
_CODE_STOPWORDS = {
    "Abs", "Satz", "Nr", "Nummer", "Alt", "Var", "Halbs", "Rn", "Ziff",
    "UND", "ODER", "DER", "DES", "DIE",
}

# --- Quoted passages next to a citation (v2). 25–400 chars, straight or
# typographic quotes (sq/de use „…" and «…» too).
_QUOTE_RE = re.compile(r'[„"“«]([^"”»„]{25,400})["”»]')
# A quote belongs to a citation only within the same sentence-ish span:
# ≤300 chars apart, no newline between them (either order).
_QUOTE_MAX_GAP = 300

# Shingle thresholds (HagaDosja-calibrated)
_QUOTE_VERIFIED = 0.85
_QUOTE_APPROX = 0.70
# How many candidate chunks we fetch per citation for quote matching
_QUOTE_CHUNK_LIMIT = 40


def _norm_text(s: str) -> str:
    """Normalize for quote matching: strip markdown, unify quotes/dashes,
    lowercase, collapse whitespace."""
    s = re.sub(r"[*_`#>\[\]]", " ", s)
    for a, b in (("„", '"'), ("“", '"'), ("”", '"'), ("«", '"'), ("»", '"'),
                 ("’", "'"), ("‘", "'"), ("–", "-"), ("—", "-")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip().lower()


def _quote_coverage(quote: str, text: str) -> float:
    """Share of the quote found in text — word 5-gram shingle coverage
    (robust to markdown, redactions and ellipses)."""
    q_tokens = _norm_text(quote).split()
    t = " " + _norm_text(text) + " "
    if not q_tokens or not t.strip():
        return 0.0
    if " ".join(q_tokens) in t:
        return 1.0
    n = 5
    if len(q_tokens) < n:
        from difflib import SequenceMatcher

        return SequenceMatcher(None, " ".join(q_tokens), t).ratio()
    shingles = [" ".join(q_tokens[i:i + n]) for i in range(len(q_tokens) - n + 1)]
    return sum(1 for s in shingles if s in t) / len(shingles)


def _attribute_quotes(text: str, citations: list[dict]) -> dict[str, list[str]]:
    """Map citation cite-string -> quotes appearing in the same sentence.
    Each quote is attributed to the nearest citation (before or after).
    Positions come from extraction (`pos`) — the rendered cite string is
    normalized and may not literally appear in the answer text."""
    positions: list[tuple[int, dict]] = [
        (c["pos"], c) for c in citations if c.get("pos", -1) >= 0
    ]
    out: dict[str, list[str]] = {}
    for qm in _QUOTE_RE.finditer(text):
        best: tuple[int, dict] | None = None
        for pos, c in positions:
            gap_text = (
                text[qm.end():pos] if pos >= qm.end() else text[pos:qm.start()]
            )
            gap = len(gap_text)
            if gap <= _QUOTE_MAX_GAP and "\n" not in gap_text:
                if best is None or gap < best[0]:
                    best = (gap, c)
        if best is not None:
            out.setdefault(best[1]["cite"], []).append(qm.group(1))
    return out


def _rare_words(quote: str, k: int = 3) -> list[str]:
    words = [w for w in re.findall(r"[a-zA-ZëçäöüßĐđŠšŽžĆć]{5,}", _norm_text(quote))]
    # longest words are the rarest bet without a frequency table
    return sorted(set(words), key=len, reverse=True)[:k]


REPAIR_PROMPT = (
    "Ti je redaktori i verifikimit të citimeve. Përgjigja e mëposhtme përmban "
    "citime që NUK u verifikuan dot kundër korpusit tonë ligjor. Ri-shkruaje "
    "përgjigjen duke i KORRIGJUAR citimet e gabuara (kur BURIMET REALE më "
    "poshtë tregojnë nenin e saktë, përdore atë numër) ose duke i HEQUR "
    "pohimet dhe thonjëzat që mbështeten vetëm në to. MOS shto citime të "
    "reja, mos ndrysho asgjë tjetër në përmbajtje, ruaj gjuhën dhe "
    "formatimin. Kthe VETËM përgjigjen e korrigjuar, pa koment shtesë."
)


async def _repair_sources(
    db: AsyncSession,
    jurisdiction_id: uuid.UUID,
    answer: str,
    bad: list[dict],
) -> str:
    """Ground truth for the repair round: for every failed citation, the REAL
    text of the cited article, and — when a quoted passage actually lives in
    a different article of the same law — where it was found. This is what
    lets the model fix a wrong article number instead of just deleting the
    claim (old-numbering hallucinations, eval case #11)."""
    bad_cites = {c["cite"] for c in bad}
    citations = [c for c in extract_citations(answer) if c["cite"] in bad_cites]
    quotes_by_cite = _attribute_quotes(answer, citations)
    parts: list[str] = []
    for c in citations:
        docs = await _find_docs(db, jurisdiction_id, c["code"])
        if not docs:
            continue
        doc_ids = [d.id for d in docs]
        if c.get("section"):
            prefixes = ["§ ", "§", "art. ", "art.", "neni ", "nenin ", "neni"]
            chunk_id = await _section_in_doc(db, doc_ids, prefixes, c["section"])
            if chunk_id is not None:
                chunk = await db.get(LegalCorpusChunk, chunk_id)
                if chunk is not None:
                    parts.append(
                        f"TEKSTI REAL i '{c['cite']}' ({docs[0].title}):\n"
                        f"{chunk.text[:700]}"
                    )
        for quote in quotes_by_cite.get(c["cite"], [])[:3]:
            words = _rare_words(quote)
            if not words:
                continue
            conds = [
                func.lower(LegalCorpusChunk.text).like(f"%{w.lower()}%")
                for w in words
            ]
            rows = await db.execute(
                select(LegalCorpusChunk)
                .where(LegalCorpusChunk.doc_id.in_(doc_ids), *conds)
                .limit(5)
            )
            best, best_cov = None, 0.0
            for cand in rows.scalars():
                cov = _quote_coverage(quote, cand.text)
                if cov > best_cov:
                    best, best_cov = cand, cov
            if best is not None and best_cov >= 0.6 and best.section:
                parts.append(
                    f"Citati «{quote[:160]}» gjendet në të vërtetë te "
                    f"'{best.section}' i {docs[0].title} (mbulimi {best_cov:.2f})."
                )
    return "\n\n".join(parts)


async def repair_citations(
    db: AsyncSession,
    jurisdiction_id: uuid.UUID | None,
    answer: str,
    checked: list[dict],
    provider_name: str | None = None,
) -> tuple[str, list[dict]] | None:
    """One bounded repair round (v2): when citations are unverified, ask the
    model to correct or drop them, then re-verify. Returns (new_answer,
    new_checked) only when the repair genuinely improved things; None
    otherwise. Never raises."""
    from app.llm import get_provider
    from app.llm.base import ChatMessage

    bad = [c for c in checked if c["status"] == "unverified"]
    if not bad:
        return None
    try:
        listing = "\n".join(
            f"- {c['cite']}" + (f" ({c['note']})" if c.get("note") else "")
            for c in bad
        )
        sources = ""
        if jurisdiction_id is not None:
            try:
                sources = await _repair_sources(db, jurisdiction_id, answer, bad)
            except Exception:
                logger.exception("repair source grounding failed")
        if sources:
            listing += f"\n\nBURIMET REALE:\n{sources}"
        provider = get_provider(provider_name)
        result = await provider.chat(
            [
                ChatMessage(role="system", content=REPAIR_PROMPT),
                ChatMessage(
                    role="user",
                    content=f"CITIMET E PAVERIFIKUARA:\n{listing}\n\n"
                            f"PËRGJIGJA:\n{answer}",
                ),
            ],
            temperature=0.0,
        )
        revised = (result.content or "").strip()
        if not revised or len(revised) < len(answer) * 0.3:
            return None  # the model gutted the answer — keep the original
        new_checked = await verify_citations(db, jurisdiction_id, revised)
        n_bad_before = len(bad)
        n_bad_after = sum(1 for c in new_checked if c["status"] == "unverified")
        if n_bad_after < n_bad_before:
            return revised, new_checked
        return None
    except Exception:
        logger.exception("citation repair round failed")
        return None


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
            "pos": m.start(),
        })

    for m in _DE_CASE_RE.finditer(text):
        case_no = re.sub(r"\s+", " ", m.group("de_case").strip())
        # Avoid false positives like "10 km 5/20" — register letters are
        # uppercase in real Aktenzeichen (ZR, BvR, AZR, StR, C...)
        letters = case_no.split()[1]
        if not any(ch.isupper() for ch in letters):
            continue
        _add({"kind": "case", "cite": case_no, "code": case_no, "section": "",
              "pos": m.start()})

    for m in _XK_ARTICLE_RE.finditer(text):
        code = re.sub(r"\s+", " ", m.group("xk_code").strip())
        section = m.group("xk_sec")
        law_no = _XK_LAW_NO_RE.search(code)
        lookup = law_no.group(0) if law_no else code
        # Named law ("Ligjit për Familjen"): look up by the title fragment
        # after the inflected "Ligji/Ligjit" word — corpus titles start with
        # "Ligji", the citation may inflect it.
        if not law_no and re.match(r"(?i)ligj\w*\s+(?:për|e|i|të)\s", code):
            lookup = re.sub(r"(?i)^ligj\w*\s+", "", code)
        _add({
            "kind": "statute",
            "cite": f"neni {section} {code}",
            "code": lookup,
            "section": section,
            "pos": m.start(),
        })

    for m in _XK_LAW_RE.finditer(text):
        law = re.sub(r"\s+", " ", m.group("xk_law").strip())
        law_no = _XK_LAW_NO_RE.search(law)
        _add({
            "kind": "law",
            "cite": law,
            "code": law_no.group(0) if law_no else law,
            "section": "",
            "pos": m.start(),
        })

    return found[:MAX_CITATIONS]


# Rank base acts above amendments ("për ndryshimin/plotësimin e ...") and
# judgments: an article lives in the base code, not in the amending law or
# in a decision whose file number happens to contain the abbreviation.
_AMENDMENT_MARKERS = ("ndryshimin", "plotësimin", "plotesimin")

_LAW_STOPWORDS = {
    "i", "e", "te", "se", "per", "ne", "nr", "të", "së", "për",
    "kosoves", "kosovës", "republikes", "republikës", "republika",
}
_DIACRITICS = str.maketrans("ëçÿ", "ecy")


def _norm_law_name(name: str) -> str:
    """Normalize an inflected Albanian law name for the name-alias lookup:
    'Ligjit të Punës' and 'Ligji i Punës' both become 'ligj punes'."""
    s = name.lower().translate(_DIACRITICS)
    words = []
    for w in re.findall(r"[a-z0-9/\-]+", s):
        if w in _LAW_STOPWORDS:
            continue
        if w in ("ligjit", "ligji", "ligjin"):
            w = "ligj"
        elif w in ("kodit", "kodi", "kodin"):
            w = "kod"
        words.append(w)
    return " ".join(words)


def _doc_rank(doc: LegalCorpusDoc) -> tuple[int, int]:
    title = (doc.title or "").lower()
    is_amendment = any(m in title for m in _AMENDMENT_MARKERS)
    is_statute = (doc.doc_type or "") in ("code", "law", "regulation")
    return (0 if is_statute and not is_amendment else 1 if is_statute else 2, 0)


async def _find_docs(
    db: AsyncSession, jurisdiction_id: uuid.UUID, code: str
) -> list[LegalCorpusDoc]:
    """Corpus docs whose reference or title mentions the cited code/number.

    Order of attempts:
    1. Statute-abbreviation alias map (XK_STATUTE_REFS): "KPP" -> the actual
       procedure code by gazette reference — never a judgment whose file
       number contains the letters (the KPPP.nr.284/23 lesson).
    2. Exact-ish reference/title LIKE lookup; multi-word lookups (named laws)
       retry with a shortened phrase. Results are ranked base act >
       amendment > judgment."""
    from app.seeds.kosovo import XK_STATUTE_NAME_REFS, XK_STATUTE_REFS

    refs = XK_STATUTE_REFS.get(code.strip().upper())
    if not refs and " " in code.strip():
        # The extraction regex may capture trailing sentence words after the
        # law name ("Ligjit të Punës pushimi vjetor…") and may have stripped
        # the inflected head ("Ligjit") — retry with shrinking prefixes, with
        # and without the "ligj" head word.
        tokens = _norm_law_name(code).split()
        if tokens and tokens[0] not in ("ligj", "kod"):
            tokens.insert(0, "ligj")
        while len(tokens) >= 2 and not refs:
            refs = XK_STATUTE_NAME_REFS.get(" ".join(tokens))
            tokens.pop()
    if refs:
        rows = await db.execute(
            select(LegalCorpusDoc).where(
                LegalCorpusDoc.jurisdiction_id == jurisdiction_id,
                LegalCorpusDoc.reference.in_(refs),
            )
        )
        docs = sorted(
            rows.scalars(),
            key=lambda d: (_doc_rank(d), refs.index(d.reference)),
        )
        if docs:
            return docs[:5]

    words = code.split()
    attempts = [code]
    if len(words) > 2:
        attempts.append(" ".join(words[:3]))
        attempts.append(" ".join(words[:2]))
    for attempt in attempts:
        needle = f"%{attempt.lower()}%"
        rows = await db.execute(
            select(LegalCorpusDoc)
            .where(
                LegalCorpusDoc.jurisdiction_id == jurisdiction_id,
                or_(
                    func.lower(func.coalesce(LegalCorpusDoc.reference, "")).like(needle),
                    func.lower(LegalCorpusDoc.title).like(needle),
                ),
            )
            .limit(15)
        )
        docs = sorted(rows.scalars(), key=_doc_rank)
        if docs:
            return docs[:5]
    return []


async def _section_in_doc(
    db: AsyncSession, doc_ids: list[uuid.UUID], kind_prefixes: list[str], section: str
) -> uuid.UUID | None:
    """The id of a chunk of these docs mentioning the cited section (or None).
    Checks the chunk's `section` label first, then the text itself."""
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
    first = row.first()
    return first[0] if first else None


async def _verify_quotes(
    db: AsyncSession, doc_ids: list[uuid.UUID], quotes: list[str]
) -> tuple[str, uuid.UUID | None, float]:
    """Verify quoted passages against the chunks of the matched docs.
    Returns (status, best_chunk_id, worst_coverage) where status is
    verified|approx|unverified — the WORST quote decides (one fabricated
    quote poisons the citation)."""
    worst_status, worst_cov = "verified", 1.0
    best_chunk: uuid.UUID | None = None
    for quote in quotes[:5]:  # bound the DB work per citation
        conditions = [
            func.lower(LegalCorpusChunk.text).like(f"%{w}%") for w in _rare_words(quote)
        ]
        stmt = (
            select(LegalCorpusChunk.id, LegalCorpusChunk.text)
            .where(LegalCorpusChunk.doc_id.in_(doc_ids))
            .limit(_QUOTE_CHUNK_LIMIT)
        )
        if conditions:
            stmt = stmt.where(or_(*conditions))
        rows = (await db.execute(stmt)).all()
        if not rows:
            # fall back to the first chunks of the doc (short laws)
            rows = (
                await db.execute(
                    select(LegalCorpusChunk.id, LegalCorpusChunk.text)
                    .where(LegalCorpusChunk.doc_id.in_(doc_ids))
                    .order_by(LegalCorpusChunk.seq)
                    .limit(_QUOTE_CHUNK_LIMIT)
                )
            ).all()
        best_q, best_q_chunk = 0.0, None
        for chunk_id, text in rows:
            cov = _quote_coverage(quote, text)
            if cov > best_q:
                best_q, best_q_chunk = cov, chunk_id
                if best_q > 0.95:
                    break
        if best_q < worst_cov:
            worst_cov = best_q
        if best_chunk is None and best_q >= _QUOTE_APPROX:
            best_chunk = best_q_chunk
    if worst_cov >= _QUOTE_VERIFIED:
        return "verified", best_chunk, worst_cov
    if worst_cov >= _QUOTE_APPROX:
        return "approx", best_chunk, worst_cov
    return "unverified", best_chunk, worst_cov


async def verify_citations(
    db: AsyncSession, jurisdiction_id: uuid.UUID | None, answer: str
) -> list[dict]:
    """Extract + verify. Each result:
    {cite, kind, status: verified|approx|law_found|unverified,
     source_title?, doc_id?, chunk_id?, note?}.

    v2: quotes attributed to a citation are verified against the source
    chunks; a quote that is not found downgrades the citation to
    unverified even when the law itself exists (fabricated-quote guard)."""
    citations = extract_citations(answer)
    if not citations or jurisdiction_id is None:
        return []
    quotes_by_cite = _attribute_quotes(answer, citations)

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
        doc_ids = [d.id for d in docs]
        base: dict = {
            "cite": c["cite"], "kind": c["kind"],
            "source_title": source_title, "doc_id": str(docs[0].id),
        }
        try:
            if c["kind"] in ("case", "law") or not c["section"]:
                base["status"] = "verified"
            else:
                # Statute with section: require the section inside the law
                prefixes = ["§ ", "§", "art. ", "art.", "artikel ",
                            "neni ", "nenin ", "neni"]
                chunk_id = await _section_in_doc(db, doc_ids, prefixes, c["section"])
                base["status"] = "verified" if chunk_id else "law_found"
                if chunk_id:
                    base["chunk_id"] = str(chunk_id)

            # v2: verify quoted text (the worst quote decides)
            quotes = quotes_by_cite.get(c["cite"], [])
            if quotes and base["status"] in ("verified", "law_found"):
                q_status, q_chunk, cov = await _verify_quotes(db, doc_ids, quotes)
                if q_status == "unverified":
                    base["status"] = "unverified"
                    base["note"] = f"cituar tekst që s'u gjet në burim ({cov:.2f})"
                elif q_status == "approx":
                    base["status"] = "approx"
                    base["note"] = f"citati u gjet përafërsisht ({cov:.2f})"
                if q_chunk is not None:
                    base["chunk_id"] = str(q_chunk)
        except Exception:
            logger.exception("citation quote check failed for %s", c["cite"])
        results.append(base)
    return results
