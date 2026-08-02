"""Jurisdiction profiles — per-country product configuration as data (D-034).

AGENTS.md hard rule #4 keeps jurisdiction *rules* (deadlines, holidays,
templates, tariffs, corpus) in the database. This module is the code-side
complement: one small declarative profile per country the platform operates
in, so services never hardcode "XK"/Kosovo assumptions again.

Resolution order for "which country am I serving?":
  1. Public endpoints: the request Host header (de.avokatiim.ai -> DE),
     forwarded by the Next.js proxy as x-avokatim-country.
  2. Authenticated tenant paths: Tenant.country.
  3. Fallback: DEFAULT_COUNTRY (XK).
"""
from dataclasses import dataclass, field

DEFAULT_COUNTRY = "XK"


@dataclass(frozen=True)
class JurisdictionProfile:
    code: str  # == Jurisdiction.code in the DB
    # Trading name of the platform on this country's host (D-056: the DE
    # host is rebranded "Ava Legal"; Kosovo keeps "AvokatIM"). Used in
    # emails, SMS and PDFs whenever the recipient's country is known.
    brand_name: str
    currency: str  # ISO 4217
    vat_rate: int  # standard VAT %, default for new tenant invoices
    timezone: str  # IANA name, used for booking slots / deadline "today"
    phone_prefix: str  # UX hint for phone inputs
    default_locale: str
    locales: tuple[str, ...]  # locales offered on this country's public host
    # Lawyer chamber registry used for license verification:
    #   "oak"  — Kosovo Bar Association (scraped CSV with emails; email match
    #            auto-verifies, see services/license_verify.py)
    #   "brav" — Germany's Bundesweites Amtliches Anwaltsverzeichnis (public
    #            lookup, no emails; name+chamber lookup + one-click approval)
    bar_registry: str
    bar_name: str  # short display name of the chamber
    # Feature switches for the public product on this country's host.
    # SOS and the notary pillar are Kosovo-tailored v1 features; they stay
    # off for DE until they get their own legal review (plan D-034 phase 2+).
    sos_enabled: bool = True
    notary_enabled: bool = True
    # Language the legal corpus is complete in — RAG falls back to this when
    # the user's locale has no translated corpus (services/rag.py).
    corpus_fallback_language: str = "sq"
    # Optional LLM provider override for this country's requests (GDPR: EU
    # traffic should use an EU provider). None = router default.
    llm_provider: str | None = None
    # City suggestions for onboarding/settings/case forms (free text remains
    # allowed — these only feed the UI datalist).
    cities: tuple[str, ...] = field(default=())
    # Public hostname serving this country; None = the main product host
    # (settings.public_base_url). Used to build absolute links (emails,
    # OAuth returns) that must land on the right country's site.
    public_host: str | None = None
    # Sub-national units (DE: the 16 Bundesländer, ISO 3166-2 codes without
    # the "DE-" prefix). Empty = the country has no regional law dimension.
    # Regional holidays and Landesrecht corpus docs carry these codes in
    # their `region` column; NULL there means nation-wide/federal.
    regions: dict[str, str] = field(default_factory=dict)
    # Default region per city (lowercased key) — a UX prefill only, the
    # user-picked region is always the source of truth.
    city_regions: dict[str, str] = field(default_factory=dict)


PROFILES: dict[str, JurisdictionProfile] = {
    "XK": JurisdictionProfile(
        code="XK",
        brand_name="AvokatIM",
        currency="EUR",
        vat_rate=18,
        timezone="Europe/Belgrade",
        phone_prefix="+383",
        default_locale="sq",
        locales=("sq", "sr", "tr", "bs", "en", "zh"),
        bar_registry="oak",
        bar_name="OAK",
        sos_enabled=True,
        notary_enabled=True,
        corpus_fallback_language="sq",
        cities=(
            "Prishtinë", "Prizren", "Pejë", "Gjakovë", "Mitrovicë",
            "Ferizaj", "Gjilan", "Vushtrri", "Podujevë", "Suharekë",
        ),
    ),
    "DE": JurisdictionProfile(
        code="DE",
        brand_name="Ava Legal",
        currency="EUR",
        vat_rate=19,
        timezone="Europe/Berlin",
        phone_prefix="+49",
        default_locale="de",
        locales=("de", "en", "tr"),
        bar_registry="brav",
        bar_name="BRAK/BRAV",
        sos_enabled=False,
        notary_enabled=False,
        corpus_fallback_language="de",
        # TEMPORARY (owner request 2026-08-01): DeepSeek for the full-feature
        # demo — the local model (Ollama gemma3:27b, D-037 phase 5) stays
        # installed and validated; set back to "local" before public launch
        # (DE-LAUNCH-GATE item 3 requires it).
        llm_provider=None,
        cities=(
            "Berlin", "Hamburg", "München", "Köln", "Frankfurt am Main",
            "Stuttgart", "Düsseldorf", "Leipzig", "Dortmund", "Essen",
        ),
        public_host="de.avokatiim.ai",
        regions={
            "BW": "Baden-Württemberg",
            "BY": "Bayern",
            "BE": "Berlin",
            "BB": "Brandenburg",
            "HB": "Bremen",
            "HH": "Hamburg",
            "HE": "Hessen",
            "MV": "Mecklenburg-Vorpommern",
            "NI": "Niedersachsen",
            "NW": "Nordrhein-Westfalen",
            "RP": "Rheinland-Pfalz",
            "SL": "Saarland",
            "SN": "Sachsen",
            "ST": "Sachsen-Anhalt",
            "SH": "Schleswig-Holstein",
            "TH": "Thüringen",
        },
        city_regions={
            "berlin": "BE", "hamburg": "HH", "münchen": "BY", "köln": "NW",
            "frankfurt am main": "HE", "frankfurt": "HE", "stuttgart": "BW",
            "düsseldorf": "NW", "leipzig": "SN", "dortmund": "NW",
            "essen": "NW", "bremen": "HB", "dresden": "SN", "hannover": "NI",
            "nürnberg": "BY", "duisburg": "NW", "bochum": "NW",
            "wuppertal": "NW", "bielefeld": "NW", "bonn": "NW",
            "münster": "NW", "mannheim": "BW", "karlsruhe": "BW",
            "augsburg": "BY", "wiesbaden": "HE", "mönchengladbach": "NW",
            "gelsenkirchen": "NW", "aachen": "NW", "braunschweig": "NI",
            "kiel": "SH", "chemnitz": "SN", "magdeburg": "ST",
            "freiburg im breisgau": "BW", "freiburg": "BW", "krefeld": "NW",
            "mainz": "RP", "lübeck": "SH", "erfurt": "TH",
            "oberhausen": "NW", "rostock": "MV", "kassel": "HE",
            "potsdam": "BB", "saarbrücken": "SL", "halle (saale)": "ST",
            "regensburg": "BY", "würzburg": "BY", "ulm": "BW",
            "heidelberg": "BW", "osnabrück": "NI", "oldenburg": "NI",
        },
    ),
}

# Public hostnames -> country. Anything unlisted (localhost, LAN IPs, the
# main domain) resolves to DEFAULT_COUNTRY.
HOST_COUNTRY: dict[str, str] = {
    "de.avokatiim.ai": "DE",
}


def profile_for(country: str | None) -> JurisdictionProfile:
    return PROFILES.get((country or "").upper(), PROFILES[DEFAULT_COUNTRY])


def country_for_host(host: str | None) -> str:
    return HOST_COUNTRY.get((host or "").split(":")[0].lower(), DEFAULT_COUNTRY)


def country_for_phone(phone: str | None) -> str:
    """Country inferred from an international phone number (WhatsApp sender:
    digits only, no '+'). Longest matching profile prefix wins; anything
    unknown falls back to the default country."""
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    best, best_len = DEFAULT_COUNTRY, 0
    for code, profile in PROFILES.items():
        prefix = profile.phone_prefix.lstrip("+")
        if digits.startswith(prefix) and len(prefix) > best_len:
            best, best_len = code, len(prefix)
    return best


def is_valid_country(country: str | None) -> bool:
    return (country or "").upper() in PROFILES


def is_valid_region(country: str | None, region: str | None) -> bool:
    return (region or "").upper() in profile_for(country).regions


def region_for_city(country: str | None, city: str | None) -> str | None:
    """Best-effort region prefill from a free-text city name."""
    return profile_for(country).city_regions.get((city or "").strip().lower())


def public_base_url_for(country: str) -> str:
    """Absolute base URL of the public site for a country — the main
    public_base_url unless the profile pins its own hostname (and the
    deployment is actually on the public domain, not localhost/LAN)."""
    from app.config import settings

    host = profile_for(country).public_host
    if host and "avokatiim.ai" in settings.public_base_url:
        return f"https://{host}"
    return settings.public_base_url


async def jurisdiction_row_for_tenant(db, tenant_id):
    """The tenant's Jurisdiction DB row (default_jurisdiction_code), falling
    back to the platform default when the code has no seeded row."""
    from sqlalchemy import select

    from app.models import Jurisdiction, Tenant

    tenant = await db.get(Tenant, tenant_id)
    code = (tenant.default_jurisdiction_code if tenant else None) or DEFAULT_COUNTRY
    row = (
        await db.execute(select(Jurisdiction).where(Jurisdiction.code == code))
    ).scalar_one_or_none()
    if row is None:
        row = (
            await db.execute(
                select(Jurisdiction).where(Jurisdiction.code == DEFAULT_COUNTRY)
            )
        ).scalar_one()
    return row


def country_from_request(request) -> str:
    """Country a public request is addressed to. Prefers the header the
    Next.js proxy derives from the public hostname; falls back to Host for
    direct backend access (curl, tests). Never trusted for tenant data —
    authenticated paths use Tenant.country instead."""
    hdr = request.headers.get("x-avokatim-country")
    if hdr and is_valid_country(hdr):
        return hdr.upper()
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    return country_for_host(host)
