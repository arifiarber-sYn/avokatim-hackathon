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
COVERAGE_BONUS = 0.06
# Ligji në fuqi > ligji i vjetër/i përkohshëm > akti amendues: zbritje të vogla, jo filtra,
# që kodi i vjetër penal të mos dalë përpara Kodit të Procedurës Penale në fuqi.
PENALTY_TEMPORARY = 0.15
PENALTY_AMENDMENT = 0.04
# Pyetje përkufizuese ("çfarë është X?") -> neni që e PËRKUFIZON, jo nëntipi i tij.
DEF_WORDS = ("çfarë është", "cfare eshte", "çka është", "cka eshte", "përkufizim", "perkufizim")
DEF_TITLES = ("natyra", "përkufizim", "perkufizim", "objekti", "kuptimi", "definicioni", "termat")
DEF_BONUS = 0.10

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
SELECT d.id, d.title, c.section, c.seq, c.text, 1 - (c.embedding <=> %(v)s::vector) AS sim, d.doc_type
FROM legal_corpus_chunks c
JOIN legal_corpus_docs d ON d.id = c.doc_id
WHERE c.embedding IS NOT NULL AND (%(lang)s::text IS NULL OR d.language = %(lang)s::text)
ORDER BY c.embedding <=> %(v)s::vector
LIMIT %(k)s
"""



SQL_FULL = """
SELECT c.text FROM legal_corpus_chunks c
WHERE c.doc_id = %(doc)s AND c.section = %(sec)s
ORDER BY c.seq
"""


def _coverage(text: str, terms: list[str]) -> float:
    """Sa pjesë e termave juridikë të pyetjes gjenden në tekstin e plotë të nenit."""
    if not terms:
        return 0.0
    low = " ".join(text.split()).lower()
    return sum(1 for x in terms if x in low) / len(terms)


def refine_articles(hits: list[dict], terms: list[str], top_k: int = TOP_K, pool: int = 12, question: str = "") -> list[dict]:
    """Renditje në nivel NENI, mbi tekstin e plotë (jo vetëm 280 shkronjat e para).

    Skori = ngjashmëria më e mirë e fragmentit + mbulimi i termave në të gjithë nenin.
    Shmang gjithashtu që i njëjti nen të zërë tri vende në top-5.
    """
    if not hits:
        return hits
    ql = question.lower()
    def_intent = any(w in ql for w in DEF_WORDS)
    groups: dict[tuple, dict] = {}
    order = []
    for h in hits:
        key = (h["title"], h.get("section"))
        if key not in groups:
            groups[key] = dict(h)
            groups[key]["parts"] = 1
            order.append(key)
        else:
            g = groups[key]
            if h["sim"] > g["sim"]:
                g.update({k: v for k, v in h.items() if k != "parts"})
            g["parts"] += 1
    keys = order[:pool]
    out = []
    try:
        with psycopg.connect(DSN) as conn, conn.cursor() as cur:
            for key in keys:
                g = groups[key]
                body = g.get("snippet") or ""
                if g.get("doc_id") and g.get("section"):
                    cur.execute(SQL_FULL, {"doc": g["doc_id"], "sec": g["section"]})
                    body = " ".join((row[0] or "") for row in cur.fetchall())[:6000]
                cov = _coverage(body, terms)
                g = dict(g)
                g["coverage"] = round(cov, 3)
                if g.get("doc_id") and g.get("section"):
                    cur.execute("SELECT title FROM hackathon_article_titles WHERE doc_id=%(doc)s AND section=%(sec)s",
                                {"doc": g["doc_id"], "sec": g["section"]})
                    row = cur.fetchone()
                    if row and row[0]:
                        g["art_title"] = row[0]
                low_title = (g.get("title") or "").lower()
                pen = 0.0
                if "përkohshëm" in low_title:
                    pen += PENALTY_TEMPORARY
                if "ndryshimin dhe plotësim" in low_title:
                    pen += PENALTY_AMENDMENT
                g["score"] = g["score"] + COVERAGE_BONUS * cov - pen
                if def_intent and any(w in (g.get("art_title") or "").lower() for w in DEF_TITLES):
                    g["score"] += DEF_BONUS
                g["snippet"] = " ".join(body.split())[:900] or g["snippet"]
                out.append(g)
    except psycopg.Error:
        return hits
    out.sort(key=lambda h: h["score"], reverse=True)
    return out[:top_k]


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
        {"doc_id": r[0], "title": r[1], "section": r[2], "seq": r[3], "snippet": (r[4] or "")[:280], "sim": float(r[5] or 0), "doc_type": r[6]}
        for r in rows
    ]
    cand = [c for c in cand if c["sim"] >= MIN_SIM]
    seen = {(c["title"], c.get("section")) for c in cand}
    if is_procedural(question):
        for h in heading_search(terms):
            if (h["title"], h["section"]) not in seen:
                cand.append(h)
    hits = refine_articles(rerank(cand, terms), terms, question=question)[:TOP_K]
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

