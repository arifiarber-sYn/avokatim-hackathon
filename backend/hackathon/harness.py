#!/usr/bin/env python3
"""Harness etalon — 20 pyetje mbi korpusin ligjor të AvokatIM.

Qëllimi: matje e përsëritshme përpara çdo ndryshimi (bazë), jo marketing.
Metrika:
  hit@5        dokumenti i pritur ndodhet në 5 rezultatet e para
  keyword@5    fragmenti përmban fjalën kyçe
  refuzim      pyetje jashtë korpusit -> asnjë rezultat i fortë ("s'e di")
Dalja: JSON + tabelë në stdout. Kthen rc=0 vetëm kur të gjitha pyetjet ekzekutohen.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg

DSN = os.environ.get(
    "AVOKATIM_DSN",
    "postgresql://avokatim@127.0.0.1:5433/avokatim"  # pa fjalekalim; vendos AVOKATIM_DSN,
)
TOP_K = 5

SQL_FTS = """
SELECT d.title, c.seq, c.text,
       ts_rank(c.tsv, plainto_tsquery('simple', %(q)s)) AS rank
FROM legal_corpus_chunks c
JOIN legal_corpus_docs d ON d.id = c.doc_id
WHERE c.tsv @@ plainto_tsquery('simple', %(q)s)
ORDER BY rank DESC
LIMIT %(k)s
"""

SQL_LIKE = """
SELECT d.title, c.seq, c.text, 0.0 AS rank
FROM legal_corpus_chunks c
JOIN legal_corpus_docs d ON d.id = c.doc_id
WHERE c.text ILIKE %(pat)s
LIMIT %(k)s
"""


def search(cur, question: str) -> list[dict]:
    cur.execute(SQL_FTS, {"q": question, "k": TOP_K})
    rows = cur.fetchall()
    if not rows:
        token = max(question.split(), key=len)
        cur.execute(SQL_LIKE, {"pat": f"%{token}%", "k": TOP_K})
        rows = cur.fetchall()
    return [
        {"title": r[0], "seq": r[1], "snippet": (r[2] or "")[:280], "rank": float(r[3] or 0)}
        for r in rows
    ]


def main() -> int:
    here = Path(__file__).resolve().parent
    questions = json.loads((here / "questions.json").read_text(encoding="utf-8"))
    out_dir = Path(os.environ.get("HARNESS_OUT", here.parent.parent / "data" / "evidence"))
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        for item in questions:
            hits = search(cur, item["question"])
            expected = (item.get("expected_doc") or "").lower()
            keyword = (item.get("keyword") or "").lower()
            hit = bool(expected) and any(expected in (h["title"] or "").lower() for h in hits)
            kw = bool(keyword) and any(keyword in (h["snippet"] or "").lower() for h in hits)
            refused = len(hits) == 0
            ok = refused if not item.get("in_corpus") else (hit or kw)
            results.append(
                {
                    "id": item["id"],
                    "question": item["question"],
                    "in_corpus": bool(item.get("in_corpus")),
                    "hits": hits,
                    "hit_at_5": hit,
                    "keyword_at_5": kw,
                    "refused": refused,
                    "ok": ok,
                }
            )

    inside = [r for r in results if r["in_corpus"]]
    outside = [r for r in results if not r["in_corpus"]]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top_k": TOP_K,
        "total": len(results),
        "in_corpus": {
            "count": len(inside),
            "hit_at_5": sum(r["hit_at_5"] for r in inside),
            "keyword_at_5": sum(r["keyword_at_5"] for r in inside),
            "ok": sum(r["ok"] for r in inside),
        },
        "outside_corpus": {
            "count": len(outside),
            "refused": sum(r["refused"] for r in outside),
            "ok": sum(r["ok"] for r in outside),
        },
        "results": results,
    }
    path = out_dir / f"harness-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"raport: {path}")
    print(f"brenda korpusit: {report['in_corpus']['ok']}/{report['in_corpus']['count']} ok "
          f"(hit@5 {report['in_corpus']['hit_at_5']}, keyword@5 {report['in_corpus']['keyword_at_5']})")
    print(f"jashtë korpusit: {report['outside_corpus']['ok']}/{report['outside_corpus']['count']} refuzuar saktë")
    for r in results:
        mark = "OK " if r["ok"] else "GABIM"
        print(f"{mark} {r['id']} {r['question'][:58]:<58} hits={len(r['hits'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

