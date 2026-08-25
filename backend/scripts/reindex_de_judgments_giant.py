"""Targeted re-index of DE judgment docs that still have giant chunks (>2400).

Launch-gate item 3 follow-up (Q-07): after chunk_text learned to split
oversized German legal paragraphs (2026-08-23), every existing doc keeps its
old giant chunks until re-imported. import_de_rechtsprechung.py --force
re-indexes the whole TOC (~16.5k docs); this script touches ONLY the docs
that still have giant chunks (~13k), which is cheaper and gentler on the
API/embedding service.

Resumable: on re-run, docs whose chunks are already ≤2400 are skipped (the
SELECT only returns docs with giant chunks).

    cd backend && .venv/bin/python scripts/reindex_de_judgments_giant.py
    ... --limit 100     # first N only (test runs)
    ... --sleep 0.3     # per-doc delay (default 0.3, same as the importer)
"""
import asyncio
import sys
import zipfile
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from import_de_rechtsprechung import parse_rii_xml  # noqa: E402
from corpus_common import api_token  # noqa: E402

API = "http://127.0.0.1:8000/api"
GIANT = 2400


async def _giant_docs(limit: int | None) -> list[tuple[str, str, str]]:
    """(doc_id, reference, source_url) for DE judgment docs with giant chunks."""
    q = """
        SELECT d.id::text, d.reference, d.source_url
        FROM legal_corpus_chunks c
        JOIN legal_corpus_docs d ON d.id = c.doc_id
        JOIN jurisdictions j ON j.id = d.jurisdiction_id
        WHERE j.code = 'DE' AND d.language = 'de' AND d.doc_type = 'judgment'
          AND length(c.text) > :giant
        GROUP BY d.id, d.reference, d.source_url
        ORDER BY d.id
    """
    async with SessionLocal() as db:
        rows = (await db.execute(text(q), {"giant": GIANT})).fetchall()
        docs = [(r[0], r[1] or "", r[2] or "") for r in rows]
    return docs[:limit] if limit else docs


async def main() -> None:
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    sleep = 0.3
    if "--sleep" in sys.argv:
        sleep = float(sys.argv[sys.argv.index("--sleep") + 1])

    docs = await _giant_docs(limit)
    print(f"giant docs to re-index: {len(docs)}", flush=True)
    if not docs:
        return

    token = await api_token()
    stats = {"ok": 0, "fail": 0, "gone": 0}
    async with httpx.AsyncClient(
        timeout=300,
        headers={"User-Agent": "AvokatIM corpus sync (contact: info@avokatiim.ai)"},
        follow_redirects=True,
    ) as web, httpx.AsyncClient(
        timeout=1800, headers={"Authorization": f"Bearer {token}"}
    ) as api:
        for i, (doc_id, ref, url) in enumerate(docs, 1):
            try:
                r = await web.get(url)
                r.raise_for_status()
                parsed = parse_rii_xml(r.content)
            except Exception as exc:  # noqa: BLE001 — log and continue
                print(f"[{i}/{len(docs)}] FAIL {ref}: {exc}", flush=True)
                stats["fail"] += 1
                continue
            # Drop the old doc first so chunking runs fresh.
            dr = await api.delete(f"{API}/corpus/{doc_id}")
            if dr.status_code not in (204, 404):
                stats["fail"] += 1
                print(f"[{i}/{len(docs)}] ERR  {ref} delete old doc: "
                      f"{dr.status_code} {dr.text[:150]}", flush=True)
                continue
            payload = {
                "jurisdiction_code": "DE",
                "title": parsed["title"][:500],
                "doc_type": "judgment",
                "reference": (parsed["reference"] or parsed["ecli"])[:255],
                "source_url": url,
                "language": "de",
                "text": parsed["text"],
            }
            resp = await api.post(f"{API}/corpus", json=payload)
            if resp.status_code == 401:  # token expired mid-run — refresh once
                token = await api_token()
                api.headers["Authorization"] = f"Bearer {token}"
                resp = await api.post(f"{API}/corpus", json=payload)
            if resp.status_code == 201:
                stats["ok"] += 1
                print(f"[{i}/{len(docs)}] OK   {parsed['title'][:70]} "
                      f"({resp.json()['chunk_count']} chunks)", flush=True)
            elif resp.status_code == 409:  # raced with another importer — fine
                stats["gone"] += 1
            else:
                stats["fail"] += 1
                print(f"[{i}/{len(docs)}] ERR  {ref} {resp.status_code}: "
                      f"{resp.text[:150]}", flush=True)
            await asyncio.sleep(sleep)

    print(f"\nreindex_giant: ok={stats['ok']} gone={stats['gone']} "
          f"fail={stats['fail']} (left with giant chunks: "
          f"{len(docs) - stats['ok'] - stats['gone']})")


if __name__ == "__main__":
    asyncio.run(main())
