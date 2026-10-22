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
            h["score"] = h.get("score", h.get("sim", 0.0)) + amount * min(n, 2)
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


def heading_search(terms: list[str], per_term: int = 3) -> list[dict]:
    """Kerko ne TITUJT e neneve, jo vetem ne tekst.

    Pa kete, neni i duhur (p.sh. 'Paraburgimi', Neni 185) mund te mos hyje fare ne
    kandidatet e kerkimit vektor, sepse teksti i tij i shkurter i titullit nuk ka
    ngjashmeri te larte me pyetjen.
    """
    out, seen = [], set()
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        for t in [x for x in terms if len(x) > 4][:3]:
            cur.execute(SQL_HEADING, {"t": "%" + t + "%", "k": per_term})
            for row in cur.fetchall():
                key = (row[0], row[1])
                if key in seen:
                    continue
                seen.add(key)
                out.append({"title": row[0], "section": row[1], "seq": row[2],
                            "snippet": (row[3] or "")[:280], "sim": 0.55,
                            "doc_type": row[4], "from_heading": True})
    return out
