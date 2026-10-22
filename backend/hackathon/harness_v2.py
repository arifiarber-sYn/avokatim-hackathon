#!/usr/bin/env python3
"""Harness etalon v2 — kërkim leksikor i përmirësuar + portë refuzimi.

Ndryshimet nga v1:
  * tsquery me OR mbi termat e përmbajtjes (jo vetëm plainto_tsquery)
  * stopwords shqip + terma më të shkurtër se 3 shkronja hiqen
  * prag refuzimi: pa rezultat të fortë -> "s'e di" (në vend të zhurmës)
  * raporton edhe arsyen e refuzimit
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg

DSN = os.environ.get(
    "AVOKATIM_DSN",
    "postgresql://avokatim@127.0.0.1:5433/avokatim"  # pa fjalekalim; vendos AVOKATIM_DSN,
)
TOP_K = 5
MIN_TERMS = 2          # sa terma duhet të përputhen të paktën
MIN_RANK = 0.005       # prag empirik; nën të -> s'e di

STOP = {
    "dhe","të","te","e","i","a","në","ne","me","për","per","nga","se","si","kur","sa",
    "është","eshte","ka","kanë","kane","kush","çfarë","cfare","cila","cilat","cilin",
    "një","nje","që","qe","do","duhet","mund","pas","para","mbi","nën","nen","ose",
    "ky","kjo","këto","keto","këtë","kete","atë","ate","ai","ajo","por","edhe","jo",
    "çfar","cfar","ligji","ligjin","sipas","rregullohen","rregullohet",
}


def terms_of(question: str) -> list[str]:
    words = re.findall(r"[0-9A-Za-zÀ-ÿ]+", question.lower())
    out: list[str] = []
    for w in words:
        if len(w) < 3 or w in STOP:
            continue
        out.append(w)
        # trung i thjeshtë shqip: hiq mbaresat e shpeshta
        for suf in ("ve", "të", "te", "it", "in", "ën", "en", "ës", "es", "sh"):
            if len(w) > 5 and w.endswith(suf):
                out.append(w[: -len(suf)])
                break
    seen, uniq = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq[:8]


SQL = """
WITH q AS (SELECT to_tsquery('simple', %(tsq)s) AS tsq)
SELECT d.title, c.seq, c.text,
       ts_rank_cd(c.tsv, q.tsq, 32) AS rank,
       (SELECT count(*) FROM unnest(%(terms)s::text[]) t
         WHERE c.tsv @@ to_tsquery('simple', t)) AS matched
FROM legal_corpus_chunks c
JOIN legal_corpus_docs d ON d.id = c.doc_id, q
WHERE c.tsv @@ q.tsq
ORDER BY rank DESC, matched DESC
LIMIT %(k)s
"""



LEGAL_HINTS = {
    "ligj","kod","nen","kontrat","martes","trash","pun","pasuri","padi","gjyq","afat",
    "parashkrim","veper","vepër","denim","dënim","paraburgim","konsumator","konkurrenc",
    "shoqeri","shoqëri","detyrim","familj","procedur","penal","civil","administrat","pron",
    "kushtetut","taks","tatim","regjistr","dokument","autoritet","pala","dëm","dem",
    "dhenave","dhënave","personale","privatesi","privatësi","subjekt","mbrojtj","mbrojt",
    "mosha","moshë","moshe","vdekj","vdekje","martes","bashkëshort","bashkeshort",
    "meshkuj","femi","fëmij","fëmijë","prind","birësim","biresim",
}

def in_domain(terms):
    return any(t.startswith(h) or h.startswith(t) for t in terms for h in LEGAL_HINTS)

def search(cur, question: str) -> tuple[list[dict], list[str], str]:
    terms = terms_of(question)
    if not terms:
        return [], terms, "pa terma"
    if not in_domain(terms):
        return [], terms, "jashtë domenit juridik"
    tsq = " | ".join(terms)
    cur.execute(SQL, {"tsq": tsq, "terms": terms, "k": TOP_K})
    rows = cur.fetchall()
    hits = [
        {"title": r[0], "seq": r[1], "snippet": (r[2] or "")[:280],
         "rank": float(r[3] or 0), "matched": int(r[4] or 0)}
        for r in rows
    ]
    if not hits:
        return [], terms, "pa rezultat"
    strong = [h for h in hits if h["matched"] >= MIN_TERMS and h["rank"] >= MIN_RANK]
    if not strong:
        return [], terms, f"i dobët (max rank {hits[0]['rank']:.4f}, matched {hits[0]['matched']})"
    return strong, terms, ""


def main() -> int:
    here = Path(__file__).resolve().parent
    questions = json.loads((here / "questions.json").read_text(encoding="utf-8"))
    out_dir = Path(os.environ.get("HARNESS_OUT", here.parent.parent / "data" / "evidence"))
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        for item in questions:
            hits, terms, why = search(cur, item["question"])
            expected = (item.get("expected_doc") or "").lower()
            keyword = (item.get("keyword") or "").lower()
            hit = bool(expected) and any(expected in (h["title"] or "").lower() for h in hits)
            kw = bool(keyword) and any(keyword in (h["snippet"] or "").lower() for h in hits)
            refused = len(hits) == 0
            ok = refused if not item.get("in_corpus") else (hit or kw)
            results.append({
                "id": item["id"], "question": item["question"],
                "in_corpus": bool(item.get("in_corpus")),
                "terms": terms, "refused": refused, "why": why,
                "hits": hits, "hit_at_5": hit, "keyword_at_5": kw, "ok": ok,
            })

    inside = [r for r in results if r["in_corpus"]]
    outside = [r for r in results if not r["in_corpus"]]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": 2, "top_k": TOP_K, "min_terms": MIN_TERMS, "min_rank": MIN_RANK,
        "total": len(results),
        "in_corpus": {"count": len(inside), "ok": sum(r["ok"] for r in inside),
                      "hit_at_5": sum(r["hit_at_5"] for r in inside),
                      "keyword_at_5": sum(r["keyword_at_5"] for r in inside)},
        "outside_corpus": {"count": len(outside), "ok": sum(r["ok"] for r in outside),
                           "refused": sum(r["refused"] for r in outside)},
        "results": results,
    }
    path = out_dir / f"harness-v2-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"raport: {path.name}")
    print(f"brenda: {report['in_corpus']['ok']}/{report['in_corpus']['count']} ok "
          f"(hit@5 {report['in_corpus']['hit_at_5']}, kw@5 {report['in_corpus']['keyword_at_5']})")
    print(f"jashtë: {report['outside_corpus']['ok']}/{report['outside_corpus']['count']} refuzuar")
    for r in results:
        print(("OK   " if r["ok"] else "GABIM"), r["id"], f"hits={len(r['hits'])}",
              (r["why"] or "")[:32], "|", r["question"][:46])
    return 0


if __name__ == "__main__":
    sys.exit(main())

