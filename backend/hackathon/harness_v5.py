#!/usr/bin/env python3
"""Harness v5 — vektor + filtër gjuhe + rirenditje hibride.

v4 ktheu marrëveshje kredie për pyetjen për parashkrimin: vektori kapte temën
"afat/kredi", jo termin juridik. v5 merr 50 kandidatë me vektor dhe i rirendit
me një bonus për termat juridikë të pyetjes që shfaqen në tekst.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_v2 import DSN, terms_of
from harness_v4 import STRONG_HINTS, in_domain, is_albanian

TOP_K = 5
CANDIDATES = 50
MIN_SIM = 0.42
KW_BONUS = 0.12


def strong_terms(terms: list[str]) -> list[str]:
    return [t for t in terms if any(t.startswith(h) or h.startswith(t) for h in STRONG_HINTS)]


def rerank(hits: list[dict], terms: list[str]) -> list[dict]:
    keys = strong_terms(terms) or terms
    for h in hits:
        text = (h["snippet"] or "").lower()
        hits_count = sum(1 for k in keys if k in text)
        h["kw_hits"] = hits_count
        h["score"] = h["sim"] + KW_BONUS * min(hits_count, 3)
    return sorted(hits, key=lambda h: h["score"], reverse=True)


def main() -> int:
    from sentence_transformers import SentenceTransformer

    here = Path(__file__).resolve().parent
    qfile = os.environ.get("HARNESS_Q", "questions.json")
    questions = json.loads((here / qfile).read_text(encoding="utf-8"))
    model = SentenceTransformer(
        os.environ.get("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
        cache_folder=str(Path.home() / ".cache" / "huggingface"),
    )
    vecs = model.encode([q["question"] for q in questions], normalize_embeddings=True, show_progress_bar=False)
    out_dir = Path(os.environ.get("HARNESS_OUT", here.parent.parent / "data" / "evidence"))
    out_dir.mkdir(parents=True, exist_ok=True)

    sql = """
    SELECT d.title, c.seq, c.text, 1 - (c.embedding <=> %(v)s::vector) AS sim
    FROM legal_corpus_chunks c
    JOIN legal_corpus_docs d ON d.id = c.doc_id
    WHERE c.embedding IS NOT NULL AND (%(lang)s::text IS NULL OR d.language = %(lang)s::text)
    ORDER BY c.embedding <=> %(v)s::vector
    LIMIT %(k)s
    """

    results = []
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        for item, vec in zip(questions, vecs):
            terms = terms_of(item["question"])
            why, hits = "", []
            if not in_domain(terms):
                why = "jashtë domenit juridik"
            else:
                lang = "sq" if is_albanian(item["question"]) else None
                lit = "[" + ",".join(f"{x:.6f}" for x in vec.tolist()) + "]"
                cur.execute(sql, {"v": lit, "k": CANDIDATES, "lang": lang})
                cand = [
                    {"title": r[0], "seq": r[1], "snippet": (r[2] or "")[:280], "sim": float(r[3] or 0)}
                    for r in cur.fetchall()
                ]
                cand = [c for c in cand if c["sim"] >= MIN_SIM]
                hits = rerank(cand, terms)[:TOP_K]
                if not hits:
                    why = "nën pragun e ngjashmërisë"
            exp = (item.get("expected_doc") or "").lower()
            kw = (item.get("keyword") or "").lower()
            hit = bool(exp) and any(exp in (h["title"] or "").lower() for h in hits)
            kwm = bool(kw) and any(kw in (h["snippet"] or "").lower() for h in hits)
            refused = len(hits) == 0
            ok = refused if not item.get("in_corpus") else (hit or kwm)
            results.append({"id": item["id"], "question": item["question"],
                            "in_corpus": bool(item.get("in_corpus")), "terms": terms,
                            "refused": refused, "why": why, "hits": hits,
                            "hit_at_5": hit, "keyword_at_5": kwm, "ok": ok})

    inside = [r for r in results if r["in_corpus"]]
    outside = [r for r in results if not r["in_corpus"]]
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "version": 5,
              "mode": "vector+lang+hybrid", "top_k": TOP_K, "candidates": CANDIDATES,
              "min_sim": MIN_SIM, "kw_bonus": KW_BONUS,
              "in_corpus": {"count": len(inside), "ok": sum(r["ok"] for r in inside),
                            "hit_at_5": sum(r["hit_at_5"] for r in inside),
                            "keyword_at_5": sum(r["keyword_at_5"] for r in inside)},
              "outside_corpus": {"count": len(outside), "ok": sum(r["ok"] for r in outside),
                                 "refused": sum(r["refused"] for r in outside)},
              "results": results}
    tag = os.environ.get("HARNESS_TAG", "")
    prefix = f"harness-v5-{tag}-" if tag else "harness-v5-"
    path = out_dir / f"{prefix}{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"raport: {path.name}")
    print(f"brenda: {report['in_corpus']['ok']}/{report['in_corpus']['count']} "
          f"(hit@5 {report['in_corpus']['hit_at_5']}, kw@5 {report['in_corpus']['keyword_at_5']})")
    print(f"jashtë: {report['outside_corpus']['ok']}/{report['outside_corpus']['count']} refuzuar")
    for r in results:
        top = r["hits"][0] if r["hits"] else None
        extra = f"sim={top['sim']:.3f} kw={top.get('kw_hits','-')}" if top else ""
        print(("OK   " if r["ok"] else "GABIM"), r["id"], f"hits={len(r['hits'])}", extra,
              (r["why"] or "")[:22], "|", r["question"][:40])
    return 0


if __name__ == "__main__":
    sys.exit(main())

