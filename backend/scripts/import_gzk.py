"""Import Kosovo laws from Gazeta Zyrtare (gzk.rks-gov.net) into the RAG corpus.

Fetches the full text of each act from ActDocumentDetail.aspx, strips the HTML,
and posts it to the local corpus API (which chunks by "Neni X" and embeds
locally). Safe to re-run: laws whose reference already exists are skipped.

Usage:
    cd backend && .venv/bin/python scripts/import_gzk.py

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
]

_SPAN_RE = re.compile(
    r'<span id="MainContent_txtDocument">(.*?)</span>', re.DOTALL
)


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

    async with httpx.AsyncClient(timeout=180, headers={"User-Agent": "Mozilla/5.0"}) as web, \
            httpx.AsyncClient(timeout=600, headers=headers) as api:
        existing = {
            d.get("reference")
            for d in (await api.get(f"{API}/corpus?jurisdiction_code=XK")).json()
        }
        for title, reference, doc_type, act_ids in LAWS:
            if reference in existing:
                print(f"SKIP  {reference}  {title} (already in corpus)")
                continue
            text = None
            source_url = None
            for candidate_src in act_ids:
                if isinstance(candidate_src, int):
                    url = f"https://gzk.rks-gov.net/ActDocumentDetail.aspx?ActID={candidate_src}"
                else:
                    url = candidate_src
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
                if candidate and len(candidate) > 5000 and "Neni" in candidate:
                    text, source_url = candidate, url
                    break
            if text is None:
                print(f"FAIL  {reference}  {title} — no usable text found")
                continue
            print(f"LOAD  {reference}  {title} ({len(text)//1000} KB) ...", flush=True)
            r = await api.post(
                f"{API}/corpus",
                json={
                    "jurisdiction_code": "XK",
                    "title": title,
                    "doc_type": doc_type,
                    "reference": reference,
                    "source_url": source_url,
                    "language": "sq",
                    "text": text,
                },
            )
            if r.status_code == 201:
                print(f"  OK — {r.json()['chunk_count']} chunks")
            else:
                print(f"  ERROR {r.status_code}: {r.text[:200]}")


asyncio.run(main())
