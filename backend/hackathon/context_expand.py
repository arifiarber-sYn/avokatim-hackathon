"""Zgjerim konteksti: kur neni referon nje nen tjeter, sill edhe ate.
Preference per KOD ne pyetjet procedurale (paraburgim, afat, ankim, lirim)."""
from __future__ import annotations

import re

import psycopg

from harness_v2 import DSN

PROCEDURAL = ("paraburgim", "afat", "procedur", "lirohet", "lirim", "ankes", "aktakuz",
              "gjykim", "hetim", "mase", "masë", "afate")

SQL_ARTICLE = """
SELECT d.title, c.section, c.seq, c.text, d.doc_type
FROM legal_corpus_chunks c
JOIN legal_corpus_docs d ON d.id = c.doc_id
WHERE d.title = %(t)s AND c.section ILIKE %(s)s
LIMIT 1
"""


def is_procedural(question: str) -> bool:
    q = question.lower()
    return any(k in q for k in PROCEDURAL)


def boost_code(hits: list[dict], amount: float = 0.08) -> list[dict]:
    for h in hits:
        if (h.get("doc_type") or "").lower() == "code":
            h["score"] = h.get("score", h.get("sim", 0.0)) + amount
    return sorted(hits, key=lambda h: h.get("score", h.get("sim", 0.0)), reverse=True)


def expand_context(hits: list[dict], limit_refs: int = 2) -> tuple[list[dict], list[str]]:
    """Kthen (hits, refs) ku refs jane nenet e shtuara."""
    added, notes = [], []
    seen = {(h.get("title"), h.get("section")) for h in hits}
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        for h in hits[:limit_refs]:
            text = (h.get("snippet") or "").lower()
            for m in re.finditer(r"nen(?:i|it|in|et|eve|ave)?\s+(\d+)", text):
                num = m.group(1)
                sect = h.get("section") or ""
                if num in sect:
                    continue
                cur.execute(SQL_ARTICLE, {"t": h.get("title"), "s": "%" + num + "%"})
                row = cur.fetchone()
                if not row:
                    continue
                key = (row[0], row[1])
                if key in seen:
                    continue
                seen.add(key)
                added.append({"title": row[0], "section": row[1], "seq": row[2],
                              "snippet": (row[3] or "")[:280], "sim": h.get("sim", 0.0),
                              "doc_type": row[4], "referenced_by": sect})
                notes.append(f"{sect} -> {row[1]}")
    return hits + added, notes



def heading_bonus(hits: list[dict], terms: list[str], amount: float = 0.09) -> list[dict]:
    """Renditje ne nivel neni: titulli i nenit (rreshtat e pare te fragmentit) peshon.

    Pa kete, kodi i duhur fiton mbi dokument, por neni brenda kodit mund te jete i gabuar
    (p.sh. 'Arrestimi gjate fazes se hetimit' per pyetjen 'kur lirohet nga paraburgimi').
    """
    import re as _re
    for h in hits:
        if (h.get("doc_type") or "").lower() not in {"law", "code"}:
            h["head_hits"] = 0
            continue
        text = (h.get("snippet") or "")
        head = " ".join(text.splitlines()[:2]).lower()
        if not head:
            h["head_hits"] = 0
            continue
        n = sum(1 for t in terms if len(t) > 3 and t in head)
        h["head_hits"] = n
        if n:
            bonus = amount * min(n, 2)
            if h.get("from_heading"):
                bonus += 0.06
            h["score"] = h.get("score", h.get("sim", 0.0)) + bonus
    return sorted(hits, key=lambda x: x.get("score", x.get("sim", 0.0)), reverse=True)


SQL_HEADING = """
SELECT d.title, c.section, c.seq, c.text, d.doc_type
FROM legal_corpus_chunks c
JOIN legal_corpus_docs d ON d.id = c.doc_id
WHERE d.language = 'sq' AND d.doc_type IN ('law','code')
  AND left(c.text, 120) ILIKE %(t)s
ORDER BY length(c.text)
LIMIT %(k)s
"""


def heading_search(terms: list[str], per_term: int = 15, keep: int = 12) -> list[dict]:
    """Kerko ne TITUJT e neneve dhe rendit sipas perputhjes se termave.

    Renditja me gjatesi te fragmentit nuk punon: per "kur lirohet nga paraburgimi"
    nxirrte nje nen te shkurter te nje kodi tjeter, jo "Neni 185 Paraburgimi".
    Tani cdo kandidat vleresohet me sa terma te pyetjes ndodhen ne titull.
    """
    out: dict[tuple, dict] = {}
    probes = [t for t in terms if len(t) > 4][:3]
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        for t in probes:
            cur.execute(SQL_HEADING, {"t": "%" + t + "%", "k": per_term})
            for row in cur.fetchall():
                title, section, seq, text, dtype = row
                head = " ".join((text or "").splitlines()[:2]).lower()
                title_zone = head[:60]
                score = 3 * sum(1 for x in terms if len(x) > 3 and x in title_zone)
                score += sum(1 for x in terms if len(x) > 3 and x in head)
                key = (title, section)
                item = {"title": title, "section": section, "seq": seq,
                        "snippet": (text or "")[:280], "sim": 0.60,
                        "doc_type": dtype, "from_heading": True, "head_score": score}
                if key not in out or item["head_score"] > out[key]["head_score"]:
                    out[key] = item
    ranked = sorted(out.values(), key=lambda x: (x["head_score"], -len(x["snippet"])), reverse=True)
    return [x for x in ranked if x["head_score"] > 0][:keep]
