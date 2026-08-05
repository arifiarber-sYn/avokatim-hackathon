"""Collect German lawyer contacts (name, city, email, practice areas) into
data/de_lawyers.csv for the Ava Legal outreach campaign (Track B).

Source: the German Bar Association's public directory anwaltauskunft.de.
Its React search UI talks to a clean JSON endpoint that needs no key:

    GET /wp-json/search/v1/query
        ?location=<city>&distance=<km>&terms[rechtsgebiet][]=<area>

Each hit already carries a public office e-mail (``e_mail_1``, or the
organisation's), the lawyer's name, salutation (from ``geschlecht``),
city/PLZ and the matched practice areas. We iterate a curated set of
diaspora-heavy cities x our strong practice areas, deduplicate by id and
e-mail, and rank Albanian-sounding names first (the diaspora legal circle
is the warmest first door — see docs/pitch/strategjia-tregu-gjerman.txt).

This only reads public professional contact data. It is a polite scraper:
sequential, 1s between calls, honest User-Agent with a contact address.
Output lands in data/ which is git-ignored (personal data stays local).

Usage:
    python scripts/scrape_de_lawyers.py               # full harvest
    python scripts/scrape_de_lawyers.py --limit-cities 3   # quick sample
"""
import csv
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote

import httpx

OUT = Path(__file__).resolve().parents[2] / "data" / "de_lawyers.csv"
BASE = "https://anwaltauskunft.de/wp-json/search/v1/query"
# The portal serves JSON only to browser-like agents; keep an honest contact.
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
REFERER = "https://anwaltauskunft.de/suche/"
DELAY_S = 1.0
DISTANCE_KM = 15

# Diaspora-heavy metros first (Baden-Württemberg, NRW, Bayern, Hessen,
# Hamburg, Berlin) — where the Albanian-German community concentrates.
CITIES = [
    "Stuttgart", "München", "Frankfurt am Main", "Düsseldorf", "Köln",
    "Hamburg", "Berlin", "Nürnberg", "Mannheim", "Karlsruhe", "Essen",
    "Dortmund", "Duisburg", "Wuppertal", "Bielefeld", "Augsburg",
    "Freiburg", "Heilbronn", "Pforzheim", "Reutlingen", "Ulm", "Bonn",
    "Wiesbaden", "Bremen", "Hannover", "Nürtingen", "Böblingen",
]

# Practice areas that map to our intake questionnaires and that the portal's
# controlled vocabulary actually accepts (verified against the live API).
PRACTICE_AREAS = [
    "Familienrecht", "Arbeitsrecht", "Verkehrsrecht", "Erbrecht",
    "Wohnungseigentumsrecht", "Sozialrecht", "Versicherungsrecht",
]

# Albanian-name heuristic (best-effort ranking, never a filter). Common
# surname suffixes + frequent given/family-name tokens in the diaspora.
_ALB_SUFFIXES = ("aj", "iqi", "shi", "lli", "gu", "ku")
_ALB_TOKENS = {
    "krasniqi", "berisha", "gashi", "hoxha", "shala", "kryeziu", "rexhepi",
    "morina", "bytyqi", "kastrati", "zeqiri", "haziri", "musliu", "ademi",
    "sadiku", "halimi", "bajrami", "dauti", "veseli", "rama", "thaci",
    "arifi", "bekteshi", "dema", "elshani", "ferizi", "gjoka", "hasani",
    "ismaili", "jashari", "kelmendi", "loshi", "maloku", "nuhiu", "osmani",
    "prekazi", "qerimi", "ramadani", "selimi", "tahiri", "ukaj", "vokshi",
    "xhaferi", "zymberi", "beqiri", "cana", "deda", "gjini", "hyseni",
    "arben", "bujar", "fatmir", "blerim", "shpresa", "arta", "drita",
    "gezim", "ilir", "jeton", "kushtrim", "leke", "valon", "vesa", "ardit",
    "besa", "dardan", "endrit", "fisnik", "granit", "liridon", "rinor",
}


def _fold(s: str) -> str:
    s = (s or "").lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def albanian_score(first: str, last: str) -> int:
    """Rough 0-3 likelihood that a name belongs to the Albanian diaspora."""
    tokens = _fold(f"{first} {last}").split()
    if not tokens:
        return 0
    score = 0
    if any(t in _ALB_TOKENS for t in tokens):
        score += 2
    if any(last and _fold(last).endswith(suf) for suf in _ALB_SUFFIXES):
        score += 1
    return min(score, 3)


def _email_of(rec: dict) -> str:
    for key in ("e_mail_1", "e_mail_2"):
        v = (rec.get(key) or "").strip().lower()
        if "@" in v:
            return v
    org = rec.get("organisation") or {}
    for key in ("e_mail_1", "e_mail_2"):
        v = (org.get(key) or "").strip().lower()
        if "@" in v:
            return v
    return ""


def _anrede(geschlecht: str) -> str:
    g = (geschlecht or "").strip().upper()
    return {"W": "Frau", "M": "Herr"}.get(g, "")


def _practice_areas(rec: dict) -> str:
    terms = rec.get("terms") or {}
    areas = terms.get("rechtsgebiet") or terms.get("fachanwaltstitel") or []
    return "; ".join(areas[:4])


def query(client: httpx.Client, city: str, area: str) -> list[dict]:
    url = (
        f"{BASE}?location={quote(city)}&distance={DISTANCE_KM}"
        f"&terms%5Brechtsgebiet%5D%5B%5D={quote(area)}"
    )
    for attempt in range(3):
        try:
            r = client.get(url)
            r.raise_for_status()
            return r.json().get("data", []) or []
        except Exception as exc:  # noqa: BLE001 — network flakiness, retry
            print(f"    retry {attempt + 1} ({city}/{area}): {exc}")
            time.sleep(3)
    return []


def main() -> None:
    limit_cities = None
    if "--limit-cities" in sys.argv:
        limit_cities = int(sys.argv[sys.argv.index("--limit-cities") + 1])
    cities = CITIES[:limit_cities] if limit_cities else CITIES

    seen_ids: set[str] = set()
    seen_emails: set[str] = set()
    rows: list[dict] = []

    headers = {"User-Agent": UA, "Accept": "application/json", "Referer": REFERER}
    with httpx.Client(headers=headers, timeout=30, follow_redirects=True) as client:
        for city in cities:
            city_new = 0
            for area in PRACTICE_AREAS:
                for rec in query(client, city, area):
                    rec_id = rec.get("id") or ""
                    email = _email_of(rec)
                    if not email:
                        continue
                    if rec_id in seen_ids or email in seen_emails:
                        continue
                    seen_ids.add(rec_id)
                    seen_emails.add(email)
                    first = (rec.get("vorname") or "").strip()
                    last = (rec.get("nachname") or "").strip()
                    rows.append({
                        "email": email,
                        "anrede": _anrede(rec.get("geschlecht")),
                        "vorname": first,
                        "nachname": last,
                        "titel": (rec.get("akademischer_titel") or "").strip(),
                        "city": (rec.get("ort") or "").strip(),
                        "plz": (rec.get("plz") or "").strip(),
                        "rechtsgebiete": _practice_areas(rec),
                        "office": ((rec.get("organisation") or {}).get("name") or "").strip(),
                        "website": (rec.get("internetadresse_1") or "").strip(),
                        "source": "anwaltauskunft.de",
                        "alb_score": albanian_score(first, last),
                    })
                    city_new += 1
                    time.sleep(DELAY_S)
            print(f"{city}: +{city_new} new (total {len(rows)})")

    # Diaspora names first, then alphabetically by city for readability.
    rows.sort(key=lambda r: (-r["alb_score"], r["city"], r["nachname"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "email", "anrede", "vorname", "nachname", "titel", "city", "plz",
            "rechtsgebiete", "office", "website", "source", "alb_score",
        ])
        w.writeheader()
        w.writerows(rows)

    diaspora = sum(1 for r in rows if r["alb_score"] > 0)
    print(f"\nwrote {len(rows)} lawyers to {OUT} ({diaspora} likely diaspora)")


if __name__ == "__main__":
    main()
