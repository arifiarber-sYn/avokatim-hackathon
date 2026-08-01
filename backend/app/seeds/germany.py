"""Germany (DE) jurisdiction data — D-034. Data, not code (AGENTS.md §5.4).

Scope:
- Holidays: the nine nationwide ones (region=None) plus each Bundesland's
  own via `Holiday.region` (D-035) — court deadlines legally depend on the
  Land's holidays (§ 222 ZPO -> §§ 187 ff. BGB). Only whole-Land holidays
  are seeded; municipal/partial ones are omitted (conservative for
  deadline math, see de_holidays).
- Month-based statutory deadlines (ZPO/VwGO/AO "1 Monat") use exact
  calendar-month math (day_type="months", §§ 187-188 BGB): same day number
  in the target month, or its last day when that day is missing.
- Initial RVG anchors, not the full Vergütungsverzeichnis.
"""
from datetime import date, timedelta


def _easter(year: int) -> date:
    """Gregorian Easter Sunday (Anonymous/Meeus algorithm)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    length = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * length) // 451
    month, day = divmod(h + length - 7 * m + 114, 31)
    return date(year, month, day + 1)


def _buss_und_bettag(year: int) -> date:
    """The Wednesday before November 23 (Saxony's Feiertagsgesetz § 1)."""
    d = date(year, 11, 22)
    while d.weekday() != 2:
        d -= timedelta(days=1)
    return d


def de_holidays(year: int) -> list[tuple[date, dict, str | None]]:
    """German public holidays for a year: the nine nationwide ones
    (region=None) plus each Bundesland's own (region = NW/BY/…)."""
    easter = _easter(year)
    out: list[tuple[date, dict, str | None]] = [
        (date(year, 1, 1), {"de": "Neujahr", "en": "New Year", "sq": "Viti i Ri"}, None),
        (easter - timedelta(days=2), {"de": "Karfreitag", "en": "Good Friday", "sq": "E Premtja e Zezë"}, None),
        (easter + timedelta(days=1), {"de": "Ostermontag", "en": "Easter Monday", "sq": "E Hëna e Pashkëve"}, None),
        (date(year, 5, 1), {"de": "Tag der Arbeit", "en": "Labour Day", "sq": "Dita e Punës"}, None),
        (easter + timedelta(days=39), {"de": "Christi Himmelfahrt", "en": "Ascension Day", "sq": "Dita e Shëlbimit"}, None),
        (easter + timedelta(days=50), {"de": "Pfingstmontag", "en": "Whit Monday", "sq": "E Hëna e Rrëshajëve"}, None),
        (date(year, 10, 3), {"de": "Tag der Deutschen Einheit", "en": "German Unity Day", "sq": "Dita e Bashkimit Gjerman"}, None),
        (date(year, 12, 25), {"de": "1. Weihnachtstag", "en": "Christmas Day", "sq": "Krishtlindjet"}, None),
        (date(year, 12, 26), {"de": "2. Weihnachtstag", "en": "Second Christmas Day", "sq": "Dita e dytë e Krishtlindjeve"}, None),
    ]
    # Land-specific holidays (Feiertagsgesetze der Länder). Deliberately
    # conservative: only holidays valid in the WHOLE Land are seeded —
    # partial ones (Mariä Himmelfahrt in Bavaria's Catholic municipalities,
    # Augsburger Friedensfest) are omitted, because treating a working day
    # as a holiday would compute a LATER due date than the real one.
    # Ostersonntag/Pfingstsonntag (BB) fall on Sundays — no effect on
    # business-day math, omitted.
    for regions, d, name in [
        (("BW", "BY", "ST"), date(year, 1, 6),
         {"de": "Heilige Drei Könige", "en": "Epiphany", "sq": "Tre Mbretërit"}),
        (("BE", "MV"), date(year, 3, 8),
         {"de": "Internationaler Frauentag", "en": "International Women's Day", "sq": "Dita e Gruas"}),
        (("BW", "BY", "HE", "NW", "RP", "SL"), easter + timedelta(days=60),
         {"de": "Fronleichnam", "en": "Corpus Christi", "sq": "Korpus Kristi"}),
        (("SL",), date(year, 8, 15),
         {"de": "Mariä Himmelfahrt", "en": "Assumption Day", "sq": "Të Ngjiturit e Shën Marisë"}),
        (("TH",), date(year, 9, 20),
         {"de": "Weltkindertag", "en": "World Children's Day", "sq": "Dita Botërore e Fëmijëve"}),
        (("BB", "HB", "HH", "MV", "NI", "SH", "SN", "ST", "TH"), date(year, 10, 31),
         {"de": "Reformationstag", "en": "Reformation Day", "sq": "Dita e Reformacionit"}),
        (("BW", "BY", "NW", "RP", "SL"), date(year, 11, 1),
         {"de": "Allerheiligen", "en": "All Saints' Day", "sq": "Të Gjithë Shenjtorët"}),
        (("SN",), _buss_und_bettag(year),
         {"de": "Buß- und Bettag", "en": "Day of Repentance and Prayer", "sq": "Dita e Pendimit dhe Lutjes"}),
    ]:
        for region in regions:
            out.append((d, name, region))
    return out


DE_JURISDICTION = {
    "code": "DE",
    "name": {
        "de": "Deutschland", "en": "Germany", "sq": "Gjermania",
        "sr": "Nemačka", "tr": "Almanya", "bs": "Njemačka", "zh": "德国",
    },
    "is_active": True,
}

_MONTH_NOTE = (
    "Monatsfrist (§ 222 ZPO i.V.m. §§ 187 ff. BGB): Fristende am Tag des "
    "Zielmonats mit derselben Zahl wie der Zustellungstag; fehlt dieser Tag, "
    "am Monatsende (§ 188 Abs. 3 BGB). Fällt das Ende auf Samstag, Sonntag "
    "oder Feiertag, endet die Frist am nächsten Werktag."
)

DE_DEADLINE_RULES = [
    {
        "code": "civil.berufung",
        "name": {
            "de": "Berufung gegen ein Urteil",
            "en": "Appeal against a judgment (Berufung)",
            "sq": "Ankesë kundër aktgjykimit (Berufung)",
        },
        "legal_basis": "ZPO § 517",
        "practice_area": "civil",
        "trigger_event": "judgment_served",
        "days": 1,
        "day_type": "months",
        "notes": _MONTH_NOTE,
    },
    {
        "code": "civil.berufungsbegruendung",
        "name": {
            "de": "Berufungsbegründung",
            "en": "Grounds of appeal (Berufungsbegründung)",
            "sq": "Arsyetimi i ankesës",
        },
        "legal_basis": "ZPO § 520 Abs. 2",
        "practice_area": "civil",
        "trigger_event": "judgment_served",
        "days": 2,
        "day_type": "months",
        "notes": _MONTH_NOTE,
    },
    {
        "code": "civil.einspruch_versaeumnisurteil",
        "name": {
            "de": "Einspruch gegen Versäumnisurteil",
            "en": "Objection to default judgment",
            "sq": "Kundërshtim ndaj aktgjykimit në mungesë",
        },
        "legal_basis": "ZPO § 339",
        "practice_area": "civil",
        "trigger_event": "judgment_served",
        "days": 14,
        "day_type": "calendar",
    },
    {
        "code": "civil.widerspruch_mahnbescheid",
        "name": {
            "de": "Widerspruch gegen Mahnbescheid",
            "en": "Objection to payment order (Mahnbescheid)",
            "sq": "Kundërshtim ndaj urdhërpagesës",
        },
        "legal_basis": "ZPO § 692 Abs. 1 Nr. 3",
        "practice_area": "civil",
        "trigger_event": "order_served",
        "days": 14,
        "day_type": "calendar",
    },
    {
        "code": "civil.einspruch_vollstreckungsbescheid",
        "name": {
            "de": "Einspruch gegen Vollstreckungsbescheid",
            "en": "Objection to enforcement order",
            "sq": "Kundërshtim ndaj urdhrit të përmbarimit",
        },
        "legal_basis": "ZPO § 700 i.V.m. § 339",
        "practice_area": "civil",
        "trigger_event": "order_served",
        "days": 14,
        "day_type": "calendar",
    },
    {
        "code": "civil.sofortige_beschwerde",
        "name": {
            "de": "Sofortige Beschwerde",
            "en": "Immediate complaint (sofortige Beschwerde)",
            "sq": "Ankesë e menjëhershme",
        },
        "legal_basis": "ZPO § 569",
        "practice_area": "civil",
        "trigger_event": "decision_served",
        "days": 14,
        "day_type": "calendar",
    },
    {
        "code": "labor.kuendigungsschutzklage",
        "name": {
            "de": "Kündigungsschutzklage",
            "en": "Unfair dismissal claim",
            "sq": "Padi kundër shkarkimit nga puna",
        },
        "legal_basis": "KSchG § 4",
        "practice_area": "labor",
        "trigger_event": "dismissal_received",
        "days": 21,
        "day_type": "calendar",
        "notes": "3 Wochen ab Zugang der schriftlichen Kündigung — Ausschlussfrist!",
    },
    {
        "code": "criminal.berufung",
        "name": {
            "de": "Berufung (Strafurteil)",
            "en": "Appeal against criminal judgment",
            "sq": "Ankesë kundër aktgjykimit penal",
        },
        "legal_basis": "StPO § 314",
        "practice_area": "criminal",
        "trigger_event": "judgment_pronounced",
        "days": 7,
        "day_type": "calendar",
        "notes": "1 Woche ab Verkündung (bzw. Zustellung bei Abwesenheit).",
    },
    {
        "code": "criminal.revision",
        "name": {
            "de": "Revision (Strafurteil)",
            "en": "Revision against criminal judgment",
            "sq": "Revizion kundër aktgjykimit penal",
        },
        "legal_basis": "StPO § 341",
        "practice_area": "criminal",
        "trigger_event": "judgment_pronounced",
        "days": 7,
        "day_type": "calendar",
    },
    {
        "code": "criminal.einspruch_strafbefehl",
        "name": {
            "de": "Einspruch gegen Strafbefehl",
            "en": "Objection to penal order (Strafbefehl)",
            "sq": "Kundërshtim ndaj urdhrit penal",
        },
        "legal_basis": "StPO § 410",
        "practice_area": "criminal",
        "trigger_event": "order_served",
        "days": 14,
        "day_type": "calendar",
    },
    {
        "code": "admin.widerspruch",
        "name": {
            "de": "Widerspruch gegen Verwaltungsakt",
            "en": "Administrative objection (Widerspruch)",
            "sq": "Kundërshtim ndaj aktit administrativ",
        },
        "legal_basis": "VwGO § 70",
        "practice_area": "administrative",
        "trigger_event": "act_notified",
        "days": 1,
        "day_type": "months",
        "notes": _MONTH_NOTE,
    },
    {
        "code": "admin.anfechtungsklage",
        "name": {
            "de": "Anfechtungsklage",
            "en": "Action for annulment (Anfechtungsklage)",
            "sq": "Padi për anulim të aktit administrativ",
        },
        "legal_basis": "VwGO § 74",
        "practice_area": "administrative",
        "trigger_event": "decision_served",
        "days": 1,
        "day_type": "months",
        "notes": _MONTH_NOTE,
    },
    {
        "code": "social.widerspruch",
        "name": {
            "de": "Widerspruch (Sozialrecht)",
            "en": "Objection in social law matters",
            "sq": "Kundërshtim në të drejtën sociale",
        },
        "legal_basis": "SGG § 84",
        "practice_area": "administrative",
        "trigger_event": "act_notified",
        "days": 1,
        "day_type": "months",
        "notes": _MONTH_NOTE,
    },
    {
        "code": "tax.einspruch",
        "name": {
            "de": "Einspruch gegen Steuerbescheid",
            "en": "Objection to tax assessment",
            "sq": "Kundërshtim ndaj vendimit tatimor",
        },
        "legal_basis": "AO § 355",
        "practice_area": "administrative",
        "trigger_event": "act_notified",
        "days": 1,
        "day_type": "months",
        "notes": _MONTH_NOTE,
    },
]

# Initial RVG anchors (Anlage 1/2 RVG, Stand 2025 — KostBRÄG 2025 amounts).
# § 13 Abs. 1 RVG fee table (Stand KostBRÄG 2025, in force 2025-06-01) as
# band data: the 1.0 fee is 51.50 € up to 500 €, then grows by a fixed
# increment per *started* step until the band ceiling. Verified against the
# published tables: 2.000 € -> 176.00, 10.000 € -> 652.00, 25.000 € -> 927.00,
# 50.000 € -> 1.357.00, 500.000 € -> 3.752.00, 1.000.000 € -> 5.502.00.
DE_RVG_TABLE = {
    "base_up_to": "500",
    "base_fee": "51.50",
    # (step, band ceiling — None = open-ended, increment per started step)
    "bands": [
        ("500", "2000", "41.50"),
        ("1000", "10000", "59.50"),
        ("3000", "25000", "55.00"),
        ("5000", "50000", "86.00"),
        ("15000", "200000", "99.50"),
        ("30000", "500000", "140.00"),
        ("50000", None, "175.00"),
    ],
    "minimum_fee": "15.00",  # § 13 Abs. 2 RVG
    "legal_basis": "§ 13 RVG (KostBRÄG 2025)",
}

# Rate-based VV items the RVG calculator offers. `group` = the Angelegenheit
# the item belongs to — the VV 7002 expense cap (20 %, max 20 €) applies per
# Angelegenheit, so out-of-court and court work each get their own pauschale.
DE_RVG_VV_ITEMS = [
    {
        "code": "geschaeftsgebuehr",
        "vv": "VV 2300",
        "rate": "1.3",
        "rate_min": "0.5",
        "rate_max": "2.5",
        "group": "aussergerichtlich",
        "name": {
            "de": "Geschäftsgebühr (außergerichtlich)",
            "en": "Business fee (out of court)",
            "sq": "Tarifa e përfaqësimit jashtëgjyqësor",
        },
    },
    {
        "code": "verfahrensgebuehr",
        "vv": "VV 3100",
        "rate": "1.3",
        "group": "gerichtlich",
        "name": {
            "de": "Verfahrensgebühr (1. Instanz)",
            "en": "Procedure fee (first instance)",
            "sq": "Tarifa procedurale (shkalla e parë)",
        },
    },
    {
        "code": "termingebuehr",
        "vv": "VV 3104",
        "rate": "1.2",
        "group": "gerichtlich",
        "name": {
            "de": "Terminsgebühr",
            "en": "Hearing fee",
            "sq": "Tarifa e seancës",
        },
    },
    {
        "code": "einigungsgebuehr",
        "vv": "VV 1000",
        "rate": "1.5",
        "group": "aussergerichtlich",
        "name": {
            "de": "Einigungsgebühr (nicht anhängig)",
            "en": "Settlement fee (not pending in court)",
            "sq": "Tarifa e marrëveshjes (jashtë procesit)",
        },
    },
    {
        "code": "einigungsgebuehr_anhaengig",
        "vv": "VV 1003",
        "rate": "1.0",
        "group": "gerichtlich",
        "name": {
            "de": "Einigungsgebühr (anhängige Sache)",
            "en": "Settlement fee (case pending)",
            "sq": "Tarifa e marrëveshjes (çështje në gjykatë)",
        },
    },
]

# § 34 GKG court-fee table (Anlage 2, Stand KostBRÄG 2025, in force
# 2025-06-01) in the same band format as DE_RVG_TABLE: the 1.0 court fee is
# 40.00 € up to 500 €, then grows per *started* step. Verified against the
# published Anlage 2: 2.000 € -> 103.00, 10.000 € -> 283.00,
# 25.000 € -> 435.50, 50.000 € -> 638.00, 200.000 € -> 2.038.00,
# 500.000 € -> 4.138.00.
DE_GKG_TABLE = {
    "base_up_to": "500",
    "base_fee": "40.00",
    "bands": [
        ("500", "2000", "21.00"),
        ("1000", "10000", "22.50"),
        ("3000", "25000", "30.50"),
        ("5000", "50000", "40.50"),
        ("15000", "200000", "140.00"),
        ("30000", "500000", "210.00"),
        ("50000", None, "210.00"),
    ],
    "minimum_fee": "15.00",  # § 34 Abs. 2 GKG
    "legal_basis": "§ 34 GKG, Anlage 2 (KostBRÄG 2025)",
}

# Per-instance data for the Prozesskostenrechner: the GKG court-fee rate
# (KV GKG Anlage 1) and the RVG lawyer items that arise in that instance.
# Same convention as the established market calculators: 1st instance
# VV 3100/3104, appeal VV 3200/3202, revision before the BGH VV 3208/3210.
DE_PROZESSKOSTEN_INSTANCES = [
    {
        "code": "erste_instanz",
        "court_kv": "KV 1210 GKG",
        "court_rate": "3.0",
        "name": {
            "de": "1. Instanz",
            "en": "First instance",
            "sq": "Shkalla e parë",
        },
        "lawyer_items": [
            {
                "vv": "VV 3100",
                "rate": "1.3",
                "name": {
                    "de": "Verfahrensgebühr",
                    "en": "Procedure fee",
                    "sq": "Tarifa procedurale",
                },
            },
            {
                "vv": "VV 3104",
                "rate": "1.2",
                "name": {
                    "de": "Terminsgebühr",
                    "en": "Hearing fee",
                    "sq": "Tarifa e seancës",
                },
            },
        ],
    },
    {
        "code": "berufung",
        "court_kv": "KV 1220 GKG",
        "court_rate": "4.0",
        "name": {
            "de": "Berufung (2. Instanz)",
            "en": "Appeal (second instance)",
            "sq": "Apeli (shkalla e dytë)",
        },
        "lawyer_items": [
            {
                "vv": "VV 3200",
                "rate": "1.6",
                "name": {
                    "de": "Verfahrensgebühr",
                    "en": "Procedure fee",
                    "sq": "Tarifa procedurale",
                },
            },
            {
                "vv": "VV 3202",
                "rate": "1.2",
                "name": {
                    "de": "Terminsgebühr",
                    "en": "Hearing fee",
                    "sq": "Tarifa e seancës",
                },
            },
        ],
    },
    {
        "code": "revision",
        "court_kv": "KV 1230 GKG",
        "court_rate": "5.0",
        "name": {
            "de": "Revision (BGH)",
            "en": "Revision (Federal Court of Justice)",
            "sq": "Revizioni (Gjykata Federale)",
        },
        "lawyer_items": [
            {
                "vv": "VV 3208",
                "rate": "2.3",
                "name": {
                    "de": "Verfahrensgebühr (BGH-Anwalt)",
                    "en": "Procedure fee (BGH counsel)",
                    "sq": "Tarifa procedurale (avokat i BGH)",
                },
            },
            {
                "vv": "VV 3210",
                "rate": "1.5",
                "name": {
                    "de": "Terminsgebühr",
                    "en": "Hearing fee",
                    "sq": "Tarifa e seancës",
                },
            },
        ],
    },
]

# Zivilgerichtliches Online-Verfahren (D-041): the 18 pilot local courts
# per the BMJV announcement of 2026-04-15 (source: bmjv.de + service.justiz.de,
# court lists set by Rechtsverordnung of each Land). `scope` is either
# "payment" (general payment claims <= 10,000 € — includes air passenger
# rights) or "flight" (air passenger rights only). `live_from` is the date
# the court joined the pilot. Court fee in the OV: 2.0 instead of 3.0
# (reduced Gerichtskostenvorschuss, service.justiz.de).
DE_OV_COURTS = [
    {"name": "AG Mannheim", "state": "BW", "scope": "payment", "live_from": "2026-04-20"},
    {"name": "AG Nürtingen", "state": "BW", "scope": "payment", "live_from": "2026-04-20"},
    {"name": "AG Nürnberg", "state": "BY", "scope": "payment", "live_from": "2026-04-15"},
    {"name": "AG Schöneberg", "state": "BE", "scope": "payment", "live_from": "2026-04-15"},
    {"name": "AG Bremen", "state": "HB", "scope": "payment", "live_from": "2026-04-15"},
    {"name": "AG Hamburg-Mitte", "state": "HH", "scope": "payment", "live_from": "2026-04-15"},
    {"name": "AG Frankfurt am Main", "state": "HE", "scope": "payment", "live_from": "2026-04-15"},
    {"name": "AG Leipzig", "state": "SN", "scope": "payment", "live_from": "2026-04-15"},
    {"name": "AG Bonn", "state": "NW", "scope": "payment", "live_from": "2026-06-01"},
    {"name": "AG Essen", "state": "NW", "scope": "payment", "live_from": "2026-06-01"},
    {"name": "AG Dortmund", "state": "NW", "scope": "payment", "live_from": "2026-06-01"},
    {"name": "AG Bitburg", "state": "RP", "scope": "payment", "live_from": "2026-06-01"},
    {"name": "AG Sinzig", "state": "RP", "scope": "payment", "live_from": "2026-06-01"},
    {"name": "AG Erding", "state": "BY", "scope": "flight", "live_from": "2026-04-15"},
    {"name": "AG Eilenburg", "state": "SN", "scope": "flight", "live_from": "2026-04-15"},
    {"name": "AG Düsseldorf", "state": "NW", "scope": "flight", "live_from": "2026-06-01"},
    {"name": "AG Steinfurt", "state": "NW", "scope": "flight", "live_from": "2026-06-01"},
    {"name": "AG Königs Wusterhausen", "state": "BB", "scope": "flight", "live_from": "2026-10-01"},
]

OV_MAX_VALUE = 10_000  # EUR — Amtsgericht ceiling of the pilot
OV_PORTAL_URL = "https://service.justiz.de/klagen-ohne-anwalt"


# Value-fee items (Nr. 3100 etc.) depend on the Gegenstandswert; the amounts
# here are the fixed statutory anchors a solo lawyer reaches for first.
DE_FEE_TARIFF = [
    {
        "code": "advice.first_consultation_consumer",
        "tariff_no": "RVG § 34",
        "name": {
            "de": "Erstberatung Verbraucher (Kappungsgrenze)",
            "en": "First consultation, consumer (statutory cap)",
            "sq": "Konsulta e parë për konsumatorë (kufiri ligjor)",
        },
        "practice_area": "civil",
        "amount": "190.00",
        "unit": "Beratung",
        "legal_basis": "RVG § 34 Abs. 1 S. 3",
        "notes": "Höchstbetrag für die erste Beratung eines Verbrauchers (zzgl. USt.).",
    },
    {
        "code": "advice.consumer_cap",
        "tariff_no": "RVG § 34",
        "name": {
            "de": "Beratung/Gutachten Verbraucher (Kappungsgrenze)",
            "en": "Advice/opinion, consumer (statutory cap)",
            "sq": "Këshillim/mendim për konsumatorë (kufiri ligjor)",
        },
        "practice_area": "civil",
        "amount": "250.00",
        "unit": "Beratung",
        "legal_basis": "RVG § 34 Abs. 1 S. 3",
        "notes": "Höchstbetrag für Beratung/Gutachten gegenüber Verbrauchern (zzgl. USt.).",
    },
    {
        "code": "criminal.defense_base_first_instance",
        "tariff_no": "VV 4100/4106",
        "name": {
            "de": "Strafverteidigung — Grund- und Verfahrensgebühr (Mittelgebühr, AG)",
            "en": "Criminal defense — base + procedure fee (mid-range, local court)",
            "sq": "Mbrojtja penale — tarifa bazë + procedurale (mesatare)",
        },
        "practice_area": "criminal",
        "amount": "396.00",
        "unit": "Verfahren",
        "legal_basis": "RVG VV Nr. 4100, 4106",
        "notes": "Rahmengebühren; hier die Mittelgebühr als Anhaltspunkt (zzgl. USt.).",
    },
    {
        "code": "criminal.hearing_fee",
        "tariff_no": "VV 4108",
        "name": {
            "de": "Strafverteidigung — Terminsgebühr (Mittelgebühr, AG)",
            "en": "Criminal defense — hearing fee (mid-range, local court)",
            "sq": "Mbrojtja penale — tarifa e seancës (mesatare)",
        },
        "practice_area": "criminal",
        "amount": "330.00",
        "unit": "Termin",
        "legal_basis": "RVG VV Nr. 4108",
        "notes": "Rahmengebühr je Hauptverhandlungstag (zzgl. USt.).",
    },
    {
        "code": "civil.geschaeftsgebuehr_5k",
        "tariff_no": "VV 2300",
        "name": {
            "de": "Geschäftsgebühr 1,3 (Gegenstandswert 5.000 €)",
            "en": "Business fee 1.3 (value in dispute €5,000)",
            "sq": "Tarifa e përfaqësimit jashtëgjyqësor 1,3 (vlera 5.000 €)",
        },
        "practice_area": "civil",
        "amount": "460.85",
        "unit": "Angelegenheit",
        "legal_basis": "RVG VV Nr. 2300; § 13 RVG",
        "notes": "1,3-Gebühr aus 5.000 € (354,50 € × 1,3, KostBRÄG 2025; zzgl. Auslagen und USt.).",
    },
    {
        "code": "civil.verfahrensgebuehr_5k",
        "tariff_no": "VV 3100",
        "name": {
            "de": "Verfahrensgebühr 1,3 (Gegenstandswert 5.000 €)",
            "en": "Procedure fee 1.3 (value in dispute €5,000)",
            "sq": "Tarifa procedurale 1,3 (vlera 5.000 €)",
        },
        "practice_area": "civil",
        "amount": "460.85",
        "unit": "Rechtszug",
        "legal_basis": "RVG VV Nr. 3100; § 13 RVG",
        "notes": "Erste Instanz; zzgl. 1,2-Terminsgebühr VV 3104 (zzgl. USt.).",
    },
    {
        "code": "civil.terminsgebuehr_5k",
        "tariff_no": "VV 3104",
        "name": {
            "de": "Terminsgebühr 1,2 (Gegenstandswert 5.000 €)",
            "en": "Hearing fee 1.2 (value in dispute €5,000)",
            "sq": "Tarifa e seancës 1,2 (vlera 5.000 €)",
        },
        "practice_area": "civil",
        "amount": "425.40",
        "unit": "Rechtszug",
        "legal_basis": "RVG VV Nr. 3104; § 13 RVG",
        "notes": "354,50 € × 1,2 (KostBRÄG 2025; zzgl. USt.).",
    },
    {
        "code": "general.postpauschale",
        "tariff_no": "VV 7002",
        "name": {
            "de": "Post- und Telekommunikationspauschale",
            "en": "Post/telecom flat expense",
            "sq": "Paushalli postar/telekomunikimi",
        },
        "practice_area": "other",
        "amount": "20.00",
        "unit": "Angelegenheit",
        "legal_basis": "RVG VV Nr. 7002",
        "notes": "20 % der Gebühren, höchstens 20 € je Angelegenheit.",
    },
]

# Lawyer document templates (jurisdiction DE, locale de) — Jinja2, filled
# from matter data in the templates module. Kept deliberately generic;
# every office adapts its own house style on top.
DE_TEMPLATES = [
    {
        "code": "civil.klageschrift",
        "locale": "de",
        "practice_area": "civil",
        "name": {"de": "Klageschrift (Zivilrecht)", "en": "Statement of claim (civil)", "sq": "Padi civile (DE)"},
        "variables": [
            {"name": "court_name", "label": {"de": "Gericht", "en": "Court", "sq": "Gjykata"}},
            {"name": "claim_subject", "label": {"de": "Streitgegenstand", "en": "Subject of claim", "sq": "Objekti i padisë"}},
            {"name": "claim_value", "label": {"de": "Streitwert (€)", "en": "Value in dispute (€)", "sq": "Vlera e kontestit (€)"}},
            {"name": "facts", "label": {"de": "Sachverhalt", "en": "Facts", "sq": "Faktet"}},
            {"name": "evidence", "label": {"de": "Beweismittel", "en": "Evidence", "sq": "Provat"}},
            {"name": "request", "label": {"de": "Anträge", "en": "Relief sought", "sq": "Kërkesat"}},
        ],
        "body": """An das
{{ court_name }}

KLAGE

des/der {{ client_name }}, {{ client_address }},
— Kläger/in —
Prozessbevollmächtigte/r: {{ lawyer_name }}, {{ firm_name }}

gegen

{{ opposing_name }}
— Beklagte/r —

wegen: {{ claim_subject }}
Streitwert: {{ claim_value }} €

Namens und in Vollmacht des Klägers/der Klägerin erheben wir Klage und beantragen:

{{ request }}

Begründung:

I. Sachverhalt

{{ facts }}

II. Beweismittel

{{ evidence }}

III. Rechtliche Würdigung

Der Anspruch ergibt sich aus dem dargestellten Sachverhalt.

{{ city }}, den {{ date }}

_____________________
{{ lawyer_name }}
Rechtsanwalt/Rechtsanwältin""",
    },
    {
        "code": "civil.ov_klageschrift",
        "locale": "de",
        "practice_area": "civil",
        "name": {
            "de": "Klageschrift Online-Verfahren (Zahlungsklage ≤ 10.000 €)",
            "en": "Statement of claim, online procedure (payment ≤ €10,000)",
            "sq": "Padi për procedurën online (pagesë ≤ 10.000 €)",
        },
        "variables": [
            {"name": "court_name", "label": {"de": "Pilot-Amtsgericht", "en": "Pilot local court", "sq": "Gjykata pilote"}},
            {"name": "claim_amount", "label": {"de": "Forderung (€)", "en": "Amount claimed (€)", "sq": "Shuma e kërkuar (€)"}},
            {"name": "claim_basis", "label": {"de": "Anspruchsgrund (z. B. Rechnung, Mietvertrag)", "en": "Basis of claim (e.g. invoice, lease)", "sq": "Baza e kërkesës (p.sh. fatura, kontrata)"}},
            {"name": "due_since", "label": {"de": "Fällig seit", "en": "Due since", "sq": "E maturuar që nga"}},
            {"name": "facts", "label": {"de": "Sachverhalt", "en": "Facts", "sq": "Faktet"}},
            {"name": "evidence", "label": {"de": "Beweismittel", "en": "Evidence", "sq": "Provat"}},
        ],
        "body": """An das
{{ court_name }}
— Online-Verfahren —

KLAGE IM ONLINE-VERFAHREN
(Zahlungsklage nach dem Gesetz zur Entwicklung und Erprobung
eines Online-Verfahrens in der Zivilgerichtsbarkeit)

des/der {{ client_name }}, {{ client_address }},
— Kläger/in —
Prozessbevollmächtigte/r: {{ lawyer_name }}, {{ firm_name }}

gegen

{{ opposing_name }}
— Beklagte/r —

wegen: Zahlungsanspruch aus {{ claim_basis }}
Streitwert: {{ claim_amount }} €

Wir beantragen,

1. die Beklagtenseite zu verurteilen, an die Klagepartei {{ claim_amount }} €
   nebst Zinsen in Höhe von 5 Prozentpunkten über dem Basiszinssatz
   seit dem {{ due_since }} zu zahlen;
2. der Beklagtenseite die Kosten des Rechtsstreits aufzuerlegen.

Begründung:

I. Sachverhalt

{{ facts }}

Der Anspruch ist seit dem {{ due_since }} fällig. Die Beklagtenseite wurde
zur Zahlung aufgefordert; eine Zahlung ist nicht erfolgt.

II. Beweismittel

{{ evidence }}

III. Zulässigkeit des Online-Verfahrens

Es handelt sich um eine Zahlungsklage mit einem Streitwert bis 10.000 €.
Das angerufene Amtsgericht nimmt an der Erprobung des zivilgerichtlichen
Online-Verfahrens teil.

{{ city }}, den {{ date }}

_____________________
{{ lawyer_name }}
Rechtsanwalt/Rechtsanwältin""",
    },
    {
        "code": "civil.ov_fluggastrechte",
        "locale": "de",
        "practice_area": "civil",
        "name": {
            "de": "Klageschrift Online-Verfahren (Fluggastrechte, VO (EG) 261/2004)",
            "en": "Statement of claim, online procedure (air passenger rights)",
            "sq": "Padi për procedurën online (të drejtat e pasagjerëve ajrorë)",
        },
        "variables": [
            {"name": "court_name", "label": {"de": "Pilot-Amtsgericht (Start- oder Zielflughafen)", "en": "Pilot court (departure or arrival airport)", "sq": "Gjykata pilote (aeroporti i nisjes/mbërritjes)"}},
            {"name": "airline", "label": {"de": "Luftfahrtunternehmen (Beklagte)", "en": "Airline (defendant)", "sq": "Kompania ajrore (e paditura)"}},
            {"name": "flight_number", "label": {"de": "Flugnummer", "en": "Flight number", "sq": "Numri i fluturimit"}},
            {"name": "flight_date", "label": {"de": "Flugdatum", "en": "Flight date", "sq": "Data e fluturimit"}},
            {"name": "route", "label": {"de": "Strecke (von — nach)", "en": "Route (from — to)", "sq": "Linja (nga — për)"}},
            {"name": "disruption", "label": {"de": "Störung (Annullierung / Verspätung > 3 h / Nichtbeförderung)", "en": "Disruption (cancellation / delay > 3 h / denied boarding)", "sq": "Problemi (anulim / vonesë > 3 orë / mospranim)"}},
            {"name": "compensation", "label": {"de": "Ausgleichszahlung (€ — 250/400/600 je Entfernung)", "en": "Compensation (€ — 250/400/600 by distance)", "sq": "Kompensimi (€ — 250/400/600 sipas distancës)"}},
            {"name": "facts", "label": {"de": "Sachverhalt", "en": "Facts", "sq": "Faktet"}},
        ],
        "body": """An das
{{ court_name }}
— Online-Verfahren —

KLAGE IM ONLINE-VERFAHREN
(Fluggastrechte, Verordnung (EG) Nr. 261/2004)

des/der {{ client_name }}, {{ client_address }},
— Kläger/in —
Prozessbevollmächtigte/r: {{ lawyer_name }}, {{ firm_name }}

gegen

{{ airline }}
— Beklagte —

wegen: Ausgleichszahlung nach Art. 7 VO (EG) Nr. 261/2004
Streitwert: {{ compensation }} €

Wir beantragen,

1. die Beklagte zu verurteilen, an die Klagepartei {{ compensation }} €
   nebst Zinsen in Höhe von 5 Prozentpunkten über dem Basiszinssatz
   seit Rechtshängigkeit zu zahlen;
2. der Beklagten die Kosten des Rechtsstreits aufzuerlegen.

Begründung:

I. Sachverhalt

Die Klagepartei verfügte über eine bestätigte Buchung für den Flug
{{ flight_number }} am {{ flight_date }} ({{ route }}), ausgeführt durch
die Beklagte. Störung: {{ disruption }}.

{{ facts }}

II. Anspruch

Der Anspruch auf Ausgleichszahlung in Höhe von {{ compensation }} € ergibt
sich aus Art. 5 bzw. Art. 4 i. V. m. Art. 7 der Verordnung (EG)
Nr. 261/2004. Außergewöhnliche Umstände im Sinne des Art. 5 Abs. 3 sind
nicht ersichtlich.

III. Zuständigkeit und Online-Verfahren

Das angerufene Amtsgericht ist als Gericht des Abflug- bzw. Ankunftsorts
zuständig und nimmt an der Erprobung des zivilgerichtlichen
Online-Verfahrens für Fluggastrechte teil.

{{ city }}, den {{ date }}

_____________________
{{ lawyer_name }}
Rechtsanwalt/Rechtsanwältin""",
    },
    {
        "code": "labor.kuendigungsschutzklage",
        "locale": "de",
        "practice_area": "labor",
        "name": {"de": "Kündigungsschutzklage", "en": "Unfair dismissal claim", "sq": "Padi kundër shkarkimit"},
        "variables": [
            {"name": "court_name", "label": {"de": "Arbeitsgericht", "en": "Labour court", "sq": "Gjykata e punës"}},
            {"name": "employer", "label": {"de": "Arbeitgeber (Beklagte)", "en": "Employer (defendant)", "sq": "Punëdhënësi"}},
            {"name": "employment_start", "label": {"de": "Beschäftigt seit", "en": "Employed since", "sq": "I punësuar që nga"}},
            {"name": "dismissal_date", "label": {"de": "Kündigung zugegangen am", "en": "Dismissal received on", "sq": "Shkarkimi u pranua më"}},
            {"name": "facts", "label": {"de": "Sachverhalt", "en": "Facts", "sq": "Faktet"}},
        ],
        "body": """An das
{{ court_name }}

KÜNDIGUNGSSCHUTZKLAGE

des/der {{ client_name }}, {{ client_address }},
— Kläger/in —
Prozessbevollmächtigte/r: {{ lawyer_name }}, {{ firm_name }}

gegen

{{ employer }}
— Beklagte —

Namens und in Vollmacht der Klagepartei erheben wir Klage und beantragen festzustellen,

1. dass das Arbeitsverhältnis der Parteien durch die Kündigung vom {{ dismissal_date }} nicht aufgelöst worden ist;
2. dass das Arbeitsverhältnis zu unveränderten Bedingungen fortbesteht.

Begründung:

Die Klagepartei ist seit dem {{ employment_start }} bei der Beklagten beschäftigt. Die Kündigung ging am {{ dismissal_date }} zu; die Drei-Wochen-Frist des § 4 KSchG ist gewahrt.

{{ facts }}

Die Kündigung ist sozial ungerechtfertigt (§ 1 KSchG).

{{ city }}, den {{ date }}

_____________________
{{ lawyer_name }}
Rechtsanwalt/Rechtsanwältin""",
    },
    {
        "code": "admin.widerspruch",
        "locale": "de",
        "practice_area": "administrative",
        "name": {"de": "Widerspruch gegen Verwaltungsakt", "en": "Administrative objection", "sq": "Kundërshtim administrativ"},
        "variables": [
            {"name": "authority", "label": {"de": "Behörde", "en": "Authority", "sq": "Organi"}},
            {"name": "act_reference", "label": {"de": "Bescheid (Az./Datum)", "en": "Decision (ref./date)", "sq": "Vendimi (nr./data)"}},
            {"name": "grounds", "label": {"de": "Begründung", "en": "Grounds", "sq": "Arsyetimi"}},
        ],
        "body": """{{ authority }}

WIDERSPRUCH

In Sachen {{ client_name }}, {{ client_address }},
vertreten durch {{ lawyer_name }}, {{ firm_name }},

legen wir hiermit gegen den Bescheid {{ act_reference }}

WIDERSPRUCH

ein (§ 70 VwGO). Zur Begründung führen wir aus:

{{ grounds }}

Wir beantragen, den Bescheid aufzuheben und über die Sache unter Beachtung unserer Ausführungen neu zu entscheiden. Um schriftliche Eingangsbestätigung wird gebeten.

{{ city }}, den {{ date }}

_____________________
{{ lawyer_name }}
Rechtsanwalt/Rechtsanwältin""",
    },
    {
        "code": "general.vollmacht",
        "locale": "de",
        "practice_area": "other",
        "name": {"de": "Vollmacht", "en": "Power of attorney", "sq": "Autorizim/Prokurë (DE)"},
        "variables": [
            {"name": "scope", "label": {"de": "Gegenstand der Vollmacht", "en": "Scope", "sq": "Objekti i autorizimit"}},
        ],
        "body": """VOLLMACHT

Hiermit bevollmächtige ich, {{ client_name }}, {{ client_address }},

{{ lawyer_name }}, {{ firm_name }},

mich in folgender Angelegenheit außergerichtlich und gerichtlich zu vertreten:

{{ scope }}

Die Vollmacht umfasst insbesondere die Prozessführung (u.a. §§ 81 ff. ZPO) einschließlich der Befugnis zur Erhebung und Zurücknahme von Klagen und Rechtsmitteln, die Vertretung in sonstigen Verfahren sowie den Empfang von Zustellungen, den Abschluss von Vergleichen und die Entgegennahme von Geldern und Wertsachen.

{{ city }}, den {{ date }}

_____________________
{{ client_name }}""",
    },
    {
        "code": "general.deckungsanfrage",
        "locale": "de",
        "practice_area": "other",
        "name": {
            "de": "Deckungsanfrage Rechtsschutzversicherung",
            "en": "Coverage inquiry to legal insurer",
            "sq": "Kërkesë mbulimi te sigurimi juridik",
        },
        "variables": [
            {"name": "insurer_name", "label": {"de": "Versicherer", "en": "Insurer", "sq": "Siguruesi"}},
            {"name": "policy_number", "label": {"de": "Versicherungsschein-Nr.", "en": "Policy number", "sq": "Numri i policës"}},
            {"name": "dispute_subject", "label": {"de": "Gegenstand der Streitigkeit", "en": "Subject of dispute", "sq": "Objekti i kontestit"}},
            {"name": "facts", "label": {"de": "Kurzdarstellung des Sachverhalts", "en": "Brief facts", "sq": "Përshkrimi i shkurtër i faktrave"}},
            {"name": "claim_value", "label": {"de": "Gegenstandswert (€)", "en": "Value in dispute (€)", "sq": "Vlera e kontestit (€)"}},
        ],
        "body": """{{ insurer_name }}
— Leistungsabteilung Rechtsschutz —

Deckungsanfrage
Versicherungsschein-Nr.: {{ policy_number }}
Versicherungsnehmer/in: {{ client_name }}, {{ client_address }}

Sehr geehrte Damen und Herren,

wir zeigen an, dass uns der/die oben genannte Versicherungsnehmer/in mit der Wahrnehmung seiner/ihrer rechtlichen Interessen beauftragt hat. Ordnungsgemäße Bevollmächtigung wird anwaltlich versichert.

Gegenstand: {{ dispute_subject }}
Gegenstandswert: {{ claim_value }} €

Zum Sachverhalt:

{{ facts }}

Wir bitten um Erteilung der Deckungszusage für die außergerichtliche Interessenwahrnehmung sowie — soweit erforderlich — für das gerichtliche Verfahren erster Instanz, und um Bestätigung der Kostenübernahme nach dem RVG. Bitte teilen Sie uns auch eine etwaige Selbstbeteiligung mit.

Um kurzfristige Rückäußerung — gern per E-Mail — wird gebeten.

Mit freundlichen Grüßen

{{ city }}, den {{ date }}

_____________________
{{ lawyer_name }}
Rechtsanwalt/Rechtsanwältin
{{ firm_name }}""",
    },
]

# Citizen self-service letters for the public /dokumentet tool on the DE
# host — same shape as seeds/citizen_docs.py, with German bodies ("body"
# key; the generator falls back to body_sq for XK templates).
DE_CITIZEN_DOC_TEMPLATES: list[dict] = [
    {
        "code": "de_widerspruch",
        "category": "institucionet",
        "name": {
            "de": "Widerspruch gegen einen Bescheid",
            "en": "Objection to an official decision",
            "tr": "Resmî karara itiraz",
            "sq": "Kundërshtim ndaj një vendimi zyrtar (DE)",
        },
        "fields": [
            {"key": "sender_name", "type": "text", "label": {
                "de": "Ihr Vor- und Nachname", "en": "Your full name",
                "tr": "Adınız ve soyadınız", "sq": "Emri dhe mbiemri"}},
            {"key": "sender_address", "type": "text", "label": {
                "de": "Ihre Anschrift", "en": "Your address",
                "tr": "Adresiniz", "sq": "Adresa"}},
            {"key": "authority", "type": "text", "label": {
                "de": "Behörde (z.B. Jobcenter Berlin Mitte)", "en": "Authority",
                "tr": "Kurum", "sq": "Organi"}},
            {"key": "act_reference", "type": "text", "label": {
                "de": "Bescheid: Aktenzeichen und Datum", "en": "Decision: reference and date",
                "tr": "Karar: dosya numarası ve tarih", "sq": "Vendimi: numri dhe data"}},
            {"key": "body", "type": "textarea", "label": {
                "de": "Warum der Bescheid falsch ist (in einfachen Worten)",
                "en": "Why the decision is wrong (in plain words)",
                "tr": "Kararın neden hatalı olduğu (basit kelimelerle)",
                "sq": "Pse vendimi është i gabuar"}},
            {"key": "city", "type": "text", "label": {
                "de": "Stadt", "en": "City", "tr": "Şehir", "sq": "Qyteti"}},
        ],
        "body": (
            "{{ sender_name }}\n{{ sender_address }}\n\n"
            "{{ authority }}\n\n"
            "Betreff: Widerspruch gegen den Bescheid {{ act_reference }}\n\n"
            "Sehr geehrte Damen und Herren,\n\n"
            "hiermit lege ich fristgerecht Widerspruch gegen den oben genannten "
            "Bescheid ein.\n\nBegründung:\n\n{{ body }}\n\n"
            "Ich bitte um schriftliche Bestätigung des Eingangs und um Überprüfung "
            "des Bescheids. Bis zur Entscheidung über den Widerspruch bitte ich, "
            "von Vollzugsmaßnahmen abzusehen.\n\n"
            "Mit freundlichen Grüßen\n\n{{ city }}, den {{ date }}\n\n"
            "_____________________\n{{ sender_name }}"
        ),
    },
    {
        "code": "de_kuendigung_vertrag",
        "category": "konsumatori",
        "name": {
            "de": "Kündigung eines Vertrags (Abo, Handy, Fitnessstudio)",
            "en": "Contract termination (subscription, phone, gym)",
            "tr": "Sözleşme feshi (abonelik, telefon, spor salonu)",
            "sq": "Ndërprerje kontrate (abonim, telefon, palestër)",
        },
        "fields": [
            {"key": "sender_name", "type": "text", "label": {
                "de": "Ihr Vor- und Nachname", "en": "Your full name",
                "tr": "Adınız ve soyadınız", "sq": "Emri dhe mbiemri"}},
            {"key": "sender_address", "type": "text", "label": {
                "de": "Ihre Anschrift", "en": "Your address",
                "tr": "Adresiniz", "sq": "Adresa"}},
            {"key": "company", "type": "text", "label": {
                "de": "Unternehmen", "en": "Company", "tr": "Şirket", "sq": "Kompania"}},
            {"key": "contract_reference", "type": "text", "label": {
                "de": "Vertrags-/Kundennummer", "en": "Contract/customer number",
                "tr": "Sözleşme/müşteri numarası", "sq": "Numri i kontratës/klientit"}},
            {"key": "city", "type": "text", "label": {
                "de": "Stadt", "en": "City", "tr": "Şehir", "sq": "Qyteti"}},
        ],
        "body": (
            "{{ sender_name }}\n{{ sender_address }}\n\n"
            "{{ company }}\n\n"
            "Betreff: Kündigung des Vertrags Nr. {{ contract_reference }}\n\n"
            "Sehr geehrte Damen und Herren,\n\n"
            "hiermit kündige ich den oben genannten Vertrag fristgerecht zum "
            "nächstmöglichen Zeitpunkt.\n\n"
            "Bitte bestätigen Sie mir die Kündigung und das Beendigungsdatum "
            "schriftlich. Einer stillschweigenden Verlängerung des Vertrags "
            "widerspreche ich ausdrücklich. Ich weise darauf hin, dass die "
            "Kündigungsbestätigung nach § 312k BGB unverzüglich zu erteilen ist.\n\n"
            "Mit freundlichen Grüßen\n\n{{ city }}, den {{ date }}\n\n"
            "_____________________\n{{ sender_name }}"
        ),
    },
    {
        "code": "de_mahnung",
        "category": "konsumatori",
        "name": {
            "de": "Mahnung — Zahlungsaufforderung",
            "en": "Payment demand (Mahnung)",
            "tr": "Ödeme ihtarı",
            "sq": "Kërkesë për pagesë (Mahnung)",
        },
        "fields": [
            {"key": "sender_name", "type": "text", "label": {
                "de": "Ihr Vor- und Nachname", "en": "Your full name",
                "tr": "Adınız ve soyadınız", "sq": "Emri dhe mbiemri"}},
            {"key": "sender_address", "type": "text", "label": {
                "de": "Ihre Anschrift", "en": "Your address",
                "tr": "Adresiniz", "sq": "Adresa"}},
            {"key": "debtor", "type": "text", "label": {
                "de": "Schuldner (Name und Anschrift)", "en": "Debtor (name and address)",
                "tr": "Borçlu (ad ve adres)", "sq": "Debitori (emri dhe adresa)"}},
            {"key": "amount", "type": "text", "label": {
                "de": "Offener Betrag (€)", "en": "Outstanding amount (€)",
                "tr": "Ödenmemiş tutar (€)", "sq": "Shuma e papaguar (€)"}},
            {"key": "reason", "type": "textarea", "label": {
                "de": "Wofür (Rechnung, Leistung, Datum)", "en": "For what (invoice, service, date)",
                "tr": "Ne için (fatura, hizmet, tarih)", "sq": "Për çfarë (fatura, shërbimi, data)"}},
            {"key": "deadline_days", "type": "text", "label": {
                "de": "Zahlungsfrist in Tagen (z.B. 14)", "en": "Payment deadline in days (e.g. 14)",
                "tr": "Ödeme süresi gün olarak (örn. 14)", "sq": "Afati i pagesës në ditë (p.sh. 14)"}},
            {"key": "city", "type": "text", "label": {
                "de": "Stadt", "en": "City", "tr": "Şehir", "sq": "Qyteti"}},
        ],
        "body": (
            "{{ sender_name }}\n{{ sender_address }}\n\n"
            "{{ debtor }}\n\n"
            "Betreff: Mahnung — Zahlungsaufforderung über {{ amount }} €\n\n"
            "Sehr geehrte Damen und Herren,\n\n"
            "trotz Fälligkeit ist die folgende Forderung bislang nicht beglichen:\n\n"
            "{{ reason }}\n\n"
            "Ich fordere Sie auf, den offenen Betrag von {{ amount }} € innerhalb "
            "von {{ deadline_days }} Tagen nach Erhalt dieses Schreibens auf mein "
            "Konto zu zahlen. Nach fruchtlosem Fristablauf befinden Sie sich in "
            "Verzug (§ 286 BGB); ich behalte mir die Einleitung des gerichtlichen "
            "Mahnverfahrens sowie die Geltendmachung von Verzugszinsen und "
            "weiteren Kosten vor.\n\n"
            "Mit freundlichen Grüßen\n\n{{ city }}, den {{ date }}\n\n"
            "_____________________\n{{ sender_name }}"
        ),
    },
    {
        "code": "de_dsgvo_auskunft",
        "category": "te_pergjithshme",
        "name": {
            "de": "Datenauskunft nach Art. 15 DSGVO",
            "en": "Data access request (Art. 15 GDPR)",
            "tr": "Veri erişim talebi (GDPR m. 15)",
            "sq": "Kërkesë për qasje në të dhëna (GDPR neni 15)",
        },
        "fields": [
            {"key": "sender_name", "type": "text", "label": {
                "de": "Ihr Vor- und Nachname", "en": "Your full name",
                "tr": "Adınız ve soyadınız", "sq": "Emri dhe mbiemri"}},
            {"key": "sender_address", "type": "text", "label": {
                "de": "Ihre Anschrift", "en": "Your address",
                "tr": "Adresiniz", "sq": "Adresa"}},
            {"key": "company", "type": "text", "label": {
                "de": "Unternehmen/Stelle", "en": "Company/entity",
                "tr": "Şirket/kurum", "sq": "Kompania/organi"}},
            {"key": "customer_reference", "type": "text", "label": {
                "de": "Kunden-/Vertragsnummer (falls vorhanden)", "en": "Customer/contract number (if any)",
                "tr": "Müşteri/sözleşme numarası (varsa)", "sq": "Numri i klientit/kontratës (nëse ka)"}},
            {"key": "city", "type": "text", "label": {
                "de": "Stadt", "en": "City", "tr": "Şehir", "sq": "Qyteti"}},
        ],
        "body": (
            "{{ sender_name }}\n{{ sender_address }}\n\n"
            "{{ company }}\n\n"
            "Betreff: Auskunftsersuchen nach Art. 15 DSGVO"
            " ({{ customer_reference }})\n\n"
            "Sehr geehrte Damen und Herren,\n\n"
            "hiermit mache ich mein Auskunftsrecht nach Art. 15 DSGVO geltend und "
            "bitte um Mitteilung, ob und welche personenbezogenen Daten Sie über "
            "mich verarbeiten — einschließlich der Verarbeitungszwecke, der "
            "Datenkategorien, der Empfänger, der geplanten Speicherdauer und der "
            "Herkunft der Daten. Bitte stellen Sie mir zudem eine Kopie der Daten "
            "zur Verfügung (Art. 15 Abs. 3 DSGVO).\n\n"
            "Die Auskunft ist unverzüglich, spätestens innerhalb eines Monats zu "
            "erteilen (Art. 12 Abs. 3 DSGVO).\n\n"
            "Mit freundlichen Grüßen\n\n{{ city }}, den {{ date }}\n\n"
            "_____________________\n{{ sender_name }}"
        ),
    },
]
