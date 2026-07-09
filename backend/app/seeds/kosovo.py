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
        "name": {"sq": "Kosova", "en": "Kosovo", "zh": "科索沃", "sr": "Kosovo", "tr": "Kosova", "bs": "Kosovo"},
    },
    {
        "code": "GB",
        "name": {"sq": "Anglia dhe Uellsi", "en": "England and Wales", "zh": "英格兰和威尔士", "sr": "Engleska i Vels", "tr": "İngiltere ve Galler", "bs": "Engleska i Vels"},
        "is_active": False,
    },
    {
        "code": "CN",
        "name": {"sq": "Kina", "en": "China", "zh": "中国", "sr": "Kina", "tr": "Çin", "bs": "Kina"},
        "is_active": False,
    },
    {
        "code": "INTL",
        "name": {"sq": "Ndërkombëtar", "en": "International", "zh": "国际", "sr": "Međunarodno", "tr": "Uluslararası", "bs": "Međunarodno"},
        "is_active": False,
    },
]

XK_DEADLINE_RULES = [
    {
        "code": "civil.appeal_judgment",
        "name": {
            "sq": "Ankesë kundër aktgjykimit",
            "en": "Appeal against judgment",
            "zh": "对判决提出上诉", "sr": "Žalba protiv presude", "tr": "Karara karşı istinaf", "bs": "Žalba protiv presude",
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
            "zh": "对裁定提出上诉", "sr": "Žalba protiv rešenja", "tr": "Ara karara karşı itiraz", "bs": "Žalba protiv rješenja",
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
            "zh": "对起诉状的答辩", "sr": "Odgovor na tužbu", "tr": "Davaya cevap", "bs": "Odgovor na tužbu",
        },
        "legal_basis": "LPK neni 395",
        "practice_area": "civil",
        "trigger_event": "claim_served",
        "days": 15,
    },
    {
        "code": "civil.revision",
        "name": {"sq": "Revizion", "en": "Revision", "zh": "再审申请", "sr": "Revizija", "tr": "Revizyon (temyiz)", "bs": "Revizija"},
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
            "zh": "对刑事判决提出上诉", "sr": "Žalba protiv krivične presude", "tr": "Ceza hükmüne karşı istinaf", "bs": "Žalba protiv krivične presude",
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
            "zh": "对起诉书提出异议", "sr": "Prigovor na optužnicu", "tr": "İddianameye itiraz", "bs": "Prigovor na optužnicu",
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
            "zh": "行政诉讼起诉", "sr": "Tužba u upravnom sporu", "tr": "İdari dava", "bs": "Tužba u upravnom sporu",
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
            "zh": "行政复议申请", "sr": "Upravna žalba", "tr": "İdari itiraz", "bs": "Upravna žalba",
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
            "zh": "劳动权利保护请求", "sr": "Zahtev za zaštitu prava iz radnog odnosa", "tr": "İş ilişkisinden doğan hakların korunması talebi", "bs": "Zahtjev za zaštitu prava iz radnog odnosa",
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
    ("01-01", {"sq": "Viti i Ri", "en": "New Year", "zh": "新年", "sr": "Nova godina", "tr": "Yılbaşı", "bs": "Nova godina"}),
    ("01-02", {"sq": "Viti i Ri (dita e dytë)", "en": "New Year (day 2)", "zh": "新年第二天", "sr": "Nova godina (drugi dan)", "tr": "Yılbaşı (ikinci gün)", "bs": "Nova godina (drugi dan)"}),
    ("02-17", {"sq": "Dita e Pavarësisë", "en": "Independence Day", "zh": "独立日", "sr": "Dan nezavisnosti", "tr": "Bağımsızlık Günü", "bs": "Dan nezavisnosti"}),
    ("04-09", {"sq": "Dita e Kushtetutës", "en": "Constitution Day", "zh": "宪法日", "sr": "Dan ustava", "tr": "Anayasa Günü", "bs": "Dan ustava"}),
    ("05-01", {"sq": "Dita e Punës", "en": "Labour Day", "zh": "劳动节", "sr": "Praznik rada", "tr": "İşçi Bayramı", "bs": "Praznik rada"}),
    ("05-09", {"sq": "Dita e Evropës", "en": "Europe Day", "zh": "欧洲日", "sr": "Dan Evrope", "tr": "Avrupa Günü", "bs": "Dan Evrope"}),
    ("12-25", {"sq": "Krishtlindjet", "en": "Christmas", "zh": "圣诞节", "sr": "Božić", "tr": "Noel", "bs": "Božić"}),
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
        "name": {"sq": "Ankesë kundër aktgjykimit", "en": "Appeal", "zh": "上诉状", "sr": "Žalba protiv presude", "tr": "Karara karşı istinaf", "bs": "Žalba protiv presude"},
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
            "zh": "行政诉讼起诉状", "sr": "Tužba u upravnom sporu", "tr": "İdari dava", "bs": "Tužba u upravnom sporu",
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
    # ------------------------------------------------------------------
    # Serbian versions of client-facing templates (Law 02/L-37: Serbian is
    # an official language state-wide). AI-translated legal text — each is
    # marked "requires lawyer review" and must be verified by the lawyer
    # before first use.
    # ------------------------------------------------------------------
    {
        "code": "general.power_of_attorney",
        "locale": "sr",
        "practice_area": "other",
        "name": {
            "sq": "Autorizim (prokurë) — serbisht [kërkon rishikim nga avokati]",
            "sr": "Punomoćje [zahteva proveru advokata]",
            "en": "Power of attorney — Serbian [requires lawyer review]",
            "zh": "授权委托书 — 塞尔维亚语[需律师审核]",
        },
        "variables": [
            {"name": "scope", "label": {
                "sq": "Fushëveprimi i autorizimit", "sr": "Obim punomoćja",
                "en": "Scope", "zh": "授权范围"}},
        ],
        "body": """PUNOMOĆJE

Ja, {{ client_name }}{% if client_address %}, sa adresom {{ client_address }}{% endif %},
ovlašćujem advokata/advokaticu {{ lawyer_name }} da me zastupa u:

{{ scope }}

Punomoćje obuhvata preduzimanje svih potrebnih procesnih radnji za zaštitu
mojih interesa, u skladu sa važećim zakonom.

{{ city }}, dana {{ date }}

Vlastodavac                                    Advokat/ica
{{ client_name }}                              {{ lawyer_name }}
""",
    },
    {
        "code": "commercial.nda",
        "locale": "sr",
        "practice_area": "commercial",
        "name": {
            "sq": "Marrëveshje konfidencialiteti (NDA) — serbisht [kërkon rishikim nga avokati]",
            "sr": "Ugovor o poverljivosti (NDA) [zahteva proveru advokata]",
            "en": "Non-disclosure agreement — Serbian [requires lawyer review]",
            "zh": "保密协议 — 塞尔维亚语[需律师审核]",
        },
        "variables": [
            {"name": "party_two", "label": {
                "sq": "Pala e dytë", "sr": "Druga strana",
                "en": "Second party", "zh": "另一方"}},
            {"name": "purpose", "label": {
                "sq": "Qëllimi i shkëmbimit të informacionit", "sr": "Svrha razmene informacija",
                "en": "Purpose", "zh": "目的"}},
            {"name": "duration_years", "label": {
                "sq": "Kohëzgjatja (vite)", "sr": "Trajanje (godine)",
                "en": "Duration (years)", "zh": "期限（年）"}},
            {"name": "penalty", "label": {
                "sq": "Dënimi kontraktual (EUR)", "sr": "Ugovorna kazna (EUR)",
                "en": "Contractual penalty", "zh": "违约金"}},
        ],
        "body": """UGOVOR O POVERLJIVOSTI

Zaključen dana {{ date }} u {{ city }}, između:

1. {{ client_name }}{% if client_address %}, sa sedištem u {{ client_address }}{% endif %} ("Prva strana"), i
2. {{ party_two }} ("Druga strana")

Član 1 — Svrha
Strane nameravaju da razmene poverljive informacije u svrhu:
{{ purpose }}

Član 2 — Poverljive informacije
Poverljivom informacijom smatra se svaki poslovni, tehnički, finansijski ili
pravni podatak koji jedna strana otkrije drugoj, u bilo kom obliku, osim
informacija koje su javno poznate bez krivice strane primaoca.

Član 3 — Obaveze
Strana primalac se obavezuje da čuva tajnost informacija, da ih ne otkriva
trećim licima bez prethodne pisane saglasnosti i da ih koristi isključivo za
svrhu utvrđenu u članu 1. Obaveza važi i za zaposlene i saradnike strana.

Član 4 — Trajanje
Ovaj ugovor važi {{ duration_years }} godina od dana potpisivanja. Obaveza
čuvanja tajnosti ostaje na snazi i nakon njegovog isteka.

Član 5 — Ugovorna kazna
Za svaku povredu ovog ugovora, strana koja ga je prekršila duguje drugoj
strani ugovornu kaznu od {{ penalty }} EUR, ne dirajući pravo na naknadu veće
stvarne štete, u skladu sa Zakonom br. 04/L-077 o obligacionim odnosima.

Član 6 — Merodavno pravo i nadležnost
Na ovaj ugovor primenjuje se pravo Republike Kosovo. Sporove rešava nadležni
sud u {{ city }}.

Prva strana                                    Druga strana
{{ client_name }}                              {{ party_two }}
""",
    },
    {
        "code": "commercial.service_contract",
        "locale": "sr",
        "practice_area": "commercial",
        "name": {
            "sq": "Kontratë për ofrimin e shërbimeve — serbisht [kërkon rishikim nga avokati]",
            "sr": "Ugovor o pružanju usluga [zahteva proveru advokata]",
            "en": "Service agreement — Serbian [requires lawyer review]",
            "zh": "服务合同 — 塞尔维亚语[需律师审核]",
        },
        "variables": [
            {"name": "provider_name", "label": {
                "sq": "Ofruesi i shërbimit", "sr": "Pružalac usluge",
                "en": "Service provider", "zh": "服务提供方"}},
            {"name": "services", "label": {
                "sq": "Përshkrimi i shërbimeve", "sr": "Opis usluga",
                "en": "Services", "zh": "服务内容"}},
            {"name": "price", "label": {
                "sq": "Çmimi dhe mënyra e pagesës", "sr": "Cena i način plaćanja",
                "en": "Price and payment", "zh": "价格与支付"}},
            {"name": "term", "label": {
                "sq": "Kohëzgjatja e kontratës", "sr": "Trajanje ugovora",
                "en": "Term", "zh": "合同期限"}},
            {"name": "notice_days", "label": {
                "sq": "Afati i njoftimit për shkëputje (ditë)", "sr": "Otkazni rok (dana)",
                "en": "Termination notice (days)", "zh": "解约通知期"}},
        ],
        "body": """UGOVOR O PRUŽANJU USLUGA

Zaključen dana {{ date }} u {{ city }}, između:

1. {{ client_name }}{% if client_address %}, sa sedištem u {{ client_address }}{% endif %} ("Naručilac"), i
2. {{ provider_name }} ("Pružalac")

Član 1 — Predmet ugovora
Pružalac se obavezuje da za Naručioca izvrši sledeće usluge:
{{ services }}

Član 2 — Cena i plaćanje
{{ price }}
Plaćanje se vrši na osnovu fakture koju izdaje Pružalac, u roku navedenom na
fakturi. Za kašnjenje se primenjuje zatezna kamata prema Zakonu br. 04/L-077
o obligacionim odnosima.

Član 3 — Trajanje
{{ term }}

Član 4 — Raskid
Svaka strana može raskinuti ugovor pisanim obaveštenjem {{ notice_days }}
dana unapred. Raskid ne dira obaveze nastale do dana prestanka.

Član 5 — Poverljivost
Strane čuvaju tajnost poslovnih informacija druge strane saznatih tokom
izvršenja ovog ugovora.

Član 6 — Merodavno pravo i sporovi
Na ovaj ugovor primenjuje se pravo Republike Kosovo, posebno Zakon br.
04/L-077 o obligacionim odnosima. Sporove rešava nadležni sud u {{ city }}.

Naručilac                                      Pružalac
{{ client_name }}                              {{ provider_name }}
""",
    },
]

# ---------------------------------------------------------------------------
# Fee tariff of the Kosovo Bar Association (Tarifa e OAK), in force since
# 1 January 2015 (approved by the OAK Assembly on 20.12.2014). Base amounts;
# the tariff's surcharges (+30%/started hour in sessions, +30% lump sum,
# +50% enforcement clause, +50% per extra party up to 300%) are in `notes`
# so the lawyer applies what fits. Amounts are DATA — editable when the
# tariff changes.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# AML indicators for lawyers (Law No. 05/L-096; based on NjIF-K / FIU-Kosovo
# guidance for reporting entities). Jurisdiction DATA, not code: the checklist
# activates for matters in the law's scope (real estate transactions, managing
# client funds, company formation/management).
# ---------------------------------------------------------------------------

XK_AML_INDICATORS = [
    {
        "code": "aml.cash_large",
        "category": "funds",
        "text": {
            "sq": "Pagesa ose depozita në para të gatshme ≥ 10.000 € (ose disa më të vogla të lidhura)",
            "sr": "Gotovinske uplate ili depoziti ≥ 10.000 € (ili više povezanih manjih)",
            "tr": "≥ 10.000 € nakit ödeme veya depozito (veya bağlantılı birden çok küçük tutar)",
            "bs": "Gotovinske uplate ili depoziti ≥ 10.000 € (ili više povezanih manjih)",
            "en": "Cash payments or deposits ≥ €10,000 (or several linked smaller ones)",
            "zh": "现金支付或存款 ≥ 10,000 欧元（或多笔关联小额）",
        },
    },
    {
        "code": "aml.source_unclear",
        "category": "funds",
        "text": {
            "sq": "Burimi i fondeve i paqartë, i padokumentuar ose në mospërputhje me profilin e klientit",
            "sr": "Poreklo sredstava nejasno, nedokumentovano ili u neskladu sa profilom klijenta",
            "tr": "Fon kaynağı belirsiz, belgesiz veya müvekkil profiliyle uyumsuz",
            "bs": "Porijeklo sredstava nejasno, nedokumentovano ili u neskladu s profilom klijenta",
            "en": "Source of funds unclear, undocumented or inconsistent with the client profile",
            "zh": "资金来源不明、无凭证或与客户情况不符",
        },
    },
    {
        "code": "aml.identity_reluctance",
        "category": "kyc",
        "text": {
            "sq": "Klienti heziton të japë dokument identifikimi ose jep të dhëna kontradiktore",
            "sr": "Klijent okleva da pruži identifikacioni dokument ili daje protivrečne podatke",
            "tr": "Müvekkil kimlik belgesi vermekte isteksiz veya çelişkili bilgiler veriyor",
            "bs": "Klijent oklijeva da pruži identifikacioni dokument ili daje protivrječne podatke",
            "en": "Client reluctant to provide ID or gives contradictory information",
            "zh": "客户不愿提供身份证件或提供矛盾信息",
        },
    },
    {
        "code": "aml.third_party",
        "category": "kyc",
        "text": {
            "sq": "Palë e tretë e paidentifikuar paguan ose udhëzon transaksionin; përfaqësim pa arsye të qartë",
            "sr": "Neidentifikovano treće lice plaća ili usmerava transakciju; zastupanje bez jasnog razloga",
            "tr": "Kimliği belirsiz üçüncü kişi işlemi ödüyor veya yönlendiriyor; açık nedeni olmayan temsil",
            "bs": "Neidentifikovano treće lice plaća ili usmjerava transakciju; zastupanje bez jasnog razloga",
            "en": "Unidentified third party funds or directs the transaction; representation without clear reason",
            "zh": "身份不明的第三方付款或主导交易；无明确理由的代理",
        },
    },
    {
        "code": "aml.property_value",
        "category": "real_estate",
        "text": {
            "sq": "Çmimi i patundshmërisë dukshëm nën/mbi vlerën e tregut, ose rishitje të shpejta të njëpasnjëshme",
            "sr": "Cena nepokretnosti znatno ispod/iznad tržišne vrednosti, ili brze uzastopne preprodaje",
            "tr": "Gayrimenkul fiyatı piyasa değerinin belirgin altında/üstünde veya art arda hızlı satışlar",
            "bs": "Cijena nekretnine znatno ispod/iznad tržišne vrijednosti, ili brze uzastopne preprodaje",
            "en": "Property price clearly below/above market value, or rapid successive resales",
            "zh": "房产价格明显低于/高于市场价，或快速连续转售",
        },
    },
    {
        "code": "aml.shell_company",
        "category": "company",
        "text": {
            "sq": "Themelim kompanish pa aktivitet të qartë ekonomik, me pronarë të fshehur ose struktura komplekse pa arsye",
            "sr": "Osnivanje kompanija bez jasne ekonomske aktivnosti, sa skrivenim vlasnicima ili nepotrebno složenim strukturama",
            "tr": "Açık ekonomik faaliyeti olmayan, gizli sahipli veya gereksiz karmaşık yapılı şirket kuruluşu",
            "bs": "Osnivanje kompanija bez jasne ekonomske aktivnosti, sa skrivenim vlasnicima ili nepotrebno složenim strukturama",
            "en": "Company formation without clear economic activity, hidden owners or needlessly complex structures",
            "zh": "设立无明确经济活动的公司、隐藏所有人或无故复杂的结构",
        },
    },
    {
        "code": "aml.pep",
        "category": "kyc",
        "text": {
            "sq": "Klienti ose pronari përfitues është person i ekspozuar politikisht (PEP)",
            "sr": "Klijent ili stvarni vlasnik je politički eksponirana ličnost (PEP)",
            "tr": "Müvekkil veya gerçek faydalanıcı siyasi nüfuz sahibi kişi (PEP)",
            "bs": "Klijent ili stvarni vlasnik je politički eksponirana osoba (PEP)",
            "en": "Client or beneficial owner is a politically exposed person (PEP)",
            "zh": "客户或受益所有人为政治公众人物（PEP）",
        },
    },
    {
        "code": "aml.geography",
        "category": "kyc",
        "text": {
            "sq": "Lidhje me juridiksione me rrezik të lartë ose nën sanksione",
            "sr": "Veze sa jurisdikcijama visokog rizika ili pod sankcijama",
            "tr": "Yüksek riskli veya yaptırım altındaki ülkelerle bağlantılar",
            "bs": "Veze s jurisdikcijama visokog rizika ili pod sankcijama",
            "en": "Links to high-risk or sanctioned jurisdictions",
            "zh": "与高风险或受制裁司法辖区有关联",
        },
    },
    {
        "code": "aml.urgency",
        "category": "behavior",
        "text": {
            "sq": "Ngutje e pazakontë, mungesë interesi për kushtet, ose gatishmëri për të paguar tarifa dukshëm më të larta",
            "sr": "Neuobičajena žurba, nezainteresovanost za uslove, ili spremnost da se plate znatno veće naknade",
            "tr": "Olağandışı acele, koşullara ilgisizlik veya belirgin şekilde yüksek ücret ödemeye isteklilik",
            "bs": "Neuobičajena žurba, nezainteresovanost za uslove, ili spremnost da se plate znatno veće naknade",
            "en": "Unusual urgency, indifference to terms, or willingness to pay clearly higher fees",
            "zh": "异常急迫、对条款漠不关心或愿意支付明显偏高的费用",
        },
    },
    {
        "code": "aml.transaction_pattern",
        "category": "funds",
        "text": {
            "sq": "Transaksione të shpeshta, të fragmentuara ose kalime fondesh pa logjikë të qartë afariste",
            "sr": "Česte, fragmentisane transakcije ili prenosi sredstava bez jasne poslovne logike",
            "tr": "Sık, parçalanmış işlemler veya açık ticari mantığı olmayan fon transferleri",
            "bs": "Česte, fragmentirane transakcije ili prijenosi sredstava bez jasne poslovne logike",
            "en": "Frequent, fragmented transactions or fund movements without clear business logic",
            "zh": "频繁、拆分的交易或缺乏明确商业逻辑的资金流转",
        },
    },
]

# Matter is "in scope" of Law 05/L-096 for lawyers when it involves these
# activities (art. 16: real estate, managing client money, company formation).
XK_AML_SCOPE_HINT = {
    "sq": "Ligji 05/L-096 zbatohet për avokatët kur lënda përfshin: transaksione patundshmërie, "
          "menaxhim të parave/llogarive të klientit, themelim ose administrim kompanish.",
    "sr": "Zakon 05/L-096 važi za advokate kada predmet obuhvata: transakcije nepokretnostima, "
          "upravljanje novcem/računima klijenta, osnivanje ili upravljanje kompanijama.",
    "tr": "05/L-096 sayılı Kanun, dosya şunları içerdiğinde avukatlar için geçerlidir: gayrimenkul "
          "işlemleri, müvekkil parası/hesap yönetimi, şirket kuruluşu veya yönetimi.",
    "bs": "Zakon 05/L-096 važi za advokate kada predmet obuhvata: transakcije nekretninama, "
          "upravljanje novcem/računima klijenta, osnivanje ili upravljanje kompanijama.",
    "en": "Law 05/L-096 applies to lawyers when the matter involves: real-estate transactions, "
          "managing client money/accounts, company formation or management.",
    "zh": "当案件涉及以下内容时，第05/L-096号法律适用于律师：房地产交易、管理客户资金/账户、公司设立或管理。",
}

XK_FEE_TARIFF = [
    # Nr. tarifor 1-2: criminal defense / representation, per session or action
    {
        "code": "criminal.session.general",
        "tariff_no": "Nr. tarifor 1-2",
        "name": {
            "sq": "Mbrojtja penale — Departamenti i përgjithshëm (seancë/veprim)",
            "en": "Criminal defense — General Department (per session/action)",
            "zh": "刑事辩护 — 普通部门（每次庭审/行动）", "sr": "Krivična odbrana — Opšte odeljenje (ročište/radnja)", "tr": "Ceza savunması — Genel Daire (duruşma/işlem)", "bs": "Krivična odbrana — Opće odjeljenje (ročište/radnja)",
        },
        "practice_area": "criminal",
        "amount": "120.00",
        "unit": "seancë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 1 dhe 2",
        "notes": "Shtesë 30% për çdo orë të filluar; paushalli 30%.",
    },
    {
        "code": "criminal.session.serious_upto10y",
        "tariff_no": "Nr. tarifor 1-2",
        "name": {
            "sq": "Mbrojtja penale — krime të rënda, dënim deri 10 vjet (seancë/veprim)",
            "en": "Criminal defense — serious crimes, up to 10 years (per session/action)",
            "zh": "刑事辩护 — 重罪，十年以下（每次庭审/行动）", "sr": "Krivična odbrana — teška krivična dela, kazna do 10 godina (ročište/radnja)", "tr": "Ceza savunması — ağır suçlar, 10 yıla kadar (duruşma/işlem)", "bs": "Krivična odbrana — teška krivična djela, kazna do 10 godina (ročište/radnja)",
        },
        "practice_area": "criminal",
        "amount": "150.00",
        "unit": "seancë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 1 dhe 2",
        "notes": "Shtesë 30% për çdo orë të filluar; paushalli 30%.",
    },
    {
        "code": "criminal.session.over10y",
        "tariff_no": "Nr. tarifor 1-2",
        "name": {
            "sq": "Mbrojtja penale — dënim 10+ vjet / neni 22 KPPK (seancë/veprim)",
            "en": "Criminal defense — 10+ years / art. 22 CCPK (per session/action)",
            "zh": "刑事辩护 — 十年以上/《刑诉法》第22条（每次庭审/行动）", "sr": "Krivična odbrana — kazna 10+ godina / član 22 ZKPK (ročište/radnja)", "tr": "Ceza savunması — 10+ yıl / ZKPK m. 22 (duruşma/işlem)", "bs": "Krivična odbrana — kazna 10+ godina / član 22 ZKPK (ročište/radnja)",
        },
        "practice_area": "criminal",
        "amount": "200.00",
        "unit": "seancë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 1 dhe 2",
        "notes": "Shtesë 30% për çdo orë të filluar; paushalli 30%.",
    },
    # Nr. tarifor 3-5: criminal submissions
    {
        "code": "criminal.submission.general",
        "tariff_no": "Nr. tarifor 3-5",
        "name": {
            "sq": "Parashtresë penale — Departamenti i përgjithshëm",
            "en": "Criminal submission — General Department",
            "zh": "刑事书状 — 普通部门", "sr": "Krivični podnesak — Opšte odeljenje", "tr": "Ceza dilekçesi — Genel Daire", "bs": "Krivični podnesak — Opće odjeljenje",
        },
        "practice_area": "criminal",
        "amount": "120.00",
        "unit": "parashtresë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 3, 4 dhe 5",
        "notes": "Kallëzim penal, ankesë për paraburgim etj.; paushalli 30%.",
    },
    {
        "code": "criminal.submission.serious_upto10y",
        "tariff_no": "Nr. tarifor 3-5",
        "name": {
            "sq": "Parashtresë penale — krime të rënda, dënim deri 10 vjet",
            "en": "Criminal submission — serious crimes, up to 10 years",
            "zh": "刑事书状 — 重罪，十年以下", "sr": "Krivični podnesak — teška krivična dela, kazna do 10 godina", "tr": "Ceza dilekçesi — ağır suçlar, 10 yıla kadar", "bs": "Krivični podnesak — teška krivična djela, kazna do 10 godina",
        },
        "practice_area": "criminal",
        "amount": "150.00",
        "unit": "parashtresë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 3, 4 dhe 5",
        "notes": "Paushalli 30%.",
    },
    {
        "code": "criminal.submission.over10y",
        "tariff_no": "Nr. tarifor 3-5",
        "name": {
            "sq": "Parashtresë penale — dënim 10+ vjet / neni 22 KPPK",
            "en": "Criminal submission — 10+ years / art. 22 CCPK",
            "zh": "刑事书状 — 十年以上/《刑诉法》第22条", "sr": "Krivični podnesak — kazna 10+ godina / član 22 ZKPK", "tr": "Ceza dilekçesi — 10+ yıl / ZKPK m. 22", "bs": "Krivični podnesak — kazna 10+ godina / član 22 ZKPK",
        },
        "practice_area": "criminal",
        "amount": "200.00",
        "unit": "parashtresë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 3, 4 dhe 5",
        "notes": "Paushalli 30%.",
    },
    # Nr. tarifor 6: civil submissions (claims etc.) by case value
    {
        "code": "civil.claim.small",
        "tariff_no": "Nr. tarifor 6",
        "name": {
            "sq": "Padi/parashtresë — kontest i vlerës së vogël",
            "en": "Claim/submission — small-value dispute",
            "zh": "起诉状/书状 — 小额纠纷", "sr": "Tužba/podnesak — spor male vrednosti", "tr": "Dava/dilekçe — küçük değerli uyuşmazlık", "bs": "Tužba/podnesak — spor male vrijednosti",
        },
        "practice_area": "civil",
        "amount": "60.00",
        "unit": "parashtresë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 6",
        "notes": "Paushalli 30%.",
    },
    {
        "code": "civil.claim.upto_10k",
        "tariff_no": "Nr. tarifor 6",
        "name": {
            "sq": "Padi/parashtresë — vlera deri 10.000 €",
            "en": "Claim/submission — value up to €10,000",
            "zh": "起诉状/书状 — 标的额一万欧元以下", "sr": "Tužba/podnesak — vrednost do 10.000 €", "tr": "Dava/dilekçe — 10.000 €'ya kadar değer", "bs": "Tužba/podnesak — vrijednost do 10.000 €",
        },
        "practice_area": "civil",
        "amount": "80.00",
        "unit": "parashtresë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 6",
        "notes": "Paushalli 30%.",
    },
    {
        "code": "civil.claim.over_10k",
        "tariff_no": "Nr. tarifor 6",
        "name": {
            "sq": "Padi/parashtresë — vlera mbi 10.000 €",
            "en": "Claim/submission — value over €10,000",
            "zh": "起诉状/书状 — 标的额一万欧元以上", "sr": "Tužba/podnesak — vrednost preko 10.000 €", "tr": "Dava/dilekçe — 10.000 € üzeri değer", "bs": "Tužba/podnesak — vrijednost preko 10.000 €",
        },
        "practice_area": "civil",
        "amount": "160.00",
        "unit": "parashtresë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 6",
        "notes": "Paushalli 30%.",
    },
    {
        "code": "civil.enforcement.small",
        "tariff_no": "Nr. tarifor 6",
        "name": {
            "sq": "Propozim për përmbarim — vlera e vogël",
            "en": "Enforcement proposal — small value",
            "zh": "执行申请 — 小额", "sr": "Predlog za izvršenje — mala vrednost", "tr": "İcra talebi — küçük değer", "bs": "Prijedlog za izvršenje — mala vrijednost",
        },
        "practice_area": "civil",
        "amount": "60.00",
        "unit": "parashtresë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 6",
        "notes": "Klauzola për përmbarim me titull përmbarimor +50%; paushalli 30%.",
    },
    {
        "code": "civil.enforcement.upto_10k",
        "tariff_no": "Nr. tarifor 6",
        "name": {
            "sq": "Propozim për përmbarim — vlera deri 10.000 €",
            "en": "Enforcement proposal — value up to €10,000",
            "zh": "执行申请 — 标的额一万欧元以下", "sr": "Predlog za izvršenje — vrednost do 10.000 €", "tr": "İcra talebi — 10.000 €'ya kadar değer", "bs": "Prijedlog za izvršenje — vrijednost do 10.000 €",
        },
        "practice_area": "civil",
        "amount": "80.00",
        "unit": "parashtresë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 6",
        "notes": "Klauzola për përmbarim me titull përmbarimor +50%; paushalli 30%.",
    },
    {
        "code": "civil.enforcement.over_10k",
        "tariff_no": "Nr. tarifor 6",
        "name": {
            "sq": "Propozim për përmbarim — vlera mbi 10.000 €",
            "en": "Enforcement proposal — value over €10,000",
            "zh": "执行申请 — 标的额一万欧元以上", "sr": "Predlog za izvršenje — vrednost preko 10.000 €", "tr": "İcra talebi — 10.000 € üzeri değer", "bs": "Prijedlog za izvršenje — vrijednost preko 10.000 €",
        },
        "practice_area": "civil",
        "amount": "160.00",
        "unit": "parashtresë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 6",
        "notes": "Klauzola për përmbarim me titull përmbarimor +50%; paushalli 30%.",
    },
    # Nr. tarifor 7: civil hearings by case value
    {
        "code": "civil.hearing.small",
        "tariff_no": "Nr. tarifor 7",
        "name": {
            "sq": "Përfaqësim në seancë — kontest i vlerës së vogël",
            "en": "Hearing representation — small-value dispute",
            "zh": "庭审代理 — 小额纠纷", "sr": "Zastupanje na ročištu — spor male vrednosti", "tr": "Duruşmada temsil — küçük değerli uyuşmazlık", "bs": "Zastupanje na ročištu — spor male vrijednosti",
        },
        "practice_area": "civil",
        "amount": "60.00",
        "unit": "seancë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 7",
        "notes": "Shtesë 30% për orë; paushalli 30%; seanca e shtyrë 50%.",
    },
    {
        "code": "civil.hearing.upto_10k",
        "tariff_no": "Nr. tarifor 7",
        "name": {
            "sq": "Përfaqësim në seancë — vlera deri 10.000 €",
            "en": "Hearing representation — value up to €10,000",
            "zh": "庭审代理 — 标的额一万欧元以下", "sr": "Zastupanje na ročištu — vrednost do 10.000 €", "tr": "Duruşmada temsil — 10.000 €'ya kadar değer", "bs": "Zastupanje na ročištu — vrijednost do 10.000 €",
        },
        "practice_area": "civil",
        "amount": "80.00",
        "unit": "seancë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 7",
        "notes": "Shtesë 30% për orë; paushalli 30%; seanca e shtyrë 50%.",
    },
    {
        "code": "civil.hearing.over_10k",
        "tariff_no": "Nr. tarifor 7",
        "name": {
            "sq": "Përfaqësim në seancë — vlera mbi 10.000 €",
            "en": "Hearing representation — value over €10,000",
            "zh": "庭审代理 — 标的额一万欧元以上", "sr": "Zastupanje na ročištu — vrednost preko 10.000 €", "tr": "Duruşmada temsil — 10.000 € üzeri değer", "bs": "Zastupanje na ročištu — vrijednost preko 10.000 €",
        },
        "practice_area": "civil",
        "amount": "160.00",
        "unit": "seancë",
        "legal_basis": "Tarifa e OAK, nr. tarifor 7",
        "notes": "Shtesë 30% për orë; paushalli 30%; seanca e shtyrë 50%.",
    },
    # Other rewards
    {
        "code": "other.misdemeanor",
        "tariff_no": "Shpërblimet tjera, pika 4",
        "name": {
            "sq": "Procedurë kundërvajtëse / disiplinore (për veprim)",
            "en": "Misdemeanor / disciplinary proceedings (per action)",
            "zh": "违章/纪律程序（每次行动）", "sr": "Prekršajni / disciplinski postupak (po radnji)", "tr": "Kabahat / disiplin işlemleri (işlem başına)", "bs": "Prekršajni / disciplinski postupak (po radnji)",
        },
        "practice_area": "other",
        "amount": "60.00",
        "unit": "veprim",
        "legal_basis": "Tarifa e OAK, shpërblimet tjera pika 4",
        "notes": "Llogaritet analogjikisht me bazën tarifore 60 €.",
    },
    {
        "code": "other.contract_drafting",
        "tariff_no": "Nr. tarifor 11",
        "name": {
            "sq": "Përpilim kontrate / ujdie / testamenti",
            "en": "Drafting a contract / settlement / will",
            "zh": "起草合同/和解协议/遗嘱", "sr": "Sastavljanje ugovora / poravnanja / testamenta", "tr": "Sözleşme / sulh / vasiyetname düzenleme", "bs": "Sastavljanje ugovora / poravnanja / testamenta",
        },
        "practice_area": "other",
        "amount": "80.00",
        "unit": "dokument",
        "legal_basis": "Tarifa e OAK, nr. tarifor 11",
        "notes": "Sipas nr. tarifor 6, ose deri në 1% të vlerës së tregut të pasurisë.",
    },
]
