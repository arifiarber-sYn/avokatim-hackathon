"""Import Kosovo laws from Gazeta Zyrtare (gzk.rks-gov.net) into the RAG corpus.

Fetches the full text of each act from ActDocumentDetail.aspx, strips the HTML,
and posts it to the local corpus API (which chunks by article headers and
embeds locally). Safe to re-run: laws whose (reference, language) pair already
exists are skipped.

The gazette is official in five languages (Law 03/L-190): Albanian, Serbian,
Turkish, Bosnian and English. GZK serves the language versions of the same
ActID after a session language postback, so `--lang sr` imports the official
Serbian texts, etc. PDF mirror candidates are Albanian-only and are skipped
for other languages.

Usage:
    cd backend && .venv/bin/python scripts/import_gzk.py             # Albanian
    cd backend && .venv/bin/python scripts/import_gzk.py --lang sr   # Serbian

To add more laws, append entries to LAWS below (find the ActID in the act's
URL on gzk.rks-gov.net; candidates are tried in order — put the consolidated
version first when one exists).
"""
import asyncio
import html as html_lib
import re
import sys

import httpx

sys.path.insert(0, ".")
from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.security import create_access_token  # noqa: E402

API = "http://127.0.0.1:8000/api"
GZK = "https://gzk.rks-gov.net"

LANG = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "sq"

# ASP.NET postback targets that switch the GZK session language.
LANG_POSTBACK = {
    "sr": "ctl00$ctlLang1$lbSerbian",
    "tr": "ctl00$ctlLang1$lbTurkish",
    "bs": "ctl00$ctlLang1$lbBosnian",
    "en": "ctl00$ctlLang1$lbEnglish",
}
if LANG != "sq" and LANG not in LANG_POSTBACK:
    sys.exit(f"unsupported --lang {LANG!r} (use sq, sr, tr, bs or en)")

# A text is accepted only when it contains the article header of its language
# (guards against GZK silently serving the Albanian fallback).
LANG_MARKERS = {
    "sq": ("Neni",),
    "sr": ("Član", "Clan", "ČLAN"),
    "bs": ("Član", "Clan", "ČLAN"),
    "tr": ("Madde", "MADDE"),
    "en": ("Article", "ARTICLE"),
}

# (title, reference, doc_type, [candidates]) — a candidate is either an int
# (GZK ActID) or a str (direct PDF URL, e.g. Ministry of Justice mirror).
LAWS = [
    ("Ligji për Procedurën Kontestimore (LPK)", "03/L-006", "law", [2583]),
    ("Kodi i Procedurës Penale", "08/L-032", "code", [61759]),
    ("Kodi Penal i Republikës së Kosovës", "06/L-074", "code", [116031, 18413]),
    ("Ligji për Marrëdhëniet e Detyrimeve (LMD)", "04/L-077", "law", [2828]),
    ("Ligji i Punës", "03/L-212", "law", [2735]),
    (
        "Ligji për Konfliktet Administrative",
        "08/L-182",
        "law",
        [
            85181,
            "https://md.rks-gov.net/wp-content/uploads/2024/06/EDD92EDA-8F48-49D0-A6E0-D831B9B30DF0.pdf",
        ],
    ),
    ("Ligji për Shoqëritë Tregtare", "06/L-016", "law", [16426]),
    ("Ligji për Familjen i Kosovës", "2004/32", "law", [111755, 2410]),
    ("Ligji për Mbrojtjen e të Dhënave Personale", "06/L-082", "law", [18616]),
    ("Ligji për Noterinë", "06/L-010", "law", [18334]),
    # Amendment laws are only a few articles long, hence the low min_chars.
    (
        "Ligji për ndryshimin e Ligjit për Noterinë (kompetenca territoriale)",
        "08/L-149",
        "law",
        # GZK hosts this amendment only as a PDF behind a postback; the
        # Ministry of Justice mirror serves the same official text directly.
        [
            66879,
            "https://md.rks-gov.net/wp-content/uploads/2024/06/15BB1CC5-280D-4269-8A2E-A2EE7CAC8D8F.pdf",
        ],
        1000,
    ),
    # NOTE: amendment 08/L-272 (e-signature arts. 31A/31B, discipline moved to
    # MoJ) has no machine-readable text online yet (GZK span is empty, gazette
    # PDF behind postback, Assembly site behind Cloudflare). Re-try later.
]

_SPAN_RE = re.compile(
    r'<span id="MainContent_txtDocument">(.*?)</span>', re.DOTALL
)
# The act's own (localized) title on ActDetail.aspx
_TITLE_RE = re.compile(r'id="MainContent_rAktet_lblAn_0"[^>]*>([^<]+)<')


def _form_field(page_html: str, name: str) -> str:
    m = re.search(rf'id="{name}" value="([^"]*)"', page_html)
    return m.group(1) if m else ""


async def _switch_gzk_language(web: httpx.AsyncClient, act_id: int) -> None:
    """ASP.NET postback that flips the GZK session language; the session
    cookie persists on the client, so every later fetch is localized."""
    url = f"{GZK}/ActDetail.aspx?ActID={act_id}"
    r = await web.get(url, follow_redirects=True)
    r.raise_for_status()
    await web.post(
        url,
        data={
            "__EVENTTARGET": LANG_POSTBACK[LANG],
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": _form_field(r.text, "__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": _form_field(r.text, "__VIEWSTATEGENERATOR"),
            "__EVENTVALIDATION": _form_field(r.text, "__EVENTVALIDATION"),
        },
        follow_redirects=True,
    )


async def _localized_title(web: httpx.AsyncClient, act_id: int) -> str | None:
    try:
        r = await web.get(f"{GZK}/ActDetail.aspx?ActID={act_id}", follow_redirects=True)
        r.raise_for_status()
    except httpx.HTTPError:
        return None
    m = _TITLE_RE.search(r.text)
    if not m:
        return None
    title = html_lib.unescape(m.group(1))
    return re.sub(r"\s+", " ", title).strip().title() or None


def _extract_pdf_text(content: bytes) -> str | None:
    import io

    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(content))
        pages = [p.extract_text() or "" for p in reader.pages]
        text = "\n".join(pages).strip()
        return text or None
    except Exception:
        return None


def _extract_text(page_html: str) -> str | None:
    m = _SPAN_RE.search(page_html)
    if not m:
        return None
    body = m.group(1)
    body = re.sub(r"<br\s*/?>", "\n", body, flags=re.IGNORECASE)
    body = re.sub(r"<[^>]+>", " ", body)
    body = html_lib.unescape(body)
    # collapse whitespace but keep line structure (needed for "Neni X" splitting)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in body.splitlines()]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text or None


async def main() -> None:
    async with SessionLocal() as db:
        owner = (
            await db.execute(select(User).where(User.role == "admin").limit(1))
        ).scalars().first()
        if owner is None:
            owner = (await db.execute(select(User).limit(1))).scalars().first()
        token = create_access_token(str(owner.id), str(owner.tenant_id))
    headers = {"Authorization": f"Bearer {token}"}

    markers = LANG_MARKERS[LANG]
    async with httpx.AsyncClient(timeout=180, headers={"User-Agent": "Mozilla/5.0"}) as web, \
            httpx.AsyncClient(timeout=600, headers=headers) as api:
        existing = {
            (d.get("reference"), d.get("language"))
            for d in (await api.get(f"{API}/corpus?jurisdiction_code=XK")).json()
        }
        if LANG != "sq":
            first_act = next(
                c for entry in LAWS for c in entry[3] if isinstance(c, int)
            )
            await _switch_gzk_language(web, first_act)
            print(f"GZK session language switched to {LANG}\n")
        for entry in LAWS:
            title, reference, doc_type, act_ids = entry[:4]
            min_chars = entry[4] if len(entry) > 4 else 5000
            if (reference, LANG) in existing:
                print(f"SKIP  {reference}  {title} (already in corpus, {LANG})")
                continue
            text = None
            source_url = None
            loaded_act_id = None
            for candidate_src in act_ids:
                if isinstance(candidate_src, int):
                    url = f"{GZK}/ActDocumentDetail.aspx?ActID={candidate_src}"
                elif LANG == "sq":
                    url = candidate_src
                else:
                    # PDF mirrors (Ministry of Justice) are Albanian-only
                    continue
                try:
                    r = await web.get(url, follow_redirects=True)
                    r.raise_for_status()
                except httpx.HTTPError as exc:
                    print(f"  warn: fetch failed for {url}: {exc}")
                    continue
                if url.lower().endswith(".pdf") or r.headers.get(
                    "content-type", ""
                ).startswith("application/pdf"):
                    candidate = _extract_pdf_text(r.content)
                else:
                    candidate = _extract_text(r.text)
                if (
                    candidate
                    and len(candidate) > min_chars
                    and any(m in candidate for m in markers)
                ):
                    text, source_url = candidate, url
                    if isinstance(candidate_src, int):
                        loaded_act_id = candidate_src
                    break
            if text is None:
                print(f"FAIL  {reference}  {title} — no usable {LANG} text found")
                continue
            doc_title = title
            if LANG != "sq":
                doc_title = (
                    await _localized_title(web, loaded_act_id) if loaded_act_id else None
                ) or f"{title} [{LANG.upper()}]"
            print(f"LOAD  {reference}  {doc_title} ({len(text)//1000} KB) ...", flush=True)
            r = await api.post(
                f"{API}/corpus",
                json={
                    "jurisdiction_code": "XK",
                    "title": doc_title,
                    "doc_type": doc_type,
                    "reference": reference,
                    "source_url": source_url,
                    "language": LANG,
                    "text": text,
                },
            )
            if r.status_code == 201:
                print(f"  OK — {r.json()['chunk_count']} chunks")
            else:
                print(f"  ERROR {r.status_code}: {r.text[:200]}")


asyncio.run(main())
