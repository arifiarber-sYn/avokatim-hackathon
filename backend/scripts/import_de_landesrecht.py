"""Import German Landesrecht (state law) into the DE corpus, tagged with the
Bundesland's `region` code (D-035).

Unlike federal law (gesetze-im-internet.de XML, see import_de_laws.py), every
Land publishes on its own portal in its own format, so this script is a set
of small per-portal adapters plus a curated list of the acts citizens
actually ask about (police, building, school, neighbours, childcare, shop
hours, holidays, data protection, municipal, press). Statutory texts are
official works free of copyright (§ 5 UrhG).

Adapters:
  bayern  — gesetze-bayern.de       /Content/Document/{slug}/true    (whole act)
  nrw     — recht.nrw.de            /lrgv/gesetz/{slug}/             (whole act)
  bravors — bravors.brandenburg.de  /gesetze/{slug}                  (whole act)
  revosax — revosax.sachsen.de      /vorschrift_gesamt/{id}.html     (whole act)

NRW slugs are version-dated (they change when the act is amended); the list
below is current as of 2026-08. Re-check the URL when re-running for updates.
REVOSAX ids come from https://www.revosax.sachsen.de/sitemap.xml (stable per
act); BRAVORS slugs are the lowercased official abbreviations. Both verified
2026-09-01. The remaining 12 Länder run juris SPAs with token-authenticated
internal APIs — those need a headless-browser adapter or a juris agreement.

    cd backend && .venv/bin/python scripts/import_de_landesrecht.py
    ... --region NW            # one Land only

Resumable: (reference, "de") pairs already in the corpus are skipped.
"""
import asyncio
import html as html_mod
import re
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.security import create_access_token  # noqa: E402

API = "http://127.0.0.1:8000/api"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AvokatIM corpus sync (info@avokatiim.ai)"}
DOC_DELAY = 1.5
MIN_CHARS = 800

# UI noise that survives tag-stripping on the portals
_NOISE_LINES = re.compile(
    r"^(Mehr|Paragraph (ausdrucken|kopieren)|Paragraph Link kopieren|Fußnoten|"
    r"Link zu(r| dieser) [^\n]*|"
    r"Dokument (ausdrucken|herunterladen)|Zum Textanfang|Feedback|Drucken)$"
)


def _strip_tags(fragment: str) -> str:
    # a segment sliced mid-tag leaves a leading remnant like '/span>'
    fragment = re.sub(r"\A[^<]*?>", "", fragment)
    fragment = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", fragment)
    fragment = re.sub(r"(?i)<(br|/p|/div|/h\d|/li|/dd|/dt|/tr)[^>]*>", "\n", fragment)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    fragment = html_mod.unescape(fragment)
    lines = []
    for raw in fragment.splitlines():
        line = re.sub(r"[ \t\u00a0]+", " ", raw).strip()
        if line and not _NOISE_LINES.match(line):
            lines.append(line)
    return "\n".join(lines)


# ---------- Bayern (gesetze-bayern.de) ----------

_BY_HEAD_RE = re.compile(
    r'<div class="paraheading">.*?class="absatz paranr">(?P<num>[^<]*)<.*?'
    r'class="absatz paratitel">(?P<title>[^<]*)<',
    re.S,
)


async def fetch_bayern(web: httpx.AsyncClient, slugs: list[str]) -> tuple[str, str] | None:
    """(source_url, text) — first slug candidate that yields a real act."""
    for slug in slugs:
        url = f"https://www.gesetze-bayern.de/Content/Document/{slug}/true"
        r = await web.get(url)
        if r.status_code != 200 or "paraheading" not in r.text:
            continue
        blocks = []
        heads = list(_BY_HEAD_RE.finditer(r.text))
        for i, m in enumerate(heads):
            end = heads[i + 1].start() if i + 1 < len(heads) else len(r.text)
            body = _strip_tags(r.text[m.end():end])
            if not body:
                continue
            heading = f"{m.group('num').strip()} {m.group('title').strip()}"
            blocks.append(f"{heading}\n{body}")
        if blocks:
            return url, "\n\n".join(blocks)
    return None


# ---------- NRW (recht.nrw.de) ----------

# Strict per-block heading: num and headline sit next to each other inside
# one <h2>; a lazy .*? across blocks would misalign sections.
_NRW_HEAD_RE = re.compile(
    r'field--field_num">(?P<num>[^<]*)</span>\s*'
    r'<span class="field field--field_headline">(?P<title>[^<]*)</span>',
    re.S,
)
# The norm text itself (footnotes use field--name-field-footnote-description)
_NRW_TEXT_MARK = 'field--name-field-text'


async def fetch_nrw(web: httpx.AsyncClient, slugs: list[str]) -> tuple[str, str] | None:
    for slug in slugs:
        url = f"https://recht.nrw.de/lrgv/gesetz/{slug}/"
        r = await web.get(url, follow_redirects=True)
        if r.status_code != 200 or "paragraph-header" not in r.text:
            continue
        blocks = []
        heads = list(_NRW_HEAD_RE.finditer(r.text))
        for i, m in enumerate(heads):
            end = heads[i + 1].start() if i + 1 < len(heads) else len(r.text)
            segment = r.text[m.end():end]
            # keep only the norm text: skip the print UI + footnote container
            # before it, cut at the next article wrapper / page footer
            pos = segment.find(_NRW_TEXT_MARK)
            if pos < 0:
                continue
            segment = segment[pos:]
            segment = re.split(
                r'paragraph--type--article|<footer|class="region-footer', segment
            )[0]
            body = _strip_tags(segment)
            if not body:
                continue
            heading = f"{m.group('num').strip()} {m.group('title').strip()}"
            blocks.append(f"{heading}\n{body}")
        if blocks:
            return url, "\n\n".join(blocks)
    return None


# ---------- Brandenburg (bravors.brandenburg.de) ----------

# Body sections: markup varies wildly per act — h3/h4/h6, align="center" or
# class="paragraph_bez", named anchors present or absent. The stable rule:
# a norm heading is any h3–h6 whose text starts with &sect;. Chapter
# headings ("Kapitel 4<br/>Zwang") and the TOC's <p><a href="#N"> links
# never match.
_BRAVORS_HEAD_RE = re.compile(
    r'<h(?P<lvl>[3-6])[^>]*>\s*(?:<a name="[^"]*"[^>]*></a>)?\s*'
    r'(?P<head>&sect;.*?)</h(?P=lvl)>',
    re.S,
)


async def fetch_bravors(web: httpx.AsyncClient, slugs: list[str]) -> tuple[str, str] | None:
    for slug in slugs:
        url = f"https://bravors.brandenburg.de/gesetze/{slug}"
        r = await web.get(url)
        # unknown slugs 302-redirect to the search page
        if r.status_code != 200 or "&sect;" not in r.text:
            continue
        blocks = []
        heads = list(_BRAVORS_HEAD_RE.finditer(r.text))
        for i, m in enumerate(heads):
            end = heads[i + 1].start() if i + 1 < len(heads) else len(r.text)
            body = _strip_tags(r.text[m.end():end])
            if not body:
                continue
            heading = " ".join(_strip_tags(m.group("head")).split())
            blocks.append(f"{heading}\n{body}")
        if blocks:
            return url, "\n\n".join(blocks)
    return None


# ---------- Sachsen (revosax.sachsen.de) ----------

# The whole-act page wraps every norm in
# <section ... title="§ 1  Zweck des Gesetzes"> — the title attribute is the
# cleanest heading source; Abschnitt/Anlage sections come along naturally.
_REVOSAX_SECTION_RE = re.compile(r'<section[^>]*\btitle="(?P<title>[^"]+)"[^>]*>')


async def fetch_revosax(web: httpx.AsyncClient, ids: list[str]) -> tuple[str, str] | None:
    for vid in ids:
        url = f"https://www.revosax.sachsen.de/vorschrift_gesamt/{vid}.html"
        r = await web.get(url)
        if r.status_code != 200 or "<section" not in r.text:
            continue
        blocks = []
        heads = list(_REVOSAX_SECTION_RE.finditer(r.text))
        for i, m in enumerate(heads):
            end = heads[i + 1].start() if i + 1 < len(heads) else len(r.text)
            segment = re.split(r"</section>", r.text[m.end():end])[0]
            body = _strip_tags(segment)
            if not body:
                continue
            heading = html_mod.unescape(" ".join(m.group("title").split()))
            # the heading repeats as the first lines of the body — keep both,
            # chunking uses the heading line for `section` detection
            blocks.append(f"{heading}\n{body}")
        if blocks:
            return url, "\n\n".join(blocks)
    return None


# ---------- curated acts ----------
# (region, reference, title, adapter, slug candidates)
ACTS = [
    # Nordrhein-Westfalen — recht.nrw.de (dated slugs, current 2026-08)
    ("NW", "PolG NRW", "Polizeigesetz des Landes Nordrhein-Westfalen", "nrw",
     ["13122025-polizeigesetz-des-landes-nordrhein-westfalen-bekanntmachung-der-neufassung"]),
    ("NW", "BauO NRW 2018", "Bauordnung für das Land Nordrhein-Westfalen (Landesbauordnung 2018)", "nrw",
     ["01012024-bauordnung-fuer-das-land-nordrhein-westfalen-landesbauordnung-2018-bauo-nrw"]),
    ("NW", "SchulG NRW", "Schulgesetz für das Land Nordrhein-Westfalen", "nrw",
     ["01082025-schulgesetz-fuer-das-land-nordrhein-westfalen-schulgesetz-nrw-schulg"]),
    ("NW", "NachbG NRW", "Nachbarrechtsgesetz Nordrhein-Westfalen", "nrw",
     ["29122021-nachbarrechtsgesetz-nachbg-nrw"]),
    ("NW", "KiBiz NRW", "Gesetz zur frühen Bildung und Förderung von Kindern (Kinderbildungsgesetz)", "nrw",
     ["01082022-gesetz-zur-fruehen-bildung-und-foerderung-von-kindern-kinderbildungsgesetz"]),
    ("NW", "LÖG NRW", "Gesetz zur Regelung der Ladenöffnungszeiten (Ladenöffnungsgesetz)", "nrw",
     ["30032018-gesetz-zur-regelung-der-ladenoeffnungszeiten-ladenoeffnungsgesetz-loeg-nrw"]),
    ("NW", "FTG NW", "Gesetz über die Sonn- und Feiertage (Feiertagsgesetz NW)", "nrw",
     ["01012000-bekanntmachung-der-neufassung-des-gesetzes-ueber-die-sonn-und-feiertage"]),
    ("NW", "DSG NRW", "Datenschutzgesetz Nordrhein-Westfalen", "nrw",
     ["01042026-datenschutzgesetz-nordrhein-westfalen",
      "25052018-datenschutzgesetz-nordrhein-westfalen-dsg-nrw"]),
    ("NW", "GO NRW", "Gemeindeordnung für das Land Nordrhein-Westfalen", "nrw",
     ["01012026-gemeindeordnung-fuer-das-land-nordrhein-westfalen-bekanntmachung-der-neufassung",
      "01112025-gemeindeordnung-fuer-das-land-nordrhein-westfalen-go-nrw-bekanntmachung-der"]),
    ("NW", "LPresseG NRW", "Pressegesetz für das Land Nordrhein-Westfalen (Landespressegesetz)", "nrw",
     ["18052021-pressegesetz-fuer-das-land-nordrhein-westfalen-landespressegesetz-nrw"]),
    # Bayern — gesetze-bayern.de (stable BayRS abbreviations)
    ("BY", "PAG", "Gesetz über die Aufgaben und Befugnisse der Bayerischen Staatlichen Polizei (Polizeiaufgabengesetz)", "bayern",
     ["BayPAG", "PAG"]),
    ("BY", "BayBO", "Bayerische Bauordnung", "bayern", ["BayBO"]),
    ("BY", "BayEUG", "Bayerisches Gesetz über das Erziehungs- und Unterrichtswesen", "bayern",
     ["BayEUG"]),
    ("BY", "AGBGB Bayern", "Gesetz zur Ausführung des Bürgerlichen Gesetzbuchs (u.a. Nachbarrecht, Art. 43 ff.)", "bayern",
     ["AGBGB", "BayAGBGB"]),
    ("BY", "BayKiBiG", "Bayerisches Kinderbildungs- und -betreuungsgesetz", "bayern",
     ["BayKiBiG"]),
    ("BY", "FTG Bayern", "Gesetz über den Schutz der Sonn- und Feiertage (Feiertagsgesetz)", "bayern",
     ["FTG", "BayFTG"]),
    ("BY", "BayDSG", "Bayerisches Datenschutzgesetz", "bayern", ["BayDSG"]),
    ("BY", "GO Bayern", "Gemeindeordnung für den Freistaat Bayern", "bayern",
     ["GO", "BayGO"]),
    ("BY", "BayPrG", "Bayerisches Pressegesetz", "bayern", ["BayPrG"]),
    ("BY", "LStVG", "Landesstraf- und Verordnungsgesetz (öffentliche Sicherheit und Ordnung)", "bayern",
     ["BayLStVG", "LStVG"]),
    # Brandenburg — bravors.brandenburg.de (lowercased abbreviations, verified 2026-09-01)
    ("BB", "BbgPolG", "Brandenburgisches Polizeigesetz", "bravors", ["bbgpolg"]),
    ("BB", "BbgBO", "Brandenburgische Bauordnung", "bravors", ["bbgbo"]),
    ("BB", "BbgSchulG", "Gesetz über die Schulen im Land Brandenburg (Brandenburgisches Schulgesetz)", "bravors",
     ["bbgschulg"]),
    ("BB", "KitaG Bbg", "Kindertagesstättengesetz (Brandenburg)", "bravors", ["kitag"]),
    ("BB", "BbgDSG", "Brandenburgisches Datenschutzgesetz", "bravors", ["bbgdsg"]),
    ("BB", "BbgKVerf", "Kommunalverfassung des Landes Brandenburg", "bravors", ["bbgkverf"]),
    ("BB", "BbgPG", "Pressegesetz des Landes Brandenburg (Landespressegesetz)", "bravors", ["bbgpg"]),
    ("BB", "BbgLöG", "Brandenburgisches Ladenöffnungsgesetz", "bravors", ["bbgloeg"]),
    ("BB", "BbgStrG", "Brandenburgisches Straßengesetz", "bravors", ["bbgstrg"]),
    # Sachsen — revosax.sachsen.de (stable sitemap ids, verified 2026-09-01)
    ("SN", "SächsPVDG", "Sächsisches Polizeivollzugsdienstgesetz", "revosax", ["18193"]),
    ("SN", "SächsBO", "Sächsische Bauordnung", "revosax", ["1779"]),
    ("SN", "SächsSchulG", "Sächsisches Schulgesetz", "revosax", ["4192"]),
    ("SN", "SächsKitaG", "Gesetz über Kindertagesbetreuung (Sachsen)", "revosax", ["1079"]),
    ("SN", "SächsLadÖffG", "Sächsisches Ladenöffnungsgesetz", "revosax", ["11548"]),
    ("SN", "SächsSFG", "Gesetz über Sonn- und Feiertage im Freistaat Sachsen", "revosax", ["3997"]),
    ("SN", "SächsDSUG", "Sächsisches Datenschutz-Umsetzungsgesetz", "revosax", ["18195"]),
    ("SN", "SächsGemO", "Sächsische Gemeindeordnung", "revosax", ["2754"]),
    ("SN", "SächsPresseG", "Sächsisches Pressegesetz", "revosax", ["4197"]),
    ("SN", "SächsStrG", "Sächsisches Straßengesetz", "revosax", ["4785"]),
]

FETCHERS = {
    "bayern": fetch_bayern,
    "nrw": fetch_nrw,
    "bravors": fetch_bravors,
    "revosax": fetch_revosax,
}


async def _api_token() -> str:
    async with SessionLocal() as db:
        owner = (
            await db.execute(select(User).where(User.role == "admin").limit(1))
        ).scalars().first()
        return create_access_token(str(owner.id), str(owner.tenant_id))


async def main(only_region: str | None = None) -> None:
    token = await _api_token()
    stats = {"ok": 0, "skip": 0, "fail": 0}
    acts = [a for a in ACTS if only_region is None or a[0] == only_region]
    async with httpx.AsyncClient(timeout=180, headers=UA, follow_redirects=True) as web, \
            httpx.AsyncClient(timeout=1800, headers={"Authorization": f"Bearer {token}"}) as api:
        existing = {
            d.get("reference")
            for d in (await api.get(f"{API}/corpus?jurisdiction_code=DE")).json()
        }
        total = len(acts)
        for i, (region, reference, title, adapter, slugs) in enumerate(acts, 1):
            if reference in existing:
                stats["skip"] += 1
                continue
            try:
                fetched = await FETCHERS[adapter](web, slugs)
            except Exception as exc:  # noqa: BLE001 — log and continue the batch
                print(f"[{i}/{total}] FAIL {reference}: {exc}", flush=True)
                stats["fail"] += 1
                continue
            if fetched is None:
                print(f"[{i}/{total}] FAIL {reference}: no slug candidate worked", flush=True)
                stats["fail"] += 1
                continue
            source_url, text = fetched
            if len(text) < MIN_CHARS:
                print(f"[{i}/{total}] FAIL {reference}: only {len(text)} chars", flush=True)
                stats["fail"] += 1
                continue
            resp = await api.post(f"{API}/corpus", json={
                "jurisdiction_code": "DE",
                "title": title[:500],
                "doc_type": "law",
                "reference": reference,
                "source_url": source_url,
                "language": "de",
                "region": region,
                "text": text,
            })
            if resp.status_code == 201:
                stats["ok"] += 1
                existing.add(reference)
                print(f"[{i}/{total}] OK   [{region}] {reference} "
                      f"({resp.json()['chunk_count']} chunks)", flush=True)
            else:
                stats["fail"] += 1
                print(f"[{i}/{total}] ERR  {reference} {resp.status_code}: "
                      f"{resp.text[:150]}", flush=True)
            await asyncio.sleep(DOC_DELAY)

    print(f"\nLandesrecht: ok={stats['ok']} skip={stats['skip']} fail={stats['fail']}")


if __name__ == "__main__":
    region = None
    if "--region" in sys.argv:
        region = sys.argv[sys.argv.index("--region") + 1].upper()
    asyncio.run(main(region))
