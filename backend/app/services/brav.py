"""Client for the BRAV public search (bravsearch.bea-brak.de).

The Bundesweites Amtliche Anwaltsverzeichnis has no API: it is a JSF/
PrimeFaces application. The flow that works (verified by hand):

1. GET /bravsearch/index.brak with a browser-like User-Agent (the portal
   answers 503 to non-browser agents) -> JSESSIONID cookie + a
   ``jakarta.faces.ViewState`` hidden field.
2. POST /bravsearch/index.xhtml as a PrimeFaces partial-ajax request with
   the search form fields and the ViewState.
3. The XML partial-response contains an ``<update id="mainPageContent">``
   CDATA block with result cards (name, profession, Kanzlei, address) and
   the total count ("Anzahl gefundener Einträge: N"), or a
   "Kein Suchergebnis" dialog when nothing matched.

The portal is known to be flaky (beA outages answer 503 on everything), so
every network problem degrades to ``None`` — callers must treat that as
"registry unavailable", never as "lawyer not found".
"""
import html
import logging
import re
import unicodedata
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

BRAV_BASE = "https://bravsearch.bea-brak.de/bravsearch"
# The portal rejects non-browser user agents with 503.
BRAV_UA = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
)
# One result page shows at most 6 cards; more results need JSF pagination,
# which we deliberately do not implement (>6 namesakes can never auto-verify
# anyway, see license_verify).
BRAV_PAGE_SIZE = 6

_VIEWSTATE_RE = re.compile(
    r'name="(?:jakarta|javax)\.faces\.ViewState"[^>]*value="([^"]+)"'
)
_COUNT_RE = re.compile(r"Anzahl gefundener Eintr(?:&auml;|ä)ge:\s*(\d+)")
_CARD_RE = re.compile(
    r'resultCardHeader ui-helper-clearfix">\s*(?P<header>[^<]+?)\s*</span>'
    r".*?<ul>(?P<items>.*?)</ul>",
    re.S,
)
_LI_RE = re.compile(r"<li>\s*(.*?)\s*</li>", re.S)
_PLZ_CITY_RE = re.compile(r"^(\d{5})\s+(.+)$")

# Academic/professional prefixes that BRAV mixes into the first-name part
# of the card header ("Meyer, Dr. Thomas") and lawyers mix into signups.
_TITLE_TOKENS = {
    "dr", "dr.", "prof", "prof.", "mag", "mag.", "dipl.-jur",
    "ll.m", "ll.m.", "llm", "mba", "b.sc", "m.sc", "jur", "jur.",
    "(fh)", "h.c", "h.c.", "med", "med.", "iur", "iur.", "rer", "rer.",
    "pol", "pol.", "nat", "nat.", "habil", "habil.",
}


@dataclass
class BravEntry:
    """One result card of the BRAV list view."""

    last_name: str
    first_name: str
    profession: str  # Rechtsanwalt / Rechtsanwältin / Syndikus... / notes
    office: str = ""  # Kanzlei name when the card shows one
    street: str = ""
    postal_code: str = ""
    city: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def describe(self) -> str:
        parts = [self.full_name, self.profession]
        if self.office:
            parts.append(self.office)
        if self.city:
            parts.append(self.city)
        return ", ".join(p for p in parts if p)


@dataclass
class BravResult:
    total: int
    entries: list[BravEntry] = field(default_factory=list)

    @property
    def truncated(self) -> bool:
        """True when the portal has more results than the first page."""
        return self.total > len(self.entries)


def normalize_de_name(name: str) -> str:
    """Canonical form for German name comparison: lowercase, academic
    titles removed, umlauts folded to their two-letter form (ü -> ue),
    other diacritics stripped."""
    s = (name or "").lower()
    s = (
        s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
        .replace("ß", "ss")
    )
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    tokens = [t for t in re.split(r"[\s,]+", s) if t and t not in _TITLE_TOKENS]
    return " ".join(tokens)


def _name_key_variants(name: str) -> set[str]:
    """Two canonical spellings so 'Mueller' matches 'Müller' but also a
    signup typed without the e ('Muller')."""
    norm = normalize_de_name(name)
    simple = norm.replace("ae", "a").replace("oe", "o").replace("ue", "u")
    return {norm, simple}


def de_names_match(a: str, b: str) -> bool:
    """Order-insensitive full-name equality with umlaut/title tolerance."""
    va = {" ".join(sorted(v.split())) for v in _name_key_variants(a)}
    vb = {" ".join(sorted(v.split())) for v in _name_key_variants(b)}
    return bool(va & vb) and bool(normalize_de_name(a))


def _clean(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", fragment)).strip()


def parse_search_response(xml_text: str) -> BravResult | None:
    """Parse the PrimeFaces partial-response of a BRAV search.

    Returns a BravResult (total may be 0) or None when the payload does not
    look like either a result list or a clean "no result" answer.
    """
    if "Kein Suchergebnis" in xml_text or "lieferte kein Ergebnis" in xml_text:
        return BravResult(total=0)

    count_m = _COUNT_RE.search(xml_text)
    if count_m is None:
        return None
    entries: list[BravEntry] = []
    for m in _CARD_RE.finditer(xml_text):
        header = html.unescape(m.group("header")).strip()
        last_name, _, first_name = header.partition(",")
        items = [_clean(li) for li in _LI_RE.findall(m.group("items"))]
        items = [i for i in items if i]
        profession = items[0] if items else ""
        street = postal = city = office = ""
        rest = items[1:]
        if rest:
            plz_m = _PLZ_CITY_RE.match(rest[-1])
            if plz_m:
                postal, city = plz_m.group(1), plz_m.group(2)
                rest = rest[:-1]
            if rest:
                street = rest[-1]
                rest = rest[:-1]
            if rest:
                office = " / ".join(rest)
        entries.append(
            BravEntry(
                last_name=last_name.strip(),
                first_name=first_name.strip(),
                profession=profession,
                office=office,
                street=street,
                postal_code=postal,
                city=city,
            )
        )
    return BravResult(total=int(count_m.group(1)), entries=entries)


async def search_brav(
    last_name: str,
    first_name: str = "",
    city: str = "",
    timeout: float = 15.0,
) -> BravResult | None:
    """Search the BRAV portal. Returns None whenever the portal cannot be
    reached or answers something unexpected (it is regularly down)."""
    headers = {"User-Agent": BRAV_UA}
    try:
        async with httpx.AsyncClient(
            base_url=BRAV_BASE, headers=headers, timeout=timeout,
            follow_redirects=True,
        ) as client:
            start = await client.get("/index.brak")
            if start.status_code != 200:
                logger.warning("BRAV portal answered %s", start.status_code)
                return None
            vs_m = _VIEWSTATE_RE.search(start.text)
            if vs_m is None:
                logger.warning("BRAV start page had no JSF ViewState")
                return None
            form = {
                "jakarta.faces.partial.ajax": "true",
                "jakarta.faces.source": "searchForm:cmdSearch",
                "jakarta.faces.partial.execute": "@all",
                "jakarta.faces.partial.render": "mainPageContent",
                "searchForm:cmdSearch": "searchForm:cmdSearch",
                "searchForm": "searchForm",
                "searchForm:ddLanguage_input": "de",
                "searchForm:ddAnrede_input": "",
                "searchForm:ddTitel_input": "",
                "searchForm:txtName": last_name or "",
                "searchForm:txtVorname": first_name or "",
                "searchForm:txtProfTitle": "",
                "searchForm:txtSpecialization_input": "",
                "searchForm:txtOfficeName": "",
                "searchForm:txtStrasse": "",
                "searchForm:txtPostal": "",
                "searchForm:txtOrt": city or "",
                "searchForm:ddRAKammer_input": "",
                "jakarta.faces.ViewState": vs_m.group(1),
            }
            resp = await client.post(
                "/index.xhtml",
                data=form,
                headers={
                    "Faces-Request": "partial/ajax",
                    "X-Requested-With": "XMLHttpRequest",
                },
            )
            if resp.status_code != 200:
                logger.warning("BRAV search answered %s", resp.status_code)
                return None
            result = parse_search_response(resp.text)
            if result is None:
                logger.warning("BRAV search response was not parseable")
            return result
    except httpx.HTTPError as exc:
        logger.warning("BRAV portal unreachable: %r", exc)
        return None
