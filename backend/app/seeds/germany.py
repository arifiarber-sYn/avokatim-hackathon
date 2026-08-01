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
        "amount": "483.60",
        "unit": "Angelegenheit",
        "legal_basis": "RVG VV Nr. 2300; § 13 RVG",
        "notes": "1,3-Gebühr aus 5.000 € (372 € × 1,3, Stand 2025; zzgl. Auslagen und USt.).",
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
        "amount": "483.60",
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
        "amount": "446.40",
        "unit": "Rechtszug",
        "legal_basis": "RVG VV Nr. 3104; § 13 RVG",
        "notes": "372 € × 1,2 (Stand 2025; zzgl. USt.).",
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
