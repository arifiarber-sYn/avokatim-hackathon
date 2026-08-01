"""Import German federal case law into the local RAG corpus (jurisdiction DE).

Source: rechtsprechung-im-internet.de — the official BMJV portal for federal
court decisions. Every decision is published as structured XML (leitsatz,
tenor, tatbestand, gruende…), public domain (§ 5 UrhG), with a machine
readable index at rii-toc.xml (~23 MB, one <item> per decision).

Usage:
    cd backend
    .venv/bin/python scripts/import_de_rechtsprechung.py                 # BGH+BAG+BVerfG, last 5 years
    .venv/bin/python scripts/import_de_rechtsprechung.py --limit 200     # newest 200 only
    .venv/bin/python scripts/import_de_rechtsprechung.py --courts BGH --years 2

Resumable like the laws importer: decisions whose reference (Aktenzeichen)
is already in the DE corpus are skipped. Import goes through the local
corpus API so chunking (Leitsatz/Tenor/Gründe-aware splitter), tsvector and
local embeddings happen exactly like every other corpus document.
"""
import asyncio
import io
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, timedelta
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.security import create_access_token  # noqa: E402

API = "http://127.0.0.1:8000/api"
RII = "https://www.rechtsprechung-im-internet.de"
TOC_URL = f"{RII}/rii-toc.xml"
DOC_DELAY = 0.3
MIN_CHARS = 400

# Court name in <gericht> starts with one of these codes.
DEFAULT_COURTS = ["BGH", "BAG", "BVerfG"]
DEFAULT_YEARS = 5

# XML content sections, in citation-friendly reading order. The corpus
# splitter recognises these exact heading lines and chunks by them.
_SECTIONS = [
    ("titelzeile", None),
    ("leitsatz", "Leitsatz"),
    ("sonstosatz", "Orientierungssatz"),
    ("tenor", "Tenor"),
    ("tatbestand", "Tatbestand"),
    ("entscheidungsgruende", "Entscheidungsgründe"),
    ("gruende", "Gründe"),
    ("abwmeinung", "Abweichende Meinung"),
]

_DOKTYP_LABEL = {"urteil": "Urteil", "beschluss": "Beschluss"}


async def _api_token() -> str:
    async with SessionLocal() as db:
        owner = (
            await db.execute(select(User).where(User.role == "admin").limit(1))
        ).scalars().first()
        return create_access_token(str(owner.id), str(owner.tenant_id))


def load_toc(path: Path, courts: list[str], since: date) -> list[dict]:
    """Newest-first list of {court, date, az, url} filtered by court + date."""
    wanted = tuple(courts)
    items: list[dict] = []
    for _, el in ET.iterparse(str(path), events=("end",)):
        if el.tag != "item":
            continue
        gericht = (el.findtext("gericht") or "").strip()
        datum = (el.findtext("entsch-datum") or "").strip()
        az = (el.findtext("aktenzeichen") or "").strip()
        link = (el.findtext("link") or "").strip()
        el.clear()
        if not (gericht.startswith(wanted) and datum and az and link):
            continue
        try:
            d = date(int(datum[:4]), int(datum[4:6]), int(datum[6:8]))
        except ValueError:
            continue
        if d < since:
            continue
        items.append({
            "court": gericht.split()[0],  # "BGH 9. Zivilsenat" -> "BGH"
            "senate": gericht,
            "date": d,
            "az": az,
            "url": link.replace("http://", "https://"),
        })
    items.sort(key=lambda i: i["date"], reverse=True)
    return items


def _section_text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    parts: list[str] = []
    # Content is nested HTML-ish (<div><dl><dd><p>…). Collect leaf paragraph
    # nodes only, so nested containers don't duplicate their children's text.
    for node in el.iter():
        if node.tag == "p":
            t = " ".join("".join(node.itertext()).split())
            if t:
                parts.append(t)
        elif node.tag in {"dt", "dd"} and node.find(".//p") is None:
            t = " ".join("".join(node.itertext()).split())
            if t:
                parts.append(t)
    if not parts:
        t = " ".join("".join(el.itertext()).split())
        if t:
            parts = [t]
    return "\n".join(parts)


def parse_rii_xml(data: bytes) -> dict:
    """Extract metadata + citation-ready plain text from a decision zip."""
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        xml_name = next(n for n in zf.namelist() if n.endswith(".xml"))
        root = ET.fromstring(zf.read(xml_name))

    ecli = (root.findtext("ecli") or "").strip()
    gertyp = (root.findtext("gertyp") or "").strip()
    datum = (root.findtext("entsch-datum") or "").strip()
    az = (root.findtext("aktenzeichen") or "").strip()
    doktyp = _DOKTYP_LABEL.get(
        (root.findtext("doktyp") or "").strip().lower(),
        (root.findtext("doktyp") or "Entscheidung").strip(),
    )
    normen = " ".join((root.findtext("norm") or "").split())

    nice_date = f"{datum[6:8]}.{datum[4:6]}.{datum[:4]}" if len(datum) == 8 else datum
    title = f"{gertyp}, {doktyp} vom {nice_date} — {az}"

    blocks: list[str] = []
    if normen:
        blocks.append(f"Normen: {normen}")
    for tag, heading in _SECTIONS:
        body = _section_text(root.find(tag))
        if not body:
            continue
        blocks.append(f"{heading}\n{body}" if heading else body)
    text = re.sub(r"\n{3,}", "\n\n", "\n\n".join(blocks)).strip()

    return {"title": title, "reference": az, "ecli": ecli, "text": text}


async def import_decisions(courts: list[str], years: int, limit: int | None) -> None:
    since = date.today() - timedelta(days=365 * years)
    token = await _api_token()
    stats = {"ok": 0, "skip": 0, "fail": 0}

    async with httpx.AsyncClient(
        timeout=300, headers={"User-Agent": "AvokatIM corpus sync (contact: info@avokatiim.ai)"},
        follow_redirects=True,
    ) as web, httpx.AsyncClient(
        timeout=1800, headers={"Authorization": f"Bearer {token}"}
    ) as api:
        toc_path = Path("/tmp/rii-toc.xml")
        if not toc_path.exists():
            print("downloading rii-toc.xml …", flush=True)
            r = await web.get(TOC_URL)
            r.raise_for_status()
            toc_path.write_bytes(r.content)
        items = load_toc(toc_path, courts, since)
        print(f"rii-toc: {len(items)} decisions match "
              f"({'+'.join(courts)}, since {since})", flush=True)
        if limit:
            items = items[:limit]

        existing = {
            d.get("reference")
            for d in (await api.get(f"{API}/corpus?jurisdiction_code=DE")).json()
        }

        total = len(items)
        for i, item in enumerate(items, 1):
            if item["az"] in existing:
                stats["skip"] += 1
                continue
            try:
                r = await web.get(item["url"])
                r.raise_for_status()
                parsed = parse_rii_xml(r.content)
            except Exception as exc:  # noqa: BLE001 — log and continue the batch
                print(f"[{i}/{total}] FAIL {item['az']}: {exc}", flush=True)
                stats["fail"] += 1
                continue
            if len(parsed["text"]) < MIN_CHARS:
                stats["skip"] += 1
                existing.add(item["az"])
                continue

            payload = {
                "jurisdiction_code": "DE",
                "title": parsed["title"][:500],
                "doc_type": "judgment",
                "reference": (parsed["reference"] or parsed["ecli"])[:255],
                "source_url": item["url"],
                "language": "de",
                "text": parsed["text"],
            }
            try:
                resp = await api.post(f"{API}/corpus", json=payload)
                if resp.status_code == 401:  # token expired mid-run — refresh once
                    token = await _api_token()
                    api.headers["Authorization"] = f"Bearer {token}"
                    resp = await api.post(f"{API}/corpus", json=payload)
            except httpx.HTTPError as exc:
                # Backend briefly down (restart/deploy) — wait and retry once,
                # then log and move on; a future run picks the decision up.
                await asyncio.sleep(15)
                try:
                    resp = await api.post(f"{API}/corpus", json=payload)
                except httpx.HTTPError:
                    print(f"[{i}/{total}] FAIL {item['az']}: {exc}", flush=True)
                    stats["fail"] += 1
                    continue
            if resp.status_code == 201:
                stats["ok"] += 1
                existing.add(item["az"])
                print(f"[{i}/{total}] OK   {parsed['title'][:70]} "
                      f"({resp.json()['chunk_count']} chunks)", flush=True)
            else:
                stats["fail"] += 1
                print(f"[{i}/{total}] ERR  {item['az']} {resp.status_code}: "
                      f"{resp.text[:150]}", flush=True)
            await asyncio.sleep(DOC_DELAY)

    print(f"\nDE case law: ok={stats['ok']} skip={stats['skip']} fail={stats['fail']}")


def _arg(flag: str, default):
    if flag in sys.argv:
        return sys.argv[sys.argv.index(flag) + 1]
    return default


if __name__ == "__main__":
    courts_arg = _arg("--courts", ",".join(DEFAULT_COURTS))
    years_arg = int(_arg("--years", DEFAULT_YEARS))
    limit_arg = _arg("--limit", None)
    asyncio.run(import_decisions(
        [c.strip() for c in str(courts_arg).split(",") if c.strip()],
        years_arg,
        int(limit_arg) if limit_arg else None,
    ))
