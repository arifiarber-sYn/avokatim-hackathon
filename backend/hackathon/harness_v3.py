#!/usr/bin/env python3
"""Harness v3 — kërkim vektor (pgvector) + portë domeni.

Modeli: paraphrase-multilingual-MiniLM-L12-v2 (384 dim), i ruajtur lokalisht.
Asnjë tekst nuk del nga makina: embeddings llogariten këtu.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_v2 import DSN, LEGAL_HINTS, terms_of

TOP_K = 5
MIN_SIM = 0.42


def in_domain(terms: list[str]) -> bool:
    return any(t.startswith(h) or h.startswith(t) for t in terms for h in LEGAL_HINTS)


def main() -> int:
    from sentence_transformers import SentenceTransformer

    here = Path(__file__).resolve().parent
    questions = json.loads((here / "questions.json").read_text(encoding="utf-8"))
    model_name = os.environ.get(
        "EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    model = SentenceTransformer(model_name, cache_folder=str(Path.home() / ".cache" / "huggingface"))

    vecs = model.encode([q["question"] for q in questions], normalize_embeddings=True, show_progress_bar=False)
    out_dir = Path(os.environ.get("HARNESS_OUT", here.parent.parent / "data" / "evidence"))
    out_dir.mkdir(parents=True, exist_ok=True)

    sql = """
    SELECT d.title, c.seq, c.text, 1 - (c.embedding <=> %(v)s::vector) AS sim
    FROM legal_corpus_chunks c
    JOIN legal_corpus_docs d ON d.id = c.doc_id
    WHERE c.embedding IS NOT NULL
    ORDER BY c.embedding <=> %(v)s::vector
    LIMIT %(k)s
    """

    results = []
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        for item, vec in zip(questions, vecs):
            terms = terms_of(item["question"])
            why = ""
            hits: list[dict] = []
            if not in_domain(terms):
                why = "jashtë domenit juridik"
            else:
                lit = "[" + ",".join(f"{x:.6f}" for x in vec.tolist()) + "]"
                cur.execute(sql, {"v": lit, "k": TOP_K})
                rows = cur.fetchall()
                hits = [
                    {"title": r[0], "seq": r[1], "snippet": (r[2] or "")[:280], "sim": float(r[3] or 0)}
                    for r in rows
                ]
                hits = [h for h in hits if h["sim"] >= MIN_SIM]
                if not hits:
                    why = "nën pragun e ngjashmërisë"

            exp = (item.get("expected_doc") or "").lower()
            kw = (item.get("keyword") or "").lower()
            hit = bool(exp) and any(exp in (h["title"] or "").lower() for h in hits)
            kwm = bool(kw) and any(kw in (h["snippet"] or "").lower() for h in hits)
            refused = len(hits) == 0
            ok = refused if not item.get("in_corpus") else (hit or kwm)
            results.append({
                "id": item["id"], "question": item["question"],
                "in_corpus": bool(item.get("in_corpus")), "terms": terms,
                "refused": refused, "why": why, "hits": hits,
                "hit_at_5": hit, "keyword_at_5": kwm, "ok": ok,
            })

    inside = [r for r in results if r["in_corpus"]]
    outside = [r for r in results if not r["in_corpus"]]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": 3, "mode": "vector", "model": model_name,
        "top_k": TOP_K, "min_sim": MIN_SIM,
        "in_corpus": {"count": len(inside), "ok": sum(r["ok"] for r in inside),
                      "hit_at_5": sum(r["hit_at_5"] for r in inside),
                      "keyword_at_5": sum(r["keyword_at_5"] for r in inside)},
        "outside_corpus": {"count": len(outside), "ok": sum(r["ok"] for r in outside),
                           "refused": sum(r["refused"] for r in outside)},
        "results": results,
    }
    path = out_dir / f"harness-v3-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"raport: {path.name}")
    print(f"brenda: {report['in_corpus']['ok']}/{report['in_corpus']['count']} "
          f"(hit@5 {report['in_corpus']['hit_at_5']}, kw@5 {report['in_corpus']['keyword_at_5']})")
    print(f"jashtë: {report['outside_corpus']['ok']}/{report['outside_corpus']['count']} refuzuar")
    for r in results:
        sim = r["hits"][0]["sim"] if r["hits"] else 0.0
        print(("OK   " if r["ok"] else "GABIM"), r["id"], f"hits={len(r['hits'])} sim={sim:.3f}",
              (r["why"] or "")[:26], "|", r["question"][:44])
    return 0


if __name__ == "__main__":
    sys.exit(main())

