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

