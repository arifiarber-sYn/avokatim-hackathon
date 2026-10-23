"""Bulk-import the COMPLETE Kosovo legislation from Gazeta Zyrtare into the
local RAG corpus (constitution, codes, laws, consolidated acts).

Two phases:

1. `--index` crawls the GZK search listing per category and writes
   data/gzk_laws_index.json (ActID, title, category). Polite: sequential,
   0.5s between pages.
2. `--lang sq|sr|tr|bs|en` imports every indexed act in that language via the
   local corpus API (which chunks by article and embeds locally). Fully
   resumable: (reference, language) pairs already in the corpus are skipped,
   so restarts/reboots just continue where they left off.

Consolidated acts are imported first so the current wording wins the
reference; the original base law is then skipped as a duplicate.

Usage:
    cd backend
    .venv/bin/python scripts/import_gzk_bulk.py --index
    .venv/bin/python scripts/import_gzk_bulk.py --lang sq
"""
import asyncio
import html as html_lib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.config import PROJECT_DIR  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.security import create_access_token  # noqa: E402

API = "http://127.0.0.1:8000/api"
GZK = "https://gzk.rks-gov.net"
INDEX_FILE = PROJECT_DIR / "data" / "gzk_laws_index.json"
PAGE_DELAY = 0.5
DOC_DELAY = 1.0

# Import order matters: consolidated versions first (current wording), the
# original law is then skipped because the reference is already present.
CATEGORIES = [
    ("kushtetuta", 1, "constitution"),
    ("kode", 5, "code"),
    ("konsoliduara", 125, "law"),
    ("ligje", 6, "law"),
]

LANG_POSTBACK = {
    "sr": "ctl00$ctlLang1$lbSerbian",
    "tr": "ctl00$ctlLang1$lbTurkish",
    "bs": "ctl00$ctlLang1$lbBosnian",
    "en": "ctl00$ctlLang1$lbEnglish",
}
LANG_MARKERS = {
    "sq": ("Neni", "NENI"),
    "sr": ("Član", "Clan", "ČLAN"),
    "bs": ("Član", "Clan", "ČLAN"),
    "tr": ("Madde", "MADDE"),
    "en": ("Article", "ARTICLE"),
}
# Tesseract models: sqi/eng come from the system install, srp_latn/tur/bos
# were fetched from tessdata_fast into data/tessdata (all copied there so a
# single TESSDATA_PREFIX works).
TESSDATA_DIR = PROJECT_DIR / "data" / "tessdata"
OCR_LANG = {"sq": "sqi", "sr": "srp_latn", "bs": "bos", "tr": "tur", "en": "eng"}
OCR_MAX_PAGES = 400
AMENDMENT_MARKERS = {
    "sq": ("Amendament", "Amandament", "AMENDAMENT", "AMANDAMENT"),
    "sr": ("Amandman", "AMANDMAN"),
    "bs": ("Amandman", "AMANDMAN"),
    "tr": ("Değişiklik", "DEĞİŞİKLİK", "Anayasa"),
    "en": ("Amendment", "AMENDMENT"),
}
# Short ratification laws have only a few articles
MIN_CHARS = 800

_SPAN_RE = re.compile(r'<span id="MainContent_txtDocument">(.*?)</span>', re.DOTALL)
_TITLE_RE = re.compile(r'id="MainContent_rAktet_lblAn_0"[^>]*>([^<]+)<')
_ACT_LINK_RE = re.compile(r'ActDetail\.aspx\?ActID=(\d+)"[^>]*>([^<]{3,200})')
_NEXT_RE = re.compile(r"doPostBack\(&#39;(ctl00\$MainContent\$gvAktet\$ctl\d+\$lbNext)&#39;")
# "LIGJI NR. 06/L-010 ...", "KODI NR. 08/L-032 ...", "LIGJI Nr. 2004/32 ..."
_REF_RE = re.compile(r"\b(?:NR|Nr|No)\.?\s*([0-9]{2,4}/[A-Z]-[0-9]{2,3}|[0-9]{4}/[0-9]{1,3})", re.IGNORECASE)


def _field(page_html: str, name: str) -> str:
    m = re.search(rf'id="{name}" value="([^"]*)"', page_html)
    return m.group(1) if m else ""


def _clean_title(raw: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(raw)).strip()


def _reference_for(act: dict) -> str:
    m = _REF_RE.search(act["title"])
    return m.group(1).upper() if m else f"GZK-{act['act_id']}"


def _extract_text(page_html: str) -> str | None:
    m = _SPAN_RE.search(page_html)
    if not m:
        return None
    body = re.sub(r"<br\s*/?>", "\n", m.group(1), flags=re.IGNORECASE)
    body = re.sub(r"<[^>]+>", " ", body)
    body = html_lib.unescape(body)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in body.splitlines()]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return text or None


def _ocr_pdf(content: bytes, lang: str) -> str | None:
    """Last resort for scanned gazette PDFs (mostly pre-2010 acts): rasterize
    with pdftoppm and OCR with tesseract. Slow but runs only when the PDF has
    no embedded text layer."""
    import os
    import subprocess
    import tempfile

    model = OCR_LANG[lang]
    if not (TESSDATA_DIR / f"{model}.traineddata").exists():
        return None
    env = dict(os.environ, TESSDATA_PREFIX=str(TESSDATA_DIR))
    try:
        with tempfile.TemporaryDirectory() as td:
            pdf_path = os.path.join(td, "act.pdf")
            with open(pdf_path, "wb") as fh:
                fh.write(content)
            subprocess.run(
                ["pdftoppm", "-r", "200", "-gray", "-png",
                 "-l", str(OCR_MAX_PAGES), pdf_path, os.path.join(td, "pg")],
                check=True, capture_output=True, timeout=600,
            )
            pages = sorted(f for f in os.listdir(td) if f.endswith(".png"))
            texts = []
            for pg in pages:
                out = subprocess.run(
                    ["tesseract", os.path.join(td, pg), "-", "-l", model, "--psm", "6"],
                    capture_output=True, text=True, env=env, timeout=120,
                )
                texts.append(out.stdout)
    except (subprocess.SubprocessError, OSError):
        return None
    return "\n".join(texts).strip() or None


async def _fetch_pdf_text(
    web: httpx.AsyncClient, act_id: int, lang: str, ocr: bool = True
) -> tuple[str | None, str]:
    """Fallback for acts published only as gazette PDFs (~1/4 of all laws):
    ActDetail.aspx carries an image-button postback that serves the PDF of
    the act in the current session language. Returns (text, source_tag)."""
    import io

    from pypdf import PdfReader

    url = f"{GZK}/ActDetail.aspx?ActID={act_id}"
    try:
        r = await web.get(url)
        r.raise_for_status()
        r2 = await web.post(url, data={
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": _field(r.text, "__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": _field(r.text, "__VIEWSTATEGENERATOR"),
            "__EVENTVALIDATION": _field(r.text, "__EVENTVALIDATION"),
            "ctl00$MainContent$rAktet$ctl00$imgDownload.x": "5",
            "ctl00$MainContent$rAktet$ctl00$imgDownload.y": "5",
        })
        r2.raise_for_status()
    except httpx.HTTPError:
        return None, "pdf"
    if not r2.headers.get("content-type", "").lower().startswith("application/pdf"):
        return None, "pdf"
    source = "pdf"
    try:
        reader = PdfReader(io.BytesIO(r2.content))
        text = "\n".join(p.extract_text() or "" for p in reader.pages).strip()
    except Exception:
        text = ""
    if len(text) < 200 and ocr:  # scanned image PDF — no embedded text layer
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, _ocr_pdf, r2.content, lang) or ""
        source = "ocr"
    if not text:
        return None, source
    # Drop the running gazette header lines so they don't pollute chunks
    text = re.sub(
        r"^.*(GAZETA ZYRTARE|SLU[ŽZ]BENI LIST|RESM[İI] GAZETE|OFFICIAL GAZETTE).*$",
        "", text, flags=re.MULTILINE | re.IGNORECASE,
    )
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return (text or None), source


async def build_index() -> None:
    acts: list[dict] = []
    seen_ids: set[int] = set()
    async with httpx.AsyncClient(
        timeout=120, headers={"User-Agent": "Mozilla/5.0 (AvokatIM corpus sync)"},
        follow_redirects=True,
    ) as web:
        for cat_name, cat_id, doc_type in CATEGORIES:
            url = f"{GZK}/SearchIn.aspx?Index=2&so=1&CatID={cat_id}"
            r = await web.get(url)
            page = 1
            while True:
                found = 0
                for act_id, title in _ACT_LINK_RE.findall(r.text):
                    aid = int(act_id)
                    if aid in seen_ids:
                        continue
                    seen_ids.add(aid)
                    acts.append({
                        "act_id": aid,
                        "title": _clean_title(title),
                        "category": cat_name,
                        "doc_type": doc_type,
                    })
                    found += 1
                next_m = _NEXT_RE.search(r.text)
                print(f"{cat_name} page {page}: +{found} (total {len(acts)})", flush=True)
                if next_m is None:
                    break
                await asyncio.sleep(PAGE_DELAY)
                r = await web.post(url, data={
                    "__EVENTTARGET": next_m.group(1),
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": _field(r.text, "__VIEWSTATE"),
                    "__VIEWSTATEGENERATOR": _field(r.text, "__VIEWSTATEGENERATOR"),
                    "__EVENTVALIDATION": _field(r.text, "__EVENTVALIDATION"),
                })
                page += 1
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps({
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "acts": acts,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nIndex written: {len(acts)} acts -> {INDEX_FILE}")


async def _api_token() -> str:
    async with SessionLocal() as db:
        owner = (
            await db.execute(select(User).where(User.role == "admin").limit(1))
        ).scalars().first()
        return create_access_token(str(owner.id), str(owner.tenant_id))


async def _switch_language(web: httpx.AsyncClient, lang: str, act_id: int) -> None:
    url = f"{GZK}/ActDetail.aspx?ActID={act_id}"
    r = await web.get(url)
    r.raise_for_status()
    await web.post(url, data={
        "__EVENTTARGET": LANG_POSTBACK[lang],
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": _field(r.text, "__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": _field(r.text, "__VIEWSTATEGENERATOR"),
        "__EVENTVALIDATION": _field(r.text, "__EVENTVALIDATION"),
    })


async def _localized_title(web: httpx.AsyncClient, act_id: int) -> str | None:
    try:
        r = await web.get(f"{GZK}/ActDetail.aspx?ActID={act_id}")
        r.raise_for_status()
    except httpx.HTTPError:
        return None
    m = _TITLE_RE.search(r.text)
    return _clean_title(m.group(1)).title() if m else None


async def import_language(lang: str) -> None:
    acts = json.loads(INDEX_FILE.read_text(encoding="utf-8"))["acts"]
    token = await _api_token()

    stats = {"ok": 0, "skip": 0, "fail": 0}
    async with httpx.AsyncClient(
        timeout=180, headers={"User-Agent": "Mozilla/5.0 (AvokatIM corpus sync)"},
        follow_redirects=True,
    ) as web, httpx.AsyncClient(
        timeout=900, headers={"Authorization": f"Bearer {token}"}
    ) as api:
        existing = {
            (d.get("reference"), d.get("language"))
            for d in (await api.get(f"{API}/corpus?jurisdiction_code=XK")).json()
        }
        if lang != "sq":
            await _switch_language(web, lang, acts[0]["act_id"])
            print(f"GZK session language: {lang}", flush=True)

        total = len(acts)
        for i, act in enumerate(acts, 1):
            reference = _reference_for(act)
            if (reference, lang) in existing:
                stats["skip"] += 1
                continue
            # Constitutional amendments are short and use "Amendamenti ..."
            # headers instead of article headers.
            if act["category"] == "kushtetuta":
                markers = LANG_MARKERS[lang] + AMENDMENT_MARKERS[lang]
                min_chars = 400
            else:
                markers = LANG_MARKERS[lang]
                min_chars = MIN_CHARS
            try:
                r = await web.get(f"{GZK}/ActDocumentDetail.aspx?ActID={act['act_id']}")
                r.raise_for_status()
                text = _extract_text(r.text)
            except httpx.HTTPError as exc:
                print(f"[{i}/{total}] FAIL {reference} fetch: {exc}", flush=True)
                stats["fail"] += 1
                continue
            source = "html"
            if not text or len(text) < min_chars or not any(m in text for m in markers):
                text, source = await _fetch_pdf_text(web, act["act_id"], lang)
            if not text or len(text) < min_chars or not any(m in text for m in markers):
                print(f"[{i}/{total}] FAIL {reference} — no usable {lang} text "
                      f"({len(text or '')} chars)", flush=True)
                stats["fail"] += 1
                continue

            title = act["title"].title()
            if lang != "sq":
                title = (await _localized_title(web, act["act_id"])) or f"{title} [{lang.upper()}]"

            resp = await api.post(f"{API}/corpus", json={
                "jurisdiction_code": "XK",
                "title": title[:500],
                "doc_type": act["doc_type"],
                "reference": reference,
                "source_url": f"{GZK}/ActDetail.aspx?ActID={act['act_id']}",
                "language": lang,
                "text": text,
            })
            if resp.status_code == 401:  # token expired mid-run — refresh once
                token = await _api_token()
                api.headers["Authorization"] = f"Bearer {token}"
                resp = await api.post(f"{API}/corpus", json={
                    "jurisdiction_code": "XK", "title": title[:500],
                    "doc_type": act["doc_type"], "reference": reference,
                    "source_url": f"{GZK}/ActDetail.aspx?ActID={act['act_id']}",
                    "language": lang, "text": text,
                })
            if resp.status_code == 201:
                stats["ok"] += 1
                existing.add((reference, lang))
                print(f"[{i}/{total}] OK   {reference} {title[:60]} "
                      f"({resp.json()['chunk_count']} chunks, {source})", flush=True)
            else:
                stats["fail"] += 1
                print(f"[{i}/{total}] ERR  {reference} {resp.status_code}: "
                      f"{resp.text[:150]}", flush=True)
            await asyncio.sleep(DOC_DELAY)

    print(f"\n{lang}: ok={stats['ok']} skip={stats['skip']} fail={stats['fail']}")


if __name__ == "__main__":
    if "--index" in sys.argv:
        asyncio.run(build_index())
    elif "--lang" in sys.argv:
        lang = sys.argv[sys.argv.index("--lang") + 1]
        if lang not in LANG_MARKERS:
            sys.exit(f"unsupported --lang {lang!r}")
        asyncio.run(import_language(lang))
    else:
        sys.exit("usage: import_gzk_bulk.py --index | --lang sq|sr|tr|bs|en")
