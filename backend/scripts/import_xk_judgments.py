"""Import published Kosovo judgments into the local RAG corpus (jurisdiction XK).

Source: gjyqesori-rks.org/aktgjykimet/ — the KGJK publication portal for
court decisions (290k+ published). The listing is a plain server-rendered
WordPress page that accepts stateless GET filters:

    ?r=M&courtId=<id>&judgeStatus=1&ordBy=v.publicationDtTm&ordDir=DESC&offset=<n>

20 rows per page, newest publication first. Each row carries the case type,
case number, decision + publication dates, judge, court and a direct PDF
link under /wp-content/uploads/verdicts/ (native-text PDFs, Albanian _SQ).

Usage:
    cd backend
    .venv/bin/python scripts/import_xk_judgments.py                    # Supreme, last 5 years
    .venv/bin/python scripts/import_xk_judgments.py --limit 300        # newest 300 only
    .venv/bin/python scripts/import_xk_judgments.py --courts supreme,apeli --years 3

Resumable twice over: PDF URLs already processed are recorded in
data/xk_judgments_state.txt (never re-downloaded), and judgments whose
reference (case number) is already in the XK corpus are skipped. Import goes
through the local corpus API so chunking, tsvector and local embeddings
happen exactly like every other corpus document. Scanned PDFs (no
extractable text) are skipped and counted — no OCR here, the citable value
is in the text-native majority.
"""
import asyncio
import io
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.security import create_access_token  # noqa: E402

API = "http://127.0.0.1:8000/api"
PORTAL = "https://www.gjyqesori-rks.org"
LIST_PATH = "/aktgjykimet/"
PAGE_SIZE = 20
# The portal sits behind Cloudflare and rate-limits bursts hard (429 after
# ~15 quick requests, then 503s). Slow steady pace + backoff keeps it happy.
DOC_DELAY = 2.5
BACKOFF_BASE = 60.0
MAX_RETRIES = 4
MIN_CHARS = 400

# courtId values from the portal's search form (2026-08).
COURTS = {
    "supreme": (12, "Gjykata Supreme"),
    "apeli": (14, "Gjykata e Apelit"),
    "komerciale": (40, "Gjykata Komerciale"),
    "prishtine": (5, "Gjykata Themelore Prishtinë"),
    "mitrovice": (6, "Gjykata Themelore Mitrovicë"),
    "peje": (7, "Gjykata Themelore Pejë"),
    "prizren": (8, "Gjykata Themelore Prizren"),
    "ferizaj": (9, "Gjykata Themelore Ferizaj"),
    "gjilan": (10, "Gjykata Themelore Gjilan"),
    "gjakove": (11, "Gjykata Themelore Gjakovë"),
}
DEFAULT_COURTS = ["supreme"]
DEFAULT_YEARS = 5

# One result row: type cell (title attr = human label, body = code), case
# number, decision date, publication date, judge, court, judge status, then
# the language links to the PDFs.
_ROW_RE = re.compile(
    r"<td class=\"cntrTxt\" title=\"(?P<type_label>[^\"]*)\">(?P<type_code>[^<]*)</td>\s*"
    r"<td>(?P<case_no>[^<]*)</td>\s*"
    r"<td>(?P<decided>[^<]*)</td>\s*"
    r"<td>(?P<published>[^<]*)</td>\s*"
    r"<td>(?P<judge>[^<]*)</td>\s*"
    r"<td>(?P<court>[^<]*)</td>\s*"
    r"<td>[^<]*</td>\s*"
    r"<td[^>]*>(?P<links>.*?)</td>",
    re.S,
)
# Albanian PDF only (_SQ); some rows publish only the Serbian version — those
# are skipped so the corpus language stays consistent with the "sq" search.
_PDF_RE = re.compile(r'href="[^"]*?(/wp-content/uploads/verdicts/[^"]+_SQ\.pdf)"')
# Official case designation as printed in the judgment ("PPP.nr.59/2025",
# "Rev.nr. 123/2020", "PML.nr.242/2025"...) — the citable reference.
_CASENO_RE = re.compile(r"\b([A-ZÇË][A-Za-zçë]{0,10}\.\s?nr\.?\s?\d+[-/]\d{2,4})", re.U)


def _parse_date(s: str) -> date | None:
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s.strip())
    return date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None


def parse_listing(html: str) -> tuple[list[dict], int]:
    """(rows, total) from one listing page. Rows without an SQ PDF are dropped."""
    total_m = re.search(r'displaying-num">\s*(\d+)', html)
    total = int(total_m.group(1)) if total_m else 0
    rows: list[dict] = []
    for m in _ROW_RE.finditer(html):
        pdf_m = _PDF_RE.search(m.group("links"))
        if not pdf_m:
            continue
        rows.append({
            "type_label": m.group("type_label").strip(),
            "type_code": m.group("type_code").strip(),
            "case_no": " ".join(m.group("case_no").split()),
            "decided": _parse_date(m.group("decided")),
            "published": _parse_date(m.group("published")),
            "judge": m.group("judge").strip(),
            "court": m.group("court").strip(),
            "pdf_url": PORTAL + pdf_m.group(1),
        })
    return rows, total


def extract_pdf_text(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    text = "\n\n".join((page.extract_text() or "") for page in reader.pages)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def build_reference(row: dict, pdf_text: str) -> str:
    """Prefer the official designation printed in the judgment itself
    ("Rev.nr. 123/2020"); fall back to portal type code + row number."""
    m = _CASENO_RE.search(pdf_text[:2000])
    if m:
        return " ".join(m.group(1).replace(" ", " ").split())
    case_no = row["case_no"]
    if re.search(r"[A-Za-z]", case_no):  # already carries its prefix
        return case_no
    return f"{row['type_code']}.nr. {case_no}"


def build_title(row: dict, reference: str) -> str:
    nice_date = row["decided"].strftime("%d.%m.%Y") if row["decided"] else ""
    label = row["type_label"] or "Vendim"
    return f"{row['court']}, {label} — {reference}" + (f", {nice_date}" if nice_date else "")


async def _get_with_backoff(client: httpx.AsyncClient, url: str) -> httpx.Response:
    """GET that survives Cloudflare rate limiting: on 429/503 sleep and retry."""
    for attempt in range(1, MAX_RETRIES + 1):
        resp = await client.get(url)
        if resp.status_code not in (429, 503):
            resp.raise_for_status()
            return resp
        if attempt == MAX_RETRIES:
            resp.raise_for_status()
        wait = BACKOFF_BASE * attempt
        print(f"rate-limited ({resp.status_code}) — waiting {wait:.0f}s", flush=True)
        await asyncio.sleep(wait)
    raise AssertionError("unreachable")


async def _api_token() -> str:
    async with SessionLocal() as db:
        owner = (
            await db.execute(select(User).where(User.role == "admin").limit(1))
        ).scalars().first()
        return create_access_token(str(owner.id), str(owner.tenant_id))


# Durable resume state: PDF URLs already processed (imported OR skipped as
# scanned/duplicate), one per line. Lives in data/ (git-ignored, survives
# restarts) so a resumed run never re-downloads what it already handled.
STATE_FILE = Path(__file__).resolve().parents[2] / "data" / "xk_judgments_state.txt"


def _load_state() -> set[str]:
    if STATE_FILE.exists():
        return {line.strip() for line in STATE_FILE.read_text().splitlines() if line.strip()}
    return set()


def _mark_done(url: str) -> None:
    with STATE_FILE.open("a") as fh:
        fh.write(url + "\n")


async def import_judgments(courts: list[str], years: int, limit: int | None) -> None:
    since = date.today() - timedelta(days=365 * years)
    token = await _api_token()
    stats = {"ok": 0, "skip": 0, "scan": 0, "fail": 0}
    imported = 0
    done_urls = _load_state()

    async with httpx.AsyncClient(
        timeout=120,
        headers={"User-Agent": "AvokatIM corpus sync (contact: info@avokatiim.ai)"},
        follow_redirects=True,
    ) as web, httpx.AsyncClient(
        timeout=1800, headers={"Authorization": f"Bearer {token}"}
    ) as api:
        existing = {
            d.get("reference")
            for d in (await api.get(f"{API}/corpus?jurisdiction_code=XK")).json()
            if d.get("doc_type") == "judgment"
        }
        print(f"XK corpus already holds {len(existing)} judgments", flush=True)

        for court_key in courts:
            court_id, court_name = COURTS[court_key]
            offset = 0
            total = None
            while True:
                if limit and imported >= limit:
                    break
                url = (
                    f"{PORTAL}{LIST_PATH}?r=M&courtId={court_id}&judgeStatus=1"
                    f"&ordBy=v.publicationDtTm&ordDir=DESC&offset={offset}"
                )
                try:
                    page = await _get_with_backoff(web, url)
                except httpx.HTTPError as exc:
                    print(f"listing FAIL {court_key} offset={offset}: {exc}", flush=True)
                    break
                rows, page_total = parse_listing(page.text)
                if total is None:
                    total = page_total
                    print(f"{court_name}: {total} published decisions", flush=True)
                if not rows:
                    break
                # Ordered by publication DESC: stop once the page is past `since`.
                if all(r["published"] and r["published"] < since for r in rows):
                    break

                for row in rows:
                    if limit and imported >= limit:
                        break
                    if row["published"] and row["published"] < since:
                        continue
                    if row["pdf_url"] in done_urls:
                        stats["skip"] += 1
                        continue
                    try:
                        pdf = await _get_with_backoff(web, row["pdf_url"])
                        text = extract_pdf_text(pdf.content)
                    except Exception as exc:  # noqa: BLE001 — log, continue batch
                        print(f"FAIL {row['case_no']}: {exc}", flush=True)
                        stats["fail"] += 1
                        continue
                    if len(text) < MIN_CHARS:
                        stats["scan"] += 1
                        _mark_done(row["pdf_url"])
                        done_urls.add(row["pdf_url"])
                        continue
                    reference = build_reference(row, text)[:255]
                    if reference in existing:
                        stats["skip"] += 1
                        _mark_done(row["pdf_url"])
                        done_urls.add(row["pdf_url"])
                        continue

                    payload = {
                        "jurisdiction_code": "XK",
                        "title": build_title(row, reference)[:500],
                        "doc_type": "judgment",
                        "reference": reference,
                        "source_url": row["pdf_url"],
                        "language": "sq",
                        "text": text,
                    }
                    try:
                        resp = await api.post(f"{API}/corpus", json=payload)
                        if resp.status_code == 401:  # token expired mid-run
                            token = await _api_token()
                            api.headers["Authorization"] = f"Bearer {token}"
                            resp = await api.post(f"{API}/corpus", json=payload)
                    except httpx.HTTPError as exc:
                        # Backend briefly down — wait, retry once, move on;
                        # a future run picks the judgment up again.
                        await asyncio.sleep(15)
                        try:
                            resp = await api.post(f"{API}/corpus", json=payload)
                        except httpx.HTTPError:
                            print(f"FAIL {reference}: {exc}", flush=True)
                            stats["fail"] += 1
                            continue
                    if resp.status_code == 201:
                        stats["ok"] += 1
                        imported += 1
                        existing.add(reference)
                        _mark_done(row["pdf_url"])
                        done_urls.add(row["pdf_url"])
                        print(f"[{imported}] OK   {payload['title'][:78]} "
                              f"({resp.json()['chunk_count']} chunks)", flush=True)
                    else:
                        stats["fail"] += 1
                        print(f"ERR  {reference} {resp.status_code}: "
                              f"{resp.text[:150]}", flush=True)
                    await asyncio.sleep(DOC_DELAY)

                offset += PAGE_SIZE
                if total is not None and offset >= total:
                    break

    print(f"\nXK case law: ok={stats['ok']} skip={stats['skip']} "
          f"scanned={stats['scan']} fail={stats['fail']}")


def _arg(flag: str, default):
    if flag in sys.argv:
        return sys.argv[sys.argv.index(flag) + 1]
    return default


if __name__ == "__main__":
    courts_arg = str(_arg("--courts", ",".join(DEFAULT_COURTS)))
    years_arg = int(_arg("--years", DEFAULT_YEARS))
    limit_arg = _arg("--limit", None)
    court_keys = [c.strip().lower() for c in courts_arg.split(",") if c.strip()]
    unknown = [c for c in court_keys if c not in COURTS]
    if unknown:
        sys.exit(f"unknown courts: {unknown} (known: {', '.join(COURTS)})")
    asyncio.run(import_judgments(
        court_keys, years_arg, int(limit_arg) if limit_arg else None
    ))
