"""Import German federal law into the local RAG corpus (jurisdiction DE).

Source: gesetze-im-internet.de — the official portal of the Federal Ministry
of Justice. Every act is published as structured XML (one <norm> per §),
public domain (§ 5 UrhG), with a machine-readable index at gii-toc.xml.

Two modes:
    cd backend
    .venv/bin/python scripts/import_de_laws.py            # ~50 core acts
    .venv/bin/python scripts/import_de_laws.py --slug bgb # one act

Resumable like the GZK importer: (reference, "de") pairs already in the
corpus are skipped. Import goes through the local corpus API so chunking
(§-aware splitter) and local embeddings happen exactly like every other
corpus document.

Re-index (launch-gate item 3 follow-up): pass --force to DELETE the existing
doc by reference first, then re-import it — needed to re-chunk docs that were
indexed before chunk_text split oversized German legal paragraphs (giant
chunks blew up the RAG prompt past the LLM context budget).
    .venv/bin/python scripts/import_de_laws.py --slug bgb --force
"""
import asyncio
import io
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.security import create_access_token  # noqa: E402

API = "http://127.0.0.1:8000/api"
GII = "https://www.gesetze-im-internet.de"
TOC_URL = f"{GII}/gii-toc.xml"
DOC_DELAY = 1.0
MIN_CHARS = 800

# The core set a general-practice German lawyer (and public Ava) needs first.
# Slugs are matched against the gii-toc index with suffix tolerance, so
# "aufenthg" also finds "aufenthg_2004".
CORE_SLUGS = [
    # Verfassung + Justiz
    "gg", "gvg", "brao", "rvg", "rdg",
    # Zivilrecht + Verfahren
    "bgb", "bgbeg", "zpo", "famfg", "prodhaftg", "agg", "vvg_2008", "erbstg",
    # Strafrecht
    "stgb", "stpo", "owig_1968", "jgg", "btmg_1981", "waffg_2002",
    # Arbeit + Soziales
    "kschg", "arbzg", "burlg", "tzbfg", "milog", "betrvg", "arbgg", "entgfg",
    "sgg", "sgb_1", "sgb_2", "sgb_3", "sgb_5", "sgb_6", "sgb_11", "sgb_12",
    # Verwaltung + Steuern
    "vwgo", "vwvfg", "ao_1977", "fgo", "estg", "ustg_1980",
    # Wirtschaft
    "hgb", "gmbhg", "aktg", "inso", "gewo", "hwo",
    # Miete/Wohnen ist im BGB; WEG separat
    "woeigg",
    # Migration
    "aufenthg_2004", "asylvfg_1992", "stag",
    # Verkehr
    "stvg", "stvo_2013",
    # Digitales + Datenschutz
    "bdsg_2018", "ddg", "urhg", "markeng", "patg",
    # --- Wave 2 (2026-08-01): high-frequency citizen topics ---
    # Familie + Schutz
    "beeg", "muschg_2018", "gewschg", "uhvorschg",
    # Zugang zum Recht + Kosten
    "berathig", "gkg_2004", "famgkg",
    # Verbraucher
    "uwg_2004",
    # Soziales (restliche Bücher mit Bürgerrelevanz)
    "sgb_4", "sgb_7", "sgb_8", "sgb_9_2018", "sgb_10",
    # Wohnen + Ausbildung
    "wogg", "baf_g", "bbig_2005", "nachwg",
    # Verkehr (Unfälle, Führerschein)
    "pflvg", "fev_2010",
    # Zwangsvollstreckung Immobilien
    "zvg",
]


async def _api_token() -> str:
    async with SessionLocal() as db:
        owner = (
            await db.execute(select(User).where(User.role == "admin").limit(1))
        ).scalars().first()
        return create_access_token(str(owner.id), str(owner.tenant_id))


def _slug_of(link: str) -> str:
    # http://www.gesetze-im-internet.de/bgb/xml.zip -> bgb
    return link.rstrip("/").split("/")[-2].lower()


async def _load_toc(web: httpx.AsyncClient) -> dict[str, str]:
    """slug -> xml.zip URL for every act on the portal (~6500)."""
    r = await web.get(TOC_URL)
    r.raise_for_status()
    toc = {}
    for item in ET.fromstring(r.content).iter("item"):
        link = item.findtext("link") or ""
        if link.endswith("xml.zip"):
            toc[_slug_of(link)] = link.replace("http://", "https://")
    return toc


def _resolve(toc: dict[str, str], slug: str) -> tuple[str, str] | None:
    """Exact slug, then prefix-tolerant match (aufenthg -> aufenthg_2004)."""
    if slug in toc:
        return slug, toc[slug]
    base = slug.split("_")[0]
    candidates = sorted(s for s in toc if s == base or s.startswith(base + "_"))
    if candidates:
        return candidates[-1], toc[candidates[-1]]
    return None


def _norm_text(norm: ET.Element) -> str:
    content = norm.find("./textdaten/text/Content")
    if content is None:
        return ""
    parts = ["".join(p.itertext()).strip() for p in content]
    if not parts:
        parts = ["".join(content.itertext()).strip()]
    return "\n".join(p for p in parts if p)


def parse_gii_xml(data: bytes) -> tuple[str, str, str]:
    """(title, reference, plain_text) from a gesetze-im-internet XML zip.

    Each § becomes a "§ N Titel" heading line, so the corpus splitter
    (_SECTION_RE knows '§'/'Art'/'Artikel') chunks by section like it does
    for 'Neni N' in Kosovo acts.
    """
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        xml_name = next(n for n in zf.namelist() if n.endswith(".xml"))
        root = ET.fromstring(zf.read(xml_name))

    norms = root.findall("norm")
    head = norms[0].find("metadaten")
    title = (head.findtext("langue") or head.findtext("kurzue") or "").strip()
    reference = (head.findtext("jurabk") or "").strip()

    blocks: list[str] = []
    for norm in norms:
        meta = norm.find("metadaten")
        enbez = (meta.findtext("enbez") or "").strip()
        section_title = "".join(
            (meta.find("titel").itertext() if meta.find("titel") is not None else [])
        ).strip()
        body = _norm_text(norm)
        if not enbez or not re.match(r"^(§|Art)", enbez):
            continue  # skip Inhaltsübersicht, Anlagen, Eingangsformel
        if not body:
            continue
        heading = f"{enbez} {section_title}".strip()
        blocks.append(f"{heading}\n{body}")
    text = "\n\n".join(blocks)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return title, reference, text


async def import_slugs(slugs: list[str], force: bool = False) -> None:
    token = await _api_token()
    stats = {"ok": 0, "skip": 0, "fail": 0, "reindex": 0}
    async with httpx.AsyncClient(
        timeout=180, headers={"User-Agent": "AvokatIM corpus sync (contact: info@avokatiim.ai)"},
        follow_redirects=True,
    ) as web, httpx.AsyncClient(
        timeout=1800, headers={"Authorization": f"Bearer {token}"}
    ) as api:
        toc = await _load_toc(web)
        print(f"gii-toc: {len(toc)} acts on the portal", flush=True)
        existing = {
            d.get("reference"): d.get("id")
            for d in (await api.get(f"{API}/corpus?jurisdiction_code=DE")).json()
        }

        total = len(slugs)
        for i, want in enumerate(slugs, 1):
            resolved = _resolve(toc, want)
            if resolved is None:
                print(f"[{i}/{total}] FAIL {want}: not in gii-toc", flush=True)
                stats["fail"] += 1
                continue
            slug, url = resolved
            try:
                r = await web.get(url)
                r.raise_for_status()
                title, reference, text = parse_gii_xml(r.content)
            except Exception as exc:  # noqa: BLE001 — log and continue the batch
                print(f"[{i}/{total}] FAIL {slug}: {exc}", flush=True)
                stats["fail"] += 1
                continue
            reference = reference or slug.upper()
            if reference in existing:
                if not force:
                    stats["skip"] += 1
                    continue
                # Re-index: drop the old doc (with its giant chunks) first, so
                # the POST below re-chunks with the current chunk_text.
                doc_id = existing[reference]
                r = await api.delete(f"{API}/corpus/{doc_id}")
                if r.status_code not in (204, 404):  # 404 = already gone, fine
                    stats["fail"] += 1
                    print(f"[{i}/{total}] ERR  {slug} delete old doc: "
                          f"{r.status_code} {r.text[:150]}", flush=True)
                    continue
                stats["reindex"] += 1
                print(f"[{i}/{total}] DEL {reference} (old doc removed, re-importing)",
                      flush=True)
                existing.pop(reference, None)
            if len(text) < MIN_CHARS:
                print(f"[{i}/{total}] FAIL {slug}: only {len(text)} chars", flush=True)
                stats["fail"] += 1
                continue

            resp = await api.post(f"{API}/corpus", json={
                "jurisdiction_code": "DE",
                "title": title[:500] or slug.upper(),
                "doc_type": "law",
                "reference": reference[:255],
                "source_url": f"{GII}/{slug}/",
                "language": "de",
                "text": text,
            })
            if resp.status_code == 401:  # token expired mid-run — refresh once
                token = await _api_token()
                api.headers["Authorization"] = f"Bearer {token}"
                resp = await api.post(f"{API}/corpus", json={
                    "jurisdiction_code": "DE", "title": title[:500] or slug.upper(),
                    "doc_type": "law", "reference": reference[:255],
                    "source_url": f"{GII}/{slug}/", "language": "de", "text": text,
                })
            if resp.status_code == 201:
                stats["ok"] += 1
                existing[reference] = resp.json()["id"]
                print(f"[{i}/{total}] OK   {reference} {title[:60]} "
                      f"({resp.json()['chunk_count']} chunks)", flush=True)
            else:
                stats["fail"] += 1
                print(f"[{i}/{total}] ERR  {slug} {resp.status_code}: "
                      f"{resp.text[:150]}", flush=True)
            await asyncio.sleep(DOC_DELAY)

    print(f"\nDE: ok={stats['ok']} skip={stats['skip']} "
          f"reindex={stats['reindex']} fail={stats['fail']}")


if __name__ == "__main__":
    force = "--force" in sys.argv
    if "--slug" in sys.argv:
        # Support repeated --slug bgb --slug zpo ... (single --slug kept for
        # backward compatibility).
        wanted = []
        args = sys.argv[1:]
        while "--slug" in args:
            idx = args.index("--slug")
            wanted.append(args[idx + 1].lower())
            args = args[idx + 2:]
    else:
        wanted = CORE_SLUGS
    asyncio.run(import_slugs(wanted, force=force))
