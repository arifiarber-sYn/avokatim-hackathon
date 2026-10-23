"""Import the GDPR (DSGVO) German consolidated text into the DE corpus.

The GDPR is an EU regulation, so it is not on gesetze-im-internet.de. Source
is the Publications Office CELLAR API (official, machine-readable, reuse
permitted by Decision 2011/833/EU): the consolidated German XHTML of
CELEX 02016R0679. EUR-Lex's human portal answers bots with empty 202s;
CELLAR serves the same content reliably.

    cd backend && .venv/bin/python scripts/import_dsgvo.py

Each "Artikel N" becomes a heading line the corpus splitter recognizes, so
chunking + local embeddings work exactly like the federal-law importer.
"""
import asyncio
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.security import create_access_token  # noqa: E402

API = "http://127.0.0.1:8000/api"
CELLAR_URL = "http://publications.europa.eu/resource/celex/02016R0679-20160504"
SOURCE_URL = (
    "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:02016R0679"
)
XHTML_NS = "{http://www.w3.org/1999/xhtml}"


async def _api_token() -> str:
    async with SessionLocal() as db:
        owner = (
            await db.execute(select(User).where(User.role == "admin").limit(1))
        ).scalars().first()
        return create_access_token(str(owner.id), str(owner.tenant_id))


def _text_of(el: ET.Element) -> str:
    txt = " ".join("".join(el.itertext()).split())
    return txt.strip()


def parse_dsgvo_xhtml(data: bytes) -> str:
    """Plain text with one 'Artikel N Titel' heading per article."""
    root = ET.fromstring(data)
    blocks: list[str] = []
    for div in root.iter(f"{XHTML_NS}div"):
        if not re.fullmatch(r"art_\d+", div.get("id") or ""):
            continue
        number = title = ""
        body: list[str] = []
        for child in div.iter():
            cls = child.get("class") or ""
            if cls == "title-article-norm":
                number = _text_of(child)
            elif cls == "stitle-article-norm":
                title = _text_of(child)
            elif cls == "norm":
                para = _text_of(child)
                if para:
                    body.append(para)
        if number and body:
            blocks.append(f"{number} {title}".strip() + "\n" + "\n".join(body))
    return "\n\n".join(blocks)


async def main() -> None:
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as web:
        r = await web.get(
            CELLAR_URL,
            headers={"Accept": "application/xhtml+xml", "Accept-Language": "deu"},
        )
        r.raise_for_status()
    text = parse_dsgvo_xhtml(r.content)
    articles = text.count("\nArtikel") + 1
    print(f"parsed: {len(text)} chars, {articles} articles", flush=True)
    if articles < 90:  # the GDPR has 99 articles
        raise SystemExit("parse looks incomplete — aborting, nothing posted")

    token = await _api_token()
    async with httpx.AsyncClient(
        timeout=1800, headers={"Authorization": f"Bearer {token}"}
    ) as api:
        existing = {
            d.get("reference")
            for d in (await api.get(f"{API}/corpus?jurisdiction_code=DE")).json()
        }
        if "DSGVO" in existing:
            print("DSGVO already in corpus — nothing to do")
            return
        resp = await api.post(f"{API}/corpus", json={
            "jurisdiction_code": "DE",
            "title": "Verordnung (EU) 2016/679 — Datenschutz-Grundverordnung",
            "doc_type": "law",
            "reference": "DSGVO",
            "source_url": SOURCE_URL,
            "language": "de",
            "text": text,
        })
        resp.raise_for_status()
        print(f"OK DSGVO ({resp.json()['chunk_count']} chunks)")


if __name__ == "__main__":
    asyncio.run(main())
