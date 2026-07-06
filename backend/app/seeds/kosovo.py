"""Seed data for the Kosovo (XK) jurisdiction: procedural deadline rules with
their legal basis, public holidays, and starter document templates.

Deadlines reference:
- LPK   = Ligji Nr. 03/L-006 per Proceduren Kontestimore (civil procedure)
- KPPRK = Kodi Nr. 08/L-032 i Procedures Penale (criminal procedure)
- LKA   = Ligji Nr. 05/L-031 per Proceduren e Pergjithshme Administrative
NOTE: verified starting points — the lawyer can adjust any rule in the UI;
rules are data, not code.
"""

JURISDICTIONS = [
    {
        "code": "XK",
        "name": {"sq": "Kosova", "en": "Kosovo", "zh": "科索沃"},
    },
    {
        "code": "GB",
        "name": {"sq": "Anglia dhe Uellsi", "en": "England and Wales", "zh": "英格兰和威尔士"},
        "is_active": False,
    },
    {
        "code": "CN",
        "name": {"sq": "Kina", "en": "China", "zh": "中国"},
        "is_active": False,
    },
    {
        "code": "INTL",
        "name": {"sq": "Ndërkombëtar", "en": "International", "zh": "国际"},
        "is_active": False,
    },
]

XK_DEADLINE_RULES = [
    {
        "code": "civil.appeal_judgment",
        "name": {
            "sq": "Ankesë kundër aktgjykimit",
            "en": "Appeal against judgment",
            "zh": "对判决提出上诉",
        },
        "legal_basis": "LPK neni 176",
        "practice_area": "civil",
        "trigger_event": "judgment_served",
        "days": 15,
    },
    {
        "code": "civil.appeal_ruling",
        "name": {
            "sq": "Ankesë kundër aktvendimit",
            "en": "Appeal against ruling",
            "zh": "对裁定提出上诉",
        },
        "legal_basis": "LPK neni 209",
        "practice_area": "civil",
        "trigger_event": "ruling_served",
        "days": 7,
    },
    {
        "code": "civil.answer_to_claim",
        "name": {
            "sq": "Përgjigje në padi",
            "en": "Answer to the claim",
            "zh": "对起诉状的答辩",
        },
        "legal_basis": "LPK neni 395",
        "practice_area": "civil",
        "trigger_event": "claim_served",
        "days": 15,
    },
    {
        "code": "civil.revision",
        "name": {"sq": "Revizion", "en": "Revision", "zh": "再审申请"},
        "legal_basis": "LPK neni 211",
        "practice_area": "civil",
        "trigger_event": "second_instance_served",
        "days": 30,
    },
    {
        "code": "criminal.appeal_judgment",
        "name": {
            "sq": "Ankesë kundër aktgjykimit penal",
            "en": "Appeal against criminal judgment",
            "zh": "对刑事判决提出上诉",
        },
        "legal_basis": "KPPRK neni 380",
        "practice_area": "criminal",
        "trigger_event": "judgment_served",
        "days": 15,
    },
    {
        "code": "criminal.objection_indictment",
        "name": {
            "sq": "Kundërshtim i aktakuzës",
            "en": "Objection to indictment",
            "zh": "对起诉书提出异议",
        },
        "legal_basis": "KPPRK neni 249",
        "practice_area": "criminal",
        "trigger_event": "indictment_served",
        "days": 30,
    },
    {
        "code": "administrative.lawsuit",
        "name": {
            "sq": "Padi në konflikt administrativ",
            "en": "Administrative dispute lawsuit",
            "zh": "行政诉讼起诉",
        },
        "legal_basis": "LKA / Ligji Nr. 03/L-202 neni 27",
        "practice_area": "administrative",
        "trigger_event": "decision_served",
        "days": 30,
    },
    {
        "code": "administrative.appeal_decision",
        "name": {
            "sq": "Ankesë administrative",
            "en": "Administrative appeal",
            "zh": "行政复议申请",
        },
        "legal_basis": "LKA neni 130",
        "practice_area": "administrative",
        "trigger_event": "decision_served",
        "days": 15,
    },
    {
        "code": "labor.protection_claim",
        "name": {
            "sq": "Kërkesë për mbrojtjen e të drejtave nga marrëdhënia e punës",
            "en": "Labor rights protection claim",
            "zh": "劳动权利保护请求",
        },
        "legal_basis": "Ligji i Punës Nr. 03/L-212 neni 79",
        "practice_area": "labor",
        "trigger_event": "violation_known",
        "days": 30,
    },
]

# Kosovo public holidays (fixed-date ones; movable religious holidays are
# entered per-year by the lawyer or a future update).
XK_HOLIDAYS_FIXED = [
    ("01-01", {"sq": "Viti i Ri", "en": "New Year", "zh": "新年"}),
    ("01-02", {"sq": "Viti i Ri (dita e dytë)", "en": "New Year (day 2)", "zh": "新年第二天"}),
    ("02-17", {"sq": "Dita e Pavarësisë", "en": "Independence Day", "zh": "独立日"}),
    ("04-09", {"sq": "Dita e Kushtetutës", "en": "Constitution Day", "zh": "宪法日"}),
    ("05-01", {"sq": "Dita e Punës", "en": "Labour Day", "zh": "劳动节"}),
    ("05-09", {"sq": "Dita e Evropës", "en": "Europe Day", "zh": "欧洲日"}),
    ("12-25", {"sq": "Krishtlindjet", "en": "Christmas", "zh": "圣诞节"}),
]

XK_TEMPLATES = [
    {
        "code": "civil.lawsuit",
        "locale": "sq",
        "practice_area": "civil",
        "name": {"sq": "Padi civile", "en": "Civil lawsuit", "zh": "民事起诉状"},
        "variables": [
            {"name": "court_name", "label": {"sq": "Gjykata", "en": "Court", "zh": "法院"}},
            {"name": "claim_subject", "label": {"sq": "Objekti i padisë", "en": "Subject of claim", "zh": "诉讼标的"}},
            {"name": "claim_value", "label": {"sq": "Vlera e kontestit", "en": "Claim value", "zh": "争议金额"}},
            {"name": "facts", "label": {"sq": "Faktet", "en": "Facts", "zh": "事实"}},
            {"name": "evidence", "label": {"sq": "Provat", "en": "Evidence", "zh": "证据"}},
            {"name": "request", "label": {"sq": "Kërkesa (petitumi)", "en": "Relief sought", "zh": "诉讼请求"}},
        ],
        "body": """{{ court_name }}

PADI

Paditësi: {{ client_name }}{% if client_address %}, {{ client_address }}{% endif %}
i/e përfaqësuar nga {{ lawyer_name }}, avokat/e

I padituri: {{ opposing_name }}

Objekti i padisë: {{ claim_subject }}
Vlera e kontestit: {{ claim_value }}

I. BAZA FAKTIKE

{{ facts }}

II. PROVAT

{{ evidence }}

III. BAZA JURIDIKE

Padia paraqitet në pajtim me nenin 252 e në vijim të Ligjit Nr. 03/L-006
për Procedurën Kontestimore.

IV. PETITUMI

Paditësi i propozon gjykatës që pas administrimit të provave të nxjerrë:

AKTGJYKIM

{{ request }}

{{ city }}, më {{ date }}

Përfaqësuesi i paditësit
{{ lawyer_name }}, avokat/e
""",
    },
    {
        "code": "civil.appeal",
        "locale": "sq",
        "practice_area": "civil",
        "name": {"sq": "Ankesë kundër aktgjykimit", "en": "Appeal", "zh": "上诉状"},
        "variables": [
            {"name": "court_name", "label": {"sq": "Gjykata e Apelit", "en": "Appeal court", "zh": "上诉法院"}},
            {"name": "first_court", "label": {"sq": "Gjykata e shkallës së parë", "en": "First instance court", "zh": "一审法院"}},
            {"name": "judgment_ref", "label": {"sq": "Numri i aktgjykimit", "en": "Judgment number", "zh": "判决书编号"}},
            {"name": "grounds", "label": {"sq": "Bazat e ankesës", "en": "Grounds of appeal", "zh": "上诉理由"}},
            {"name": "request", "label": {"sq": "Propozimi", "en": "Request", "zh": "请求"}},
        ],
        "body": """{{ court_name }}
përmes
{{ first_court }}

ANKESË

kundër Aktgjykimit {{ judgment_ref }} të {{ first_court }}

Ankuesi: {{ client_name }}
i/e përfaqësuar nga {{ lawyer_name }}, avokat/e

Në afatin ligjor prej 15 ditësh sipas nenit 176 të LPK-së, paraqes këtë
ankesë për shkak të:

{{ grounds }}

PROPOZIMI

{{ request }}

{{ city }}, më {{ date }}

Përfaqësuesi i ankuesit
{{ lawyer_name }}, avokat/e
""",
    },
    {
        "code": "general.power_of_attorney",
        "locale": "sq",
        "practice_area": "other",
        "name": {"sq": "Autorizim (prokurë)", "en": "Power of attorney", "zh": "授权委托书"},
        "variables": [
            {"name": "scope", "label": {"sq": "Fushëveprimi i autorizimit", "en": "Scope", "zh": "授权范围"}},
        ],
        "body": """AUTORIZIM

Unë, {{ client_name }}{% if client_address %}, me adresë {{ client_address }}{% endif %},
autorizoj avokatin/en {{ lawyer_name }} që të më përfaqësojë në:

{{ scope }}

Autorizimi përfshin ndërmarrjen e të gjitha veprimeve procedurale të nevojshme
për mbrojtjen e interesave të mia, në pajtim me ligjin në fuqi.

{{ city }}, më {{ date }}

Autorizuesi                                    Avokati/ja
{{ client_name }}                              {{ lawyer_name }}
""",
    },
]
