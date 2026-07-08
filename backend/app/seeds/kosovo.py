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
    {
        "code": "civil.payment_order_objection",
        "locale": "sq",
        "practice_area": "civil",
        "name": {
            "sq": "Prapësim kundër urdhërpagesës",
            "en": "Objection to payment order",
            "zh": "支付令异议书",
        },
        "variables": [
            {"name": "court_name", "label": {"sq": "Gjykata", "en": "Court", "zh": "法院"}},
            {"name": "order_ref", "label": {"sq": "Numri i urdhërpagesës", "en": "Payment order no.", "zh": "支付令编号"}},
            {"name": "order_date", "label": {"sq": "Data e pranimit të urdhërpagesës", "en": "Date order received", "zh": "收到日期"}},
            {"name": "grounds", "label": {"sq": "Arsyet e prapësimit", "en": "Grounds", "zh": "异议理由"}},
        ],
        "body": """{{ court_name }}

PRAPËSIM

kundër Urdhërpagesës {{ order_ref }}, pranuar më {{ order_date }}

Debitori: {{ client_name }}{% if client_address %}, {{ client_address }}{% endif %}
i/e përfaqësuar nga {{ lawyer_name }}, avokat/e

Në afatin ligjor, në pajtim me dispozitat e Ligjit Nr. 03/L-006 për Procedurën
Kontestimore që rregullojnë procedurën e lëshimit të urdhërpagesës, paraqes
prapësim kundër urdhërpagesës së cekur më lart, për këto arsye:

{{ grounds }}

PROPOZIMI

I propozoj gjykatës që ta anulojë urdhërpagesën dhe çështja të vazhdojë
sipas rregullave të procedurës kontestimore.

{{ city }}, më {{ date }}

Përfaqësuesi i debitorit
{{ lawyer_name }}, avokat/e
""",
    },
    {
        "code": "labor.lawsuit",
        "locale": "sq",
        "practice_area": "labor",
        "name": {
            "sq": "Padi nga marrëdhënia e punës",
            "en": "Employment lawsuit",
            "zh": "劳动争议起诉状",
        },
        "variables": [
            {"name": "court_name", "label": {"sq": "Gjykata", "en": "Court", "zh": "法院"}},
            {"name": "employer_name", "label": {"sq": "Punëdhënësi (i padituri)", "en": "Employer", "zh": "用人单位"}},
            {"name": "violation", "label": {"sq": "Shkelja e pretenduar", "en": "Alleged violation", "zh": "违法行为"}},
            {"name": "facts", "label": {"sq": "Faktet", "en": "Facts", "zh": "事实"}},
            {"name": "request", "label": {"sq": "Kërkesa (petitumi)", "en": "Relief sought", "zh": "诉讼请求"}},
        ],
        "body": """{{ court_name }}

PADI
nga marrëdhënia e punës

Paditësi: {{ client_name }}{% if client_address %}, {{ client_address }}{% endif %}
i/e përfaqësuar nga {{ lawyer_name }}, avokat/e

I padituri: {{ employer_name }}

Objekti: {{ violation }}

I. BAZA FAKTIKE

{{ facts }}

II. BAZA JURIDIKE

Padia bazohet në Ligjin Nr. 03/L-212 i Punës dhe paraqitet brenda afatit të
paraparë me nenin 87 të tij, si dhe në pajtim me Ligjin Nr. 03/L-006 për
Procedurën Kontestimore. Kontesti nga marrëdhënia e punës është procedurë
me përparësi sipas nenit 475 të LPK-së.

III. PETITUMI

{{ request }}

{{ city }}, më {{ date }}

Përfaqësuesi i paditësit
{{ lawyer_name }}, avokat/e
""",
    },
    {
        "code": "administrative.lawsuit",
        "locale": "sq",
        "practice_area": "administrative",
        "name": {
            "sq": "Padi në konflikt administrativ",
            "en": "Administrative dispute lawsuit",
            "zh": "行政诉讼起诉状",
        },
        "variables": [
            {"name": "court_name", "label": {"sq": "Gjykata", "en": "Court", "zh": "法院"}},
            {"name": "authority", "label": {"sq": "Organi publik (i padituri)", "en": "Public authority", "zh": "行政机关"}},
            {"name": "act_ref", "label": {"sq": "Akti administrativ (numri/data)", "en": "Administrative act", "zh": "行政行为"}},
            {"name": "grounds", "label": {"sq": "Arsyet e paligjshmërisë", "en": "Grounds of illegality", "zh": "违法理由"}},
            {"name": "request", "label": {"sq": "Kërkesa", "en": "Relief sought", "zh": "请求"}},
        ],
        "body": """{{ court_name }}
Departamenti për Çështje Administrative

PADI
për anulimin e aktit administrativ

Paditësi: {{ client_name }}{% if client_address %}, {{ client_address }}{% endif %}
i/e përfaqësuar nga {{ lawyer_name }}, avokat/e

I padituri: {{ authority }}

Akti i kontestuar: {{ act_ref }}

I. ARSYET E PALIGJSHMËRISË

{{ grounds }}

II. BAZA JURIDIKE

Padia paraqitet në pajtim me Ligjin Nr. 08/L-182 për Konfliktet Administrative,
brenda afatit tridhjetëditor nga dita e dorëzimit të aktit administrativ.

III. KËRKESA

{{ request }}

{{ city }}, më {{ date }}

Përfaqësuesi i paditësit
{{ lawyer_name }}, avokat/e
""",
    },
    {
        "code": "commercial.demand_letter",
        "locale": "sq",
        "practice_area": "commercial",
        "name": {
            "sq": "Vërejtje para padisë (kërkesë për pagesë)",
            "en": "Demand letter",
            "zh": "催告函",
        },
        "variables": [
            {"name": "debtor_name", "label": {"sq": "Debitori", "en": "Debtor", "zh": "债务人"}},
            {"name": "debt_amount", "label": {"sq": "Shuma e borxhit (EUR)", "en": "Debt amount", "zh": "欠款金额"}},
            {"name": "debt_basis", "label": {"sq": "Baza e borxhit (kontrata/fatura)", "en": "Basis of debt", "zh": "债务依据"}},
            {"name": "payment_deadline", "label": {"sq": "Afati i pagesës (ditë)", "en": "Payment deadline (days)", "zh": "付款期限"}},
            {"name": "bank_details", "label": {"sq": "Llogaria bankare", "en": "Bank account", "zh": "银行账户"}},
        ],
        "body": """{{ debtor_name }}

VËREJTJE PARA PADISË
Kërkesë për pagesën e borxhit

I/E nderuar,

Në emër të klientit tonë {{ client_name }}, ju njoftojmë se ndaj jush
evidentohet borxh i papaguar në shumë prej {{ debt_amount }} EUR, me bazë:

{{ debt_basis }}

Në pajtim me Ligjin Nr. 04/L-077 për Marrëdhëniet e Detyrimeve, ju ftojmë që
brenda {{ payment_deadline }} ditësh nga pranimi i kësaj shkrese ta paguani
shumën e cekur në llogarinë:

{{ bank_details }}

Në të kundërtën, do të detyrohemi ta iniciojmë procedurën gjyqësore
(përfshirë propozimin për urdhërpagesë), me ç'rast do të kërkohen edhe
kamatëvonesa ligjore dhe shpenzimet e procedurës.

{{ city }}, më {{ date }}

Me respekt,
{{ lawyer_name }}, avokat/e
""",
    },
    {
        "code": "commercial.nda",
        "locale": "sq",
        "practice_area": "commercial",
        "name": {
            "sq": "Marrëveshje konfidencialiteti (NDA)",
            "en": "Non-disclosure agreement",
            "zh": "保密协议",
        },
        "variables": [
            {"name": "party_two", "label": {"sq": "Pala e dytë", "en": "Second party", "zh": "另一方"}},
            {"name": "purpose", "label": {"sq": "Qëllimi i shkëmbimit të informacionit", "en": "Purpose", "zh": "目的"}},
            {"name": "duration_years", "label": {"sq": "Kohëzgjatja (vite)", "en": "Duration (years)", "zh": "期限（年）"}},
            {"name": "penalty", "label": {"sq": "Dënimi kontraktual (EUR)", "en": "Contractual penalty", "zh": "违约金"}},
        ],
        "body": """MARRËVESHJE KONFIDENCIALITETI

E lidhur më {{ date }} në {{ city }}, ndërmjet:

1. {{ client_name }}{% if client_address %}, me seli në {{ client_address }}{% endif %} ("Pala e Parë"), dhe
2. {{ party_two }} ("Pala e Dytë")

Neni 1 — Qëllimi
Palët synojnë të shkëmbejnë informacion konfidencial për qëllim të:
{{ purpose }}

Neni 2 — Informacioni konfidencial
Informacion konfidencial konsiderohet çdo e dhënë afariste, teknike, financiare
ose juridike e shpalosur nga njëra palë tek tjetra, në çfarëdo forme, përveç
informacionit që është publikisht i njohur pa faj të palës pranuese.

Neni 3 — Detyrimet
Pala pranuese detyrohet ta ruajë fshehtësinë e informacionit, të mos ia
shpalosë atë palëve të treta pa pëlqim paraprak me shkrim dhe ta përdorë
vetëm për qëllimin e përcaktuar në nenin 1. Detyrimi vlen edhe për
punonjësit dhe bashkëpunëtorët e palëve.

Neni 4 — Kohëzgjatja
Kjo marrëveshje vlen {{ duration_years }} vite nga data e nënshkrimit.
Detyrimi i ruajtjes së fshehtësisë mbetet në fuqi edhe pas skadimit të saj.

Neni 5 — Dënimi kontraktual
Për çdo shkelje të kësaj marrëveshjeje, pala shkelëse i detyrohet palës
tjetër dënim kontraktual prej {{ penalty }} EUR, pa e cenuar të drejtën për
shpërblimin e dëmit real më të lartë, në pajtim me Ligjin Nr. 04/L-077 për
Marrëdhëniet e Detyrimeve.

Neni 6 — E drejta e zbatueshme dhe juridiksioni
Për këtë marrëveshje vlen e drejta e Republikës së Kosovës. Kontestet i
zgjidh gjykata kompetente në {{ city }}.

Pala e Parë                                    Pala e Dytë
{{ client_name }}                              {{ party_two }}
""",
    },
    {
        "code": "commercial.service_contract",
        "locale": "sq",
        "practice_area": "commercial",
        "name": {
            "sq": "Kontratë për ofrimin e shërbimeve",
            "en": "Service agreement",
            "zh": "服务合同",
        },
        "variables": [
            {"name": "provider_name", "label": {"sq": "Ofruesi i shërbimit", "en": "Service provider", "zh": "服务提供方"}},
            {"name": "services", "label": {"sq": "Përshkrimi i shërbimeve", "en": "Services", "zh": "服务内容"}},
            {"name": "price", "label": {"sq": "Çmimi dhe mënyra e pagesës", "en": "Price and payment", "zh": "价格与支付"}},
            {"name": "term", "label": {"sq": "Kohëzgjatja e kontratës", "en": "Term", "zh": "合同期限"}},
            {"name": "notice_days", "label": {"sq": "Afati i njoftimit për shkëputje (ditë)", "en": "Termination notice (days)", "zh": "解约通知期"}},
        ],
        "body": """KONTRATË PËR OFRIMIN E SHËRBIMEVE

E lidhur më {{ date }} në {{ city }}, ndërmjet:

1. {{ client_name }}{% if client_address %}, me seli në {{ client_address }}{% endif %} ("Porositësi"), dhe
2. {{ provider_name }} ("Ofruesi")

Neni 1 — Objekti i kontratës
Ofruesi merr përsipër t'i kryejë për Porositësin këto shërbime:
{{ services }}

Neni 2 — Çmimi dhe pagesa
{{ price }}
Pagesa kryhet në bazë të faturës së lëshuar nga Ofruesi, brenda afatit të
cekur në faturë. Për vonesë zbatohet kamatëvonesa sipas Ligjit Nr. 04/L-077
për Marrëdhëniet e Detyrimeve.

Neni 3 — Kohëzgjatja
{{ term }}

Neni 4 — Shkëputja
Secila palë mund ta shkëpusë kontratën me njoftim me shkrim
{{ notice_days }} ditë përpara. Shkëputja nuk i prek detyrimet e krijuara
deri në ditën e ndërprerjes.

Neni 5 — Konfidencialiteti
Palët e ruajnë fshehtësinë e informacionit afarist të njëra-tjetrës të
mësuar gjatë zbatimit të kësaj kontrate.

Neni 6 — E drejta e zbatueshme dhe kontestet
Për këtë kontratë vlen e drejta e Republikës së Kosovës, në veçanti Ligji
Nr. 04/L-077 për Marrëdhëniet e Detyrimeve. Kontestet i zgjidh gjykata
kompetente në {{ city }}.

Porositësi                                     Ofruesi
{{ client_name }}                              {{ provider_name }}
""",
    },
    {
        "code": "labor.employment_contract",
        "locale": "sq",
        "practice_area": "labor",
        "name": {
            "sq": "Kontratë pune",
            "en": "Employment contract",
            "zh": "劳动合同",
        },
        "variables": [
            {"name": "employee_name", "label": {"sq": "I punësuari", "en": "Employee", "zh": "员工"}},
            {"name": "position", "label": {"sq": "Pozita / përshkrimi i punës", "en": "Position", "zh": "职位"}},
            {"name": "salary", "label": {"sq": "Paga bruto (EUR)", "en": "Gross salary", "zh": "工资"}},
            {"name": "start_date", "label": {"sq": "Data e fillimit të punës", "en": "Start date", "zh": "入职日期"}},
            {"name": "contract_term", "label": {"sq": "Kohëzgjatja (e pacaktuar / e caktuar deri më)", "en": "Term", "zh": "期限"}},
            {"name": "probation", "label": {"sq": "Puna provuese (muaj, max 6)", "en": "Probation (months)", "zh": "试用期"}},
        ],
        "body": """KONTRATË PUNE
(në pajtim me nenin 10 dhe 11 të Ligjit Nr. 03/L-212 i Punës)

E lidhur më {{ date }} në {{ city }}, ndërmjet:

Punëdhënësi: {{ client_name }}{% if client_address %}, me seli në {{ client_address }}{% endif %}
I punësuari: {{ employee_name }}

Neni 1 — Pozita dhe detyrat e punës
I punësuari themelon marrëdhënie pune në pozitën: {{ position }}

Neni 2 — Kohëzgjatja
Kontrata lidhet për: {{ contract_term }}
Puna fillon më {{ start_date }}. Puna provuese: {{ probation }} muaj.

Neni 3 — Paga
Paga bazë bruto është {{ salary }} EUR në muaj, e pagueshme më së voni deri
në fund të muajit pasues, në llogarinë bankare të të punësuarit.

Neni 4 — Orari i punës
Orari i plotë i punës është 40 orë në javë, në pajtim me nenin 20 të Ligjit
të Punës. Puna jashtë orarit kompensohet sipas ligjit.

Neni 5 — Pushimet
I punësuari ka të drejtë në pushim vjetor të paguar prej së paku katër (4)
javësh për vit kalendarik (neni 32 i Ligjit të Punës), pushim javor dhe
pushime të tjera sipas ligjit dhe aktit të brendshëm të punëdhënësit.

Neni 6 — Ndërprerja e marrëdhënies së punës
Marrëdhënia e punës ndërpritet në mënyrat dhe me afatet e parapara me
Ligjin Nr. 03/L-212 i Punës (nenet 67-78).

Neni 7 — Dispozita përfundimtare
Për çështjet e parregulluara me këtë kontratë zbatohet Ligji Nr. 03/L-212
i Punës dhe aktet nënligjore në fuqi. Kontrata lidhet në dy ekzemplarë.

Punëdhënësi                                    I punësuari
{{ client_name }}                              {{ employee_name }}
""",
    },
    {
        "code": "general.legal_opinion",
        "locale": "sq",
        "practice_area": "other",
        "name": {
            "sq": "Opinion ligjor",
            "en": "Legal opinion",
            "zh": "法律意见书",
        },
        "variables": [
            {"name": "recipient", "label": {"sq": "Drejtuar (klienti/organi)", "en": "Addressed to", "zh": "致"}},
            {"name": "question", "label": {"sq": "Çështja juridike", "en": "Legal question", "zh": "法律问题"}},
            {"name": "facts", "label": {"sq": "Gjendja faktike", "en": "Facts", "zh": "事实"}},
            {"name": "analysis", "label": {"sq": "Analiza juridike", "en": "Legal analysis", "zh": "法律分析"}},
            {"name": "conclusion", "label": {"sq": "Përfundimi dhe rekomandimi", "en": "Conclusion", "zh": "结论"}},
        ],
        "body": """OPINION LIGJOR

Për: {{ recipient }}
Nga: {{ lawyer_name }}, avokat/e
Data: {{ date }}

I. ÇËSHTJA JURIDIKE

{{ question }}

II. GJENDJA FAKTIKE

{{ facts }}

III. ANALIZA JURIDIKE

{{ analysis }}

IV. PËRFUNDIMI DHE REKOMANDIMI

{{ conclusion }}

Ky opinion bazohet në legjislacionin e Republikës së Kosovës në fuqi në
datën e lëshimit dhe në gjendjen faktike të prezantuar nga klienti. Për
çdo ndryshim të rrethanave, opinioni duhet të rishikohet.

{{ lawyer_name }}, avokat/e
{{ city }}, më {{ date }}
""",
    },
    {
        "code": "commercial.due_diligence_checklist",
        "locale": "sq",
        "practice_area": "commercial",
        "name": {
            "sq": "Listë kontrolli — Due diligence ligjor",
            "en": "Legal due diligence checklist",
            "zh": "法律尽职调查清单",
        },
        "variables": [
            {"name": "target_company", "label": {"sq": "Shoqëria objekt (target)", "en": "Target company", "zh": "目标公司"}},
            {"name": "transaction", "label": {"sq": "Transaksioni (blerje aksionesh/asetesh)", "en": "Transaction", "zh": "交易类型"}},
        ],
        "body": """DUE DILIGENCE LIGJOR — LISTË KONTROLLI

Shoqëria objekt: {{ target_company }}
Transaksioni: {{ transaction }}
Përgatitur nga: {{ lawyer_name }}, avokat/e · {{ date }}

I. STATUSI KORPORATIV (Ligji Nr. 06/L-016 për Shoqëritë Tregtare)
[ ] Certifikata e regjistrimit në ARBK dhe informatat e biznesit
[ ] Statuti dhe marrëveshja e shoqërisë (versionet aktuale)
[ ] Struktura e pronësisë; librat e aksioneve/pjesëve
[ ] Vendimet e asamblesë dhe të bordit (3 vitet e fundit)
[ ] Prokurat dhe përfaqësuesit e autorizuar

II. KONTRATAT MATERIALE (Ligji Nr. 04/L-077 — LMD)
[ ] Kontratat me klientët dhe furnitorët kryesorë
[ ] Kontratat e kredisë, garancitë, pengjet dhe hipotekat
[ ] Kontratat e qirasë dhe të drejtat mbi paluajtshmëritë
[ ] Klauzolat "change of control" në kontratat ekzistuese

III. PUNËSIMI (Ligji Nr. 03/L-212 i Punës)
[ ] Lista e punonjësve, kontratat e punës, pagat
[ ] Kontratat e menaxhmentit dhe klauzolat e moskonkurrencës
[ ] Kontestet e punës të hapura ose të pritshme

IV. PASURIA DHE TË DREJTAT
[ ] Certifikatat e pronësisë (kadastri), barrët dhe servitutet
[ ] Pronësia intelektuale: marka, patenta, domene
[ ] Licencat dhe lejet e veprimtarisë

V. KONTESTET DHE PAJTUESHMËRIA
[ ] Proceset gjyqësore aktive (si paditës/i paditur)
[ ] Procedurat përmbarimore dhe tatimore
[ ] Pajtueshmëria me Ligjin Nr. 06/L-082 për Mbrojtjen e të Dhënave Personale
[ ] Detyrimet tatimore dhe kontributet (vërtetimi i ATK-së)

VI. GJETJET DHE VLERËSIMI I RREZIKUT
(Plotësohet pas shqyrtimit të dokumenteve)

{{ city }}, më {{ date }}
{{ lawyer_name }}, avokat/e
""",
    },
]
