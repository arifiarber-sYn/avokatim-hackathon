#!/usr/bin/env python3
"""Sweep pragjesh: mblidh rezultatet një herë, vlerëso konfigurime offline."""
from __future__ import annotations
import json, os, re, sys
from pathlib import Path
import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_v2 import terms_of, SQL, DSN

TOP = 10

def collect(cur, question):
    terms = terms_of(question)
    if not terms:
        return [], terms
    cur.execute(SQL.replace("LIMIT %(k)s", "LIMIT %(k)s"), {"tsq": " | ".join(terms), "terms": terms, "k": TOP})
    return [{"title": r[0], "snippet": (r[2] or "")[:280], "rank": float(r[3] or 0), "matched": int(r[4] or 0)} for r in cur.fetchall()], terms

def score(rows, item, min_terms, min_rank):
    strong = [h for h in rows if h["matched"] >= min_terms and h["rank"] >= min_rank]
    if not item["in_corpus"]:
        return len(strong) == 0
    exp = (item.get("expected_doc") or "").lower(); kw = (item.get("keyword") or "").lower()
    if not strong: return False
    return bool(exp) and any(exp in h["title"].lower() for h in strong[:5]) or (bool(kw) and any(kw in h["snippet"].lower() for h in strong[:5]))

def main():
    qs = json.loads((Path(__file__).resolve().parent / "questions.json").read_text(encoding="utf-8"))
    data = []
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        for it in qs:
            rows, terms = collect(cur, it["question"])
            data.append((it, rows, terms))
    best = None
    for mt in (1, 2, 3):
        for mr in (0.0, 0.005, 0.02, 0.05, 0.1, 0.2, 0.3):
            inside = sum(score(r, it, mt, mr) for it, r, _ in data if it["in_corpus"])
            outside = sum(score(r, it, mt, mr) for it, r, _ in data if not it["in_corpus"])
            total = inside + outside
            key = (total, inside, outside)
            if best is None or key > best[0]:
                best = (key, mt, mr, inside, outside)
    print("me e mira: total=%d (brenda %d/15, jashte %d/5) min_terms=%d min_rank=%.3f" % (best[0][0], best[3], best[4], best[1], best[2]))
    for mt, mr in [(2,0.005),(2,0.05),(3,0.005),(2,0.02)]:
        i = sum(score(r, it, mt, mr) for it, r, _ in data if it["in_corpus"])
        o = sum(score(r, it, mt, mr) for it, r, _ in data if not it["in_corpus"])
        print(f"  mt={mt} mr={mr}: brenda {i}/15 jashte {o}/5")

if __name__ == "__main__":
    main()

