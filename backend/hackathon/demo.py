#!/usr/bin/env python3
"""Demo CLI: pyetje -> dëshmi -> përgjigje me citime (ose "s'e di").

Pa LLM në këtë hap: përgjigjja ndërtohet nga dëshmitë e kthyera, që të tregojë
qartë se çka do të citohej. Kur të lidhet modeli (lokal ose Meta), vetëm teksti
i përgjigjes ndryshon — citimet vijnë gjithmonë nga i njëjti burim.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_v2 import DSN, terms_of
from harness_v4 import in_domain, is_albanian
from harness_v5 import CANDIDATES, MIN_SIM, TOP_K, rerank
from context_expand import boost_code, expand_context, heading_bonus, heading_search, is_procedural

MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Filtër domeni: tema e pyetjes -> titull ligji. Parandalon që një ligj tjetër që
# përmend të njëjtat fjalë (p.sh. e drejta ndërkombëtare private) të dalë i pari.
TOPIC_FILTERS = (
    ("konkurrenc", "%konkurrenc%"),
    ("konsumator", "%konsumator%"),
    ("të dhëna", "%të dhënave personale%"),
    ("te dhena", "%të dhënave personale%"),
    ("shoqëri", "%shoqëritë tregtare%"),
    ("shoqeri", "%shoqëritë tregtare%"),
    ("martes", "%familjen%"),
    ("trashëgim", "%trashëgim%"),
    ("trashEgim", "%trashëgim%"),
    ("kontrata e punës", "%ligji i punës%"),
    ("kontratës së punës", "%ligji i punës%"),
)


def topic_filter(question: str) -> str | None:
    q = question.lower()
    for key, pat in TOPIC_FILTERS:
        if key in q:
            return pat
    return None
_SQL = """
SELECT d.title, c.section, c.seq, c.text, 1 - (c.embedding <=> %(v)s::vector) AS sim, d.doc_type
FROM legal_corpus_chunks c
JOIN legal_corpus_docs d ON d.id = c.doc_id
WHERE c.embedding IS NOT NULL AND (%(lang)s::text IS NULL OR d.language = %(lang)s::text)
ORDER BY c.embedding <=> %(v)s::vector
LIMIT %(k)s
"""


def retrieve(question: str, model) -> tuple[list[dict], str]:
    terms = terms_of(question)
    if not in_domain(terms):
        return [], "pyetja nuk i përket domenit juridik"
    vec = model.encode([question], normalize_embeddings=True, show_progress_bar=False)[0]
    lit = "[" + ",".join(f"{x:.6f}" for x in vec.tolist()) + "]"
    lang = "sq" if is_albanian(question) else None
    tf = topic_filter(question)
    sql = _SQL.replace("WHERE c.embedding IS NOT NULL",
                       "WHERE c.embedding IS NOT NULL AND (%(tf)s::text IS NULL OR d.title ILIKE %(tf)s::text)")
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(sql, {"v": lit, "k": CANDIDATES, "lang": lang, "tf": tf})
        rows = cur.fetchall()
    cand = [
        {"title": r[0], "section": r[1], "seq": r[2], "snippet": (r[3] or "")[:280], "sim": float(r[4] or 0), "doc_type": r[5]}
        for r in rows
    ]
    cand = [c for c in cand if c["sim"] >= MIN_SIM]
    seen = {(c["title"], c.get("section")) for c in cand}
    if is_procedural(question):
        for h in heading_search(terms):
            if (h["title"], h["section"]) not in seen:
                cand.append(h)
    hits = rerank(cand, terms)[:TOP_K]
    if not hits:
        return [], "pa dëshmi mbi pragun e ngjashmërisë"
    if is_procedural(question):
        hits = heading_bonus(hits, terms)
        hits = boost_code(hits)
    hits, _refs = expand_context(hits, limit_refs=2)
    return hits, ""


def answer(question: str, model) -> str:
    hits, why = retrieve(question, model)
    if not hits:
        return f"s'e di — {why}.\n"
    lines = [f"Pyetja: {question}", "", "Dëshmitë:"]
    for i, h in enumerate(hits, 1):
        section = f" ({h.get('section')})" if h.get("section") else ""
        lines.append(f"  [{i}] {h['title']}{section} — ngjashmëri {h['sim']:.3f}")
        snippet = " ".join((h["snippet"] or "").split())[:220]
        lines.append(f"      «{snippet}»")
    lines += ["", "Përgjigja (e ndërtuar vetëm nga dëshmitë e mësipërme):"]
    top = hits[0]
    section = f" ({top.get('section')})" if top.get("section") else ""
    lines.append(f"  Sipas {top['title']}{section}, kjo pyetje trajtohet në fragmentin [1].")
    lines.append("  Citimet janë të verifikueshme: dokumenti + neni + fragmenti.")
    return "\n".join(lines) + "\n"


def main() -> int:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL, cache_folder=str(Path.home() / ".cache" / "huggingface"))
    questions = sys.argv[1:] or [
        "Kur fillon afati i parashkrimit të kërkesave?",
        "Sa është TVSH-ja në Norvegji?",
    ]
    for q in questions:
        print(answer(q, model))
        print("-" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())

