"""Kontrata e korpusit K-a — teste offline, pa DB, pa rrjet.

Kontrollon: manifestin, hash-et, lidhjen vendim-OCDS dhe parakushtin e refuzimit.
Perdorimi:  python3 -m pytest tests -q   ose   python3 tests/test_corpus_contract.py
"""
import gzip
import hashlib
import json
import os
import pathlib

CORPUS = pathlib.Path(os.environ.get("OA_CORPUS", str(pathlib.Path.home() / "oa-korpus" / "k-a")))
MANIFEST = CORPUS / "MANIFEST.json"
JOIN_ID = "622-25-1796-2-2-1"
SECTIONS = ("s2", "s2_text", "s2_2025", "s2_2025_text")


def man() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def all_items(m: dict) -> list:
    items = list(m["elemente"])
    for key in SECTIONS:
        items.extend(m[key]["skedare"])
    return items


def test_manifest_exists():
    assert MANIFEST.exists(), f"mungon {MANIFEST}"
    m = man()
    assert "elemente" in m
    for key in SECTIONS:
        assert key in m, f"seksioni {key} mungon"
        assert "skedare" in m[key], f"{key} nuk ka liste skedare"


def test_counts():
    m = man()
    assert len(m["elemente"]) == 2
    assert len(m["s2"]["skedare"]) == 10
    assert len(m["s2_text"]["skedare"]) == 10
    assert len(m["s2_2025"]["skedare"]) >= 14
    assert len(m["s2_2025_text"]["skedare"]) >= 12


def test_hashes_match():
    checked = 0
    for item in all_items(man()):
        p = CORPUS / item["skedari"]
        assert p.exists(), "mungon " + item["skedari"]
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        assert got == item["sha256"], "hash i ndryshuar: " + item["skedari"]
        checked += 1
    assert checked >= 50, "u kontrolluan vetem %d skedare" % checked


def _ocds_record(key: str):
    for name in ("2025.jsonl.gz", "2026.jsonl.gz"):
        p = CORPUS / name
        if not p.exists():
            continue
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            for line in fh:
                if key in line:
                    return json.loads(line), name
    return None, None


def test_join_decision_to_registry():
    txt = (CORPUS / "s2-2025-text" / "Vendimi_2025-1289.txt").read_text(encoding="utf-8")
    assert JOIN_ID in txt, "vendimi nuk permban numrin e prokurimit"
    rec, _src = _ocds_record(JOIN_ID)
    assert rec is not None, "numri nuk u gjet ne OCDS"
    tender = rec.get("tender", {})
    assert tender.get("id") == JOIN_ID
    assert "Prizrenit" in (tender.get("title") or "")
    assert (tender.get("value") or {}).get("amount") == 80000.0


def test_refusal_precondition():
    bogus = "999-99-999999-9-9-9"
    rec, _src = _ocds_record(bogus)
    assert rec is None, "nje numer i rreme duhet te mos gjendet"


if __name__ == "__main__":
    fails = 0
    for name in sorted(dir()):
        if name.startswith("test_") and callable(globals()[name]):
            try:
                globals()[name]()
                print("PASS", name)
            except AssertionError as e:
                fails += 1
                print("FAIL", name, ":", e)
    print("")
    print("%d deshtime" % fails)
    raise SystemExit(1 if fails else 0)
