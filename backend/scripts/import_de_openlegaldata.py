"""Import German instance-court case law (AG/LG/OLG…) from openlegaldata.io
into the local RAG corpus (jurisdiction DE) — D-059 F2.

Source: the Open Legal Data project (openlegaldata.io) publishes German court
decisions as bulk JSONL dumps (one case per line, CC0/public-domain court
text). Download a dump first, e.g.:

    curl -LO https://static.openlegaldata.io/dumps/de/cases.jsonl.gz

Usage:
    cd backend
    .venv/bin/python scripts/import_de_openlegaldata.py --file cases.jsonl.gz
    .venv/bin/python scripts/import_de_openlegaldata.py --file cases.jsonl.gz --limit 500
    .venv/bin/python scripts/import_de_openlegaldata.py --file cases.jsonl.gz --since 2018-01-01

What gets imported (data-driven filters, see REGISTERS):
- courts of instance (AG, LG, OLG, ArbG, LAG) — the federal courts come from
  rechtsprechung-im-internet with richer XML;
- the practice areas a small office actually litigates: civil (incl. rent &
  traffic damages), family, labor — recognized by the register letter in the
  German Aktenzeichen (e.g. "8 C 123/19": C = AG civil).

Resume-safe like the RII importer: references already in the DB are skipped
(direct DB check via corpus_common) and the DB unique index turns any race
into a 409, which is also treated as a skip.
"""
import asyncio
import gzip
import json
import re
import sys
from datetime import date
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from corpus_common import api_token, existing_references  # noqa: E402

API = "http://127.0.0.1:8000/api"
MIN_CHARS = 600
DOC_DELAY = 0.05  # local file + local API — only pace the embedding work

# Court name must start with one of these (instance courts only — federal
# courts come from rechtsprechung-im-internet).
COURT_PREFIXES = ("AG ", "LG ", "OLG ", "ArbG ", "LAG ", "KG",)

# Aktenzeichen register letters -> practice area we want. German court file
# numbers encode the register: "8 C 123/19" (AG civil), "12 O 45/20" (LG
# civil first instance), "5 S 9/21" (LG civil appeal), "3 F 78/19" (family),
# "2 Ca 150/20" (labor first instance), "4 Sa 33/21" (labor appeal),
# "1 U 12/22" (OLG civil appeal), "7 T 5/20" (LG complaints). Criminal and
# administrative registers are deliberately absent.
REGISTERS: dict[str, str] = {
    "C": "civil", "O": "civil", "S": "civil", "U": "civil", "T": "civil",
    "F": "family", "UF": "family",
    "Ca": "labor", "Sa": "labor", "Ta": "labor",
}
_AZ_RE = re.compile(r"\b\d{1,3}\s+([A-Za-z]{1,3})\s+\d+/\d{2}\b")

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")


def practice_area(file_number: str) -> str | None:
    m = _AZ_RE.search(file_number or "")
    return REGISTERS.get(m.group(1)) if m else None


def html_to_text(html: str) -> str:
    """OLDP content is simple HTML — block tags become line breaks, the rest
    is stripped. Good enough for RAG chunks; no external deps."""
    html = re.sub(r"(?i)</(p|div|h[1-6]|li|tr|dd|dt|blockquote)>", "\n\n", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    text = _TAG_RE.sub(" ", html)
    text = (
        text.replace("&nbsp;", " ").replace("&amp;", "&")
        .replace("&lt;", "<").replace("&gt;", ">")
        .replace("&quot;", '"').replace("&#39;", "'")
    )
    lines = [_WS_RE.sub(" ", ln).strip() for ln in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def parse_case(raw: dict) -> dict | None:
    """OLDP case JSON -> corpus payload dict, or None when filtered out."""
    court = (raw.get("court") or {}).get("name", "").strip()
    file_number = (raw.get("file_number") or "").strip()
    content = raw.get("content") or ""
    when = (raw.get("date") or "").strip()
    if not (court.startswith(COURT_PREFIXES) and file_number and content and when):
        return None
    area = practice_area(file_number)
    if area is None:
        return None
    text = html_to_text(content)
    if len(text) < MIN_CHARS:
        return None

    kind = (raw.get("type") or "Entscheidung").strip()
    nice_date = ".".join(reversed(when.split("-"))) if "-" in when else when
    # Reference must be unique ACROSS courts — many AGs share "3 C 123/20",
    # so the court name is part of it (unlike federal Aktenzeichen).
    reference = f"{court}, {file_number}"
    ecli = (raw.get("ecli") or "").strip()
    return {
        "jurisdiction_code": "DE",
        "title": f"{court}, {kind} vom {nice_date} — {file_number}"[:500],
        "doc_type": "judgment",
        "reference": reference[:255],
        "source_url": f"https://de.openlegaldata.io/case/{raw.get('slug', '')}",
        "language": "de",
        "text": text if not ecli else f"ECLI: {ecli}\n\n{text}",
        "date": when,
        "area": area,
    }


def iter_dump(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip().rstrip(",")
            if not line or line in "[]":
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


async def import_cases(path: Path, limit: int | None, since: date | None) -> None:
    token = await api_token()
    existing = await existing_references("DE")
    stats = {"ok": 0, "skip": 0, "fail": 0, "filtered": 0}
    imported = 0

    async with httpx.AsyncClient(
        timeout=1800, headers={"Authorization": f"Bearer {token}"}
    ) as api:
        for n, raw in enumerate(iter_dump(path), 1):
            parsed = parse_case(raw)
            if parsed is None:
                stats["filtered"] += 1
                continue
            if since and parsed["date"] < since.isoformat():
                stats["filtered"] += 1
                continue
            if parsed["reference"] in existing:
                stats["skip"] += 1
                continue
            payload = {k: v for k, v in parsed.items() if k not in ("date", "area")}
            try:
                resp = await api.post(f"{API}/corpus", json=payload)
                if resp.status_code == 401:  # token expired mid-run — refresh once
                    token = await api_token()
                    api.headers["Authorization"] = f"Bearer {token}"
                    resp = await api.post(f"{API}/corpus", json=payload)
            except httpx.HTTPError as exc:
                await asyncio.sleep(15)
                try:
                    resp = await api.post(f"{API}/corpus", json=payload)
                except httpx.HTTPError:
                    print(f"[line {n}] FAIL {parsed['reference']}: {exc}", flush=True)
                    stats["fail"] += 1
                    continue
            if resp.status_code == 201:
                stats["ok"] += 1
                imported += 1
                existing.add(parsed["reference"])
                print(f"[{imported}] OK   {parsed['title'][:70]} "
                      f"({resp.json()['chunk_count']} chunks, {parsed['area']})",
                      flush=True)
            elif resp.status_code == 409:  # already in DB — resume-safe
                stats["skip"] += 1
                existing.add(parsed["reference"])
            else:
                stats["fail"] += 1
                print(f"[line {n}] ERR  {parsed['reference']} {resp.status_code}: "
                      f"{resp.text[:150]}", flush=True)
            if limit and imported >= limit:
                break
            await asyncio.sleep(DOC_DELAY)

    print(f"\nopenlegaldata: ok={stats['ok']} skip={stats['skip']} "
          f"filtered={stats['filtered']} fail={stats['fail']}")


def _arg(flag: str, default):
    if flag in sys.argv:
        return sys.argv[sys.argv.index(flag) + 1]
    return default


if __name__ == "__main__":
    file_arg = _arg("--file", None)
    if not file_arg:
        sys.exit("Usage: import_de_openlegaldata.py --file cases.jsonl[.gz] "
                 "[--limit N] [--since YYYY-MM-DD]")
    limit_arg = _arg("--limit", None)
    since_arg = _arg("--since", None)
    asyncio.run(import_cases(
        Path(file_arg),
        int(limit_arg) if limit_arg else None,
        date.fromisoformat(since_arg) if since_arg else None,
    ))
