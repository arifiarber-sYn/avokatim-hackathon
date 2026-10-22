#!/usr/bin/env python3
"""Harness v4 — vektor + filtër gjuhe + portë e rreptë domeni.

Ndryshimi kyç ndaj v3: korpusi ka 16 906 dokumente gjermane dhe 3 086 shqipe, dhe
kërkimi vektor pa filtër tërhiqte BGH/Arbeitsgerichtsgesetz për pyetje shqipe.
Tani, kur pyetja është shqipe, kërkohet vetëm brenda dokumenteve shqipe.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_v2 import DSN, terms_of

TOP_K = 5
MIN_SIM = 0.42

STRONG_HINTS = {
    "ligj", "kod", "nen", "kontrat", "martes", "trash", "padi", "gjyq", "afat",
    "parashkrim", "veper", "vepër", "denim", "dënim", "paraburgim", "konsumator",
    "konkurrenc", "shoqeri", "shoqëri", "detyrim", "familj", "procedur", "penal",
    "pron", "kushtetut", "tatim", "pun", "dhenave", "dhënave", "personale", "subjekt",
    "pasuri", "bashkeshort", "bashkëshort", "ndarje", "vdekj", "vdekje", "trash",
    "hetim", "ankes", "shitës", "shtes", "pushim", "fëmij", "kontrollues", "mashtrim", "reklam", "shoqër",
}
SQ_MARKERS = set("ëçËÇ")


def is_albanian(text: str) -> bool:
    if any(ch in SQ_MARKERS for ch in text):
        return True
    low = text.lower().split()
    return any(w in {"sa", "kush", "cfare", "çfarë", "cila", "cilat", "kur", "si", "eshte", "është"} for w in low)


def in_domain(terms: list[str]) -> bool:
    return any(t.startswith(h) or h.startswith(t) for t in terms for h in STRONG_HINTS)


def main() -> int:
    from sentence_transformers import SentenceTransformer

    here = Path(__file__).resolve().parent
    questions = json.loads((here / "questions.json").read_text(encoding="utf-8"))
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
                cur.execute(sql, {"v": lit, "k": TOP_K, "lang": lang})
                hits = [
                    {"title": r[0], "seq": r[1], "snippet": (r[2] or "")[:280], "sim": float(r[3] or 0)}
                    for r in cur.fetchall()
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
            results.append({"id": item["id"], "question": item["question"],
                            "in_corpus": bool(item.get("in_corpus")), "terms": terms,
                            "refused": refused, "why": why, "hits": hits,
                            "hit_at_5": hit, "keyword_at_5": kwm, "ok": ok})

    inside = [r for r in results if r["in_corpus"]]
    outside = [r for r in results if not r["in_corpus"]]
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "version": 4,
              "mode": "vector+lang", "top_k": TOP_K, "min_sim": MIN_SIM,
              "in_corpus": {"count": len(inside), "ok": sum(r["ok"] for r in inside),
                            "hit_at_5": sum(r["hit_at_5"] for r in inside),
                            "keyword_at_5": sum(r["keyword_at_5"] for r in inside)},
              "outside_corpus": {"count": len(outside), "ok": sum(r["ok"] for r in outside),
                                 "refused": sum(r["refused"] for r in outside)},
              "results": results}
    path = out_dir / f"harness-v4-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"raport: {path.name}")
    print(f"brenda: {report['in_corpus']['ok']}/{report['in_corpus']['count']} "
          f"(hit@5 {report['in_corpus']['hit_at_5']}, kw@5 {report['in_corpus']['keyword_at_5']})")
    print(f"jashtë: {report['outside_corpus']['ok']}/{report['outside_corpus']['count']} refuzuar")
    for r in results:
        sim = r["hits"][0]["sim"] if r["hits"] else 0.0
        print(("OK   " if r["ok"] else "GABIM"), r["id"], f"hits={len(r['hits'])} sim={sim:.3f}",
              (r["why"] or "")[:24], "|", r["question"][:42])
    return 0


if __name__ == "__main__":
    sys.exit(main())

