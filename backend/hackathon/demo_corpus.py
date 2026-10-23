#!/usr/bin/env python3
"""Demo offline mbi korpusin K-a: pyetje -> deshmi -> pergjigje me citime (ose "s'e di").

Pa DB, pa LLM, pa rrjet. Burimet:
  1) vendimet e Panelit  s2-2025-text/Vendimi*.txt
  2) regjistri OCDS       2025.jsonl.gz / 2026.jsonl.gz
  3) ligji 04/L-042       nenet e cituara ne vetë vendim

Perdorimi:
    python hackathon/demo_corpus.py "Kush u ankua per dezinsektimin e Prizrenit?"
    python hackathon/demo_corpus.py --refuse "Sa kushton qiraja ne Berlin?"
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import pathlib
import re
import sys

CORPUS = pathlib.Path(os.environ.get("OA_CORPUS", str(pathlib.Path.home() / "oa-korpus" / "k-a")))
STOP = set("dhe te e i a ne me per nga se si kur sa cfare eshte kush cilat ku ka kane nuk po mos u kete atij asaj cka".split())
PROC = re.compile(r"\b\d{2,4}-[A-Za-z]{0,6}-?\d{2}-\d{3,6}-\d-\d-\d\b")
HEADER = ("organi shqyrtues", "tel:", "rruga migjeni", "republic of kosovo", "telo za")
MIN_SCORE = 1.2


def stem(w: str) -> str:
    w = w.lower()
    return w[:6] if len(w) >= 6 else w


def terms(text: str) -> list:
    return [stem(w) for w in re.findall(r"[A-Za-zÇËçë0-9]+", text)
            if len(w) > 2 and w.lower() not in STOP]


def load_decisions() -> list:
    d = CORPUS / "s2-2025-text"
    out, seen = [], {}
    for f in sorted(d.glob("Vendimi*.txt")):
        text = f.read_text(encoding="utf-8", errors="replace")
        h = hashlib.md5(text.encode()).hexdigest()[:10]
        if h in seen:
            # i njejti dokument me emer tjeter: mbaj emrin qe perputhet me numrin OSHP ne tekst
            m = re.search(r"OSHP:\s*\d{4}/(\d+)", text)
            want = m.group(1) if m else ""
            cur = seen[h][0]
            if want and want in f.name and want not in cur:
                for i, (of, ot) in enumerate(out):
                    if of.name == cur:
                        out[i] = (f, text)
                        seen[h][0] = f.name
                        break
            continue
        seen[h] = [f.name]
        out.append((f, text))
    return out


def build_idf(docs: list) -> dict:
    df = {}
    for _f, text in docs:
        for t in set(terms(text)):
            df[t] = df.get(t, 0) + 1
    n = max(len(docs), 1)
    return {t: math.log(1 + (n + 1) / (c + 0.5)) for t, c in df.items()}


def rank(q: set, docs: list, idf: dict) -> list:
    out = []
    for f, text in docs:
        inter = q & set(terms(text))
        s = sum(idf.get(t, 0.0) for t in inter) / (len(q) ** 0.5)
        out.append((s, f, text))
    return sorted(out, reverse=True)


def pick_sentence(text: str, q: set, idf: dict) -> str:
    best, score = "", 0.0
    for s in re.split(r"(?<=[.!?])\s+|\n{2,}", text):
        low = s.lower().strip()
        if not low or any(h in low for h in HEADER):
            continue
        st = set(terms(s))
        hit = q & st
        if not hit:
            continue
        sc = sum(idf.get(t, 0.0) for t in hit)
        if sc > score:
            best, score = s, sc
    return " ".join(best.split())[:340]


def ocds_lookup(pid: str):
    for name in ("2025.jsonl.gz", "2026.jsonl.gz"):
        p = CORPUS / name
        if not p.exists():
            continue
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            for line in fh:
                if pid in line:
                    return json.loads(line), name
    return None, None


def find_proc(text: str, sentence: str):
    idx = text.find(sentence[:50]) if sentence else -1
    if idx >= 0:
        m = PROC.search(text[max(0, idx - 700): idx + 1100])
        if m:
            return m.group(0)
    m = PROC.search(text)
    return m.group(0) if m else None


def answer(query: str) -> dict:
    docs = load_decisions()
    q = set(terms(query))
    idf = build_idf(docs)
    ranked = rank(q, docs, idf)
    if not ranked or ranked[0][0] < MIN_SCORE:
        return {"ok": False, "reason": "asnje vendim nuk mbulon pyetjen", "searched": len(docs)}
    sc, f, text = ranked[0]
    citat = pick_sentence(text, q, idf)
    if not citat:
        return {"ok": False, "reason": "perputhje vetem ne krye te dokumentit", "searched": len(docs)}
    PAT = r"nenit?\s+(\d{1,3}(?:\s*,\s*(?:dhe\s+)?\d{1,3})*)"
    def _arts(src):
        out = set()
        for grp in re.findall(PAT, src):
            for num in re.findall(r"\d{1,3}", grp):
                out.add(int(num))
        return sorted(out)
    arts = _arts(citat) or _arts(text)[:8]
    pid = find_proc(text, citat)
    rec, src = ocds_lookup(pid) if pid else (None, None)
    tender = (rec or {}).get("tender", {})
    return {
        "ok": True, "sku": round(sc, 2), "skedari": str(f.relative_to(CORPUS)), "citat": citat,
        "numer": pid, "regjistri": (rec or {}).get("ocid"), "titull": tender.get("title"),
        "vlera": (tender.get("value") or {}).get("amount"),
        "monedha": (tender.get("value") or {}).get("currency"),
        "nene": arts[:8],
        "burimi_ocds": src, "konkurrues": len(docs),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--refuse", metavar="PYETJA")
    a = ap.parse_args()
    query = a.refuse or a.query
    if not query:
        ap.print_help()
        return 2
    r = answer(query)
    print("PYETJA:", query)
    print()
    if not r["ok"]:
        print("PERGJIGJA: s'e di —", r["reason"] + ".", "(kontrollova %d dokumente)" % r["searched"])
        return 0
    print("BURIMI 1 (vendim):", r["skedari"], " [pike %.2f]" % r["sku"])
    print("  citat:", r["citat"])
    if r["numer"]:
        print("BURIMI 2 (regjister):", r["regjistri"] or "(i pagjetur)")
        print("  tender:", r["numer"], "|", (r["titull"] or "")[:70])
        if r["vlera"]:
            print("  vlera:", r["vlera"], r["monedha"], "| burimi:", r["burimi_ocds"])
    print("BURIMI 3 (ligj): neni", ", ".join(str(x) for x in r["nene"]) or "-", "(LPP 04/L-042)")
    print()
    print("PERGJIGJA: bazuar ne", r["skedari"].split("/")[-1], "- citati eshte teksti i vendimit;",
          "numri i njejte lidh regjistrin dhe nenet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
