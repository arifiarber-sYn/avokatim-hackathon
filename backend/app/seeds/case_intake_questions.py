"""Structured intake questionnaires per practice area (D-059 F5) — data,
not code (hard rule §5.4).

A flat description forces the lawyer to ask the same 3 first questions in
every conversation. These category-specific questions are asked right after
the citizen picks a category (web) or after the LLM classifies the case
(WhatsApp / phone), and the answers land in
`CaseRequest.structured_answers` where the lawyer sees them labeled.

Question shape:
    key       stable identifier (snake_case)
    type      "text" | "date" | "choice"
    label     {sq, en, de, sr, tr, bs, zh}
    choices   for type=choice: [{value, label{...}}]
    countries optional list — omit for both XK and DE

Keep each category at 3–5 questions: this is triage, not an interrogation.
"""

_YES_NO = lambda: [  # noqa: E731 — tiny factory keeps the data readable
    {"value": "yes", "label": {
        "sq": "Po", "en": "Yes", "de": "Ja", "sr": "Da", "tr": "Evet",
        "bs": "Da", "zh": "是"}},
    {"value": "no", "label": {
        "sq": "Jo", "en": "No", "de": "Nein", "sr": "Ne", "tr": "Hayır",
        "bs": "Ne", "zh": "否"}},
]

CASE_INTAKE_QUESTIONS: dict[str, list[dict]] = {
    "family": [
        {
            "key": "marriage_date",
            "type": "date",
            "label": {
                "sq": "Kur është lidhur martesa (afërsisht)?",
                "en": "When was the marriage concluded (approximately)?",
                "de": "Wann wurde die Ehe geschlossen (ungefähr)?",
                "sr": "Kada je brak sklopljen (približno)?",
                "tr": "Evlilik ne zaman gerçekleşti (yaklaşık)?",
                "bs": "Kada je brak sklopljen (približno)?",
                "zh": "婚姻是何时缔结的（大约）？",
            },
        },
        {
            "key": "minor_children",
            "type": "text",
            "label": {
                "sq": "Sa fëmijë të mitur keni (mosha)?",
                "en": "How many minor children do you have (ages)?",
                "de": "Wie viele minderjährige Kinder haben Sie (Alter)?",
                "sr": "Koliko maloletne dece imate (uzrast)?",
                "tr": "Kaç reşit olmayan çocuğunuz var (yaşları)?",
                "bs": "Koliko maloljetne djece imate (uzrast)?",
                "zh": "您有几个未成年子女（年龄）？",
            },
        },
        {
            "key": "separated",
            "type": "choice",
            "choices": _YES_NO(),
            "label": {
                "sq": "A jetoni tashmë të ndarë?",
                "en": "Are you already living separately?",
                "de": "Leben Sie bereits getrennt?",
                "sr": "Da li već živite odvojeno?",
                "tr": "Zaten ayrı mı yaşıyorsunuz?",
                "bs": "Da li već živite odvojeno?",
                "zh": "你们是否已经分居？",
            },
        },
        {
            "key": "property_dispute",
            "type": "choice",
            "choices": _YES_NO(),
            "label": {
                "sq": "A ka kontest për pasuri të përbashkët?",
                "en": "Is there a dispute over joint property?",
                "de": "Gibt es Streit über gemeinsames Vermögen?",
                "sr": "Da li postoji spor oko zajedničke imovine?",
                "tr": "Ortak mal varlığı konusunda ihtilaf var mı?",
                "bs": "Da li postoji spor oko zajedničke imovine?",
                "zh": "是否存在共同财产纠纷？",
            },
        },
    ],
    "labor": [
        {
            "key": "termination_date",
            "type": "date",
            "label": {
                "sq": "Kur e keni marrë njoftimin e ndërprerjes / largimit?",
                "en": "When did you receive the termination notice?",
                "de": "Wann haben Sie die Kündigung erhalten?",
                "sr": "Kada ste primili obaveštenje o otkazu?",
                "tr": "Fesih bildirimini ne zaman aldınız?",
                "bs": "Kada ste primili obavještenje o otkazu?",
                "zh": "您何时收到解雇通知？",
            },
        },
        {
            "key": "employer_size",
            "type": "choice",
            "choices": [
                {"value": "lt10", "label": {
                    "sq": "Deri 10 punëtorë", "en": "Up to 10 employees",
                    "de": "Bis 10 Mitarbeiter", "sr": "Do 10 zaposlenih",
                    "tr": "10 çalışana kadar", "bs": "Do 10 zaposlenih",
                    "zh": "10名员工以内"}},
                {"value": "10to50", "label": {
                    "sq": "10–50 punëtorë", "en": "10–50 employees",
                    "de": "10–50 Mitarbeiter", "sr": "10–50 zaposlenih",
                    "tr": "10–50 çalışan", "bs": "10–50 zaposlenih",
                    "zh": "10–50名员工"}},
                {"value": "gt50", "label": {
                    "sq": "Mbi 50 punëtorë", "en": "Over 50 employees",
                    "de": "Über 50 Mitarbeiter", "sr": "Preko 50 zaposlenih",
                    "tr": "50'den fazla çalışan", "bs": "Preko 50 zaposlenih",
                    "zh": "50名员工以上"}},
            ],
            "label": {
                "sq": "Sa i madh është punëdhënësi?",
                "en": "How large is the employer?",
                "de": "Wie groß ist der Arbeitgeber?",
                "sr": "Koliko je veliki poslodavac?",
                "tr": "İşveren ne kadar büyük?",
                "bs": "Koliko je veliki poslodavac?",
                "zh": "雇主规模有多大？",
            },
        },
        {
            "key": "written_contract",
            "type": "choice",
            "choices": _YES_NO(),
            "label": {
                "sq": "A keni kontratë pune me shkrim?",
                "en": "Do you have a written employment contract?",
                "de": "Haben Sie einen schriftlichen Arbeitsvertrag?",
                "sr": "Da li imate pisani ugovor o radu?",
                "tr": "Yazılı iş sözleşmeniz var mı?",
                "bs": "Da li imate pisani ugovor o radu?",
                "zh": "您有书面劳动合同吗？",
            },
        },
        {
            "key": "unpaid_wages",
            "type": "choice",
            "choices": _YES_NO(),
            "label": {
                "sq": "A ju detyrohen paga të papaguara?",
                "en": "Are you owed unpaid wages?",
                "de": "Sind Ihnen Löhne/Gehälter ausstehend?",
                "sr": "Da li vam duguju neisplaćene zarade?",
                "tr": "Ödenmemiş ücret alacağınız var mı?",
                "bs": "Da li vam duguju neisplaćene plate?",
                "zh": "是否拖欠您工资？",
            },
        },
    ],
    "civil": [
        {
            "key": "dispute_type",
            "type": "choice",
            "choices": [
                {"value": "rent", "label": {
                    "sq": "Qira / banesë", "en": "Rent / housing",
                    "de": "Miete / Wohnung", "sr": "Zakup / stan",
                    "tr": "Kira / konut", "bs": "Zakup / stan", "zh": "租赁/住房"}},
                {"value": "traffic", "label": {
                    "sq": "Trafik / dëm aksidenti", "en": "Traffic / accident damage",
                    "de": "Verkehr / Unfallschaden", "sr": "Saobraćaj / šteta iz nezgode",
                    "tr": "Trafik / kaza hasarı", "bs": "Saobraćaj / šteta iz nezgode",
                    "zh": "交通/事故损害"}},
                {"value": "contract", "label": {
                    "sq": "Kontratë / borxh", "en": "Contract / debt",
                    "de": "Vertrag / Forderung", "sr": "Ugovor / dug",
                    "tr": "Sözleşme / alacak", "bs": "Ugovor / dug", "zh": "合同/债务"}},
                {"value": "property", "label": {
                    "sq": "Pronësi / paluajtshmëri", "en": "Property / real estate",
                    "de": "Eigentum / Immobilie", "sr": "Svojina / nekretnina",
                    "tr": "Mülkiyet / gayrimenkul", "bs": "Vlasništvo / nekretnina",
                    "zh": "产权/不动产"}},
                {"value": "other", "label": {
                    "sq": "Tjetër", "en": "Other", "de": "Sonstiges", "sr": "Drugo",
                    "tr": "Diğer", "bs": "Drugo", "zh": "其他"}},
            ],
            "label": {
                "sq": "Për çfarë lloji kontesti bëhet fjalë?",
                "en": "What kind of dispute is it?",
                "de": "Um welche Art von Streit handelt es sich?",
                "sr": "O kakvoj vrsti spora se radi?",
                "tr": "Ne tür bir ihtilaf söz konusu?",
                "bs": "O kakvoj vrsti spora se radi?",
                "zh": "属于哪一类纠纷？",
            },
        },
        {
            "key": "amount",
            "type": "text",
            "label": {
                "sq": "Vlera e përafërt e kontestit (€)?",
                "en": "Approximate value in dispute (€)?",
                "de": "Ungefährer Streitwert (€)?",
                "sr": "Približna vrednost spora (€)?",
                "tr": "Yaklaşık ihtilaf değeri (€)?",
                "bs": "Približna vrijednost spora (€)?",
                "zh": "争议金额大约是多少（欧元）？",
            },
        },
        {
            "key": "incident_date",
            "type": "date",
            "label": {
                "sq": "Kur ka ndodhur ngjarja / është lidhur kontrata?",
                "en": "When did the event happen / contract get signed?",
                "de": "Wann ist das Ereignis passiert / wurde der Vertrag geschlossen?",
                "sr": "Kada se događaj desio / ugovor zaključen?",
                "tr": "Olay ne zaman gerçekleşti / sözleşme ne zaman imzalandı?",
                "bs": "Kada se događaj desio / ugovor zaključen?",
                "zh": "事件何时发生/合同何时签订？",
            },
        },
        {
            "key": "has_documents",
            "type": "choice",
            "choices": _YES_NO(),
            "label": {
                "sq": "A keni kontratë ose dokumente/prova me shkrim?",
                "en": "Do you have a contract or written documents/evidence?",
                "de": "Haben Sie einen Vertrag oder schriftliche Unterlagen/Beweise?",
                "sr": "Da li imate ugovor ili pisane dokumente/dokaze?",
                "tr": "Sözleşme veya yazılı belge/kanıtınız var mı?",
                "bs": "Da li imate ugovor ili pisane dokumente/dokaze?",
                "zh": "您是否有合同或书面文件/证据？",
            },
        },
    ],
    "criminal": [
        {
            "key": "role",
            "type": "choice",
            "choices": [
                {"value": "suspect", "label": {
                    "sq": "I dyshuar / i akuzuar", "en": "Suspect / accused",
                    "de": "Beschuldigt / angeklagt", "sr": "Osumnjičeni / optuženi",
                    "tr": "Şüpheli / sanık", "bs": "Osumnjičeni / optuženi",
                    "zh": "嫌疑人/被告"}},
                {"value": "victim", "label": {
                    "sq": "I dëmtuar / viktimë", "en": "Victim / injured party",
                    "de": "Geschädigt / Opfer", "sr": "Oštećeni / žrtva",
                    "tr": "Mağdur", "bs": "Oštećeni / žrtva", "zh": "受害人"}},
                {"value": "witness", "label": {
                    "sq": "Dëshmitar", "en": "Witness", "de": "Zeuge", "sr": "Svedok",
                    "tr": "Tanık", "bs": "Svjedok", "zh": "证人"}},
            ],
            "label": {
                "sq": "Cili është roli juaj në procedurë?",
                "en": "What is your role in the proceedings?",
                "de": "Welche Rolle haben Sie im Verfahren?",
                "sr": "Koja je vaša uloga u postupku?",
                "tr": "Süreçteki rolünüz nedir?",
                "bs": "Koja je vaša uloga u postupku?",
                "zh": "您在程序中的角色是什么？",
            },
        },
        {
            "key": "detention",
            "type": "choice",
            "choices": _YES_NO(),
            "label": {
                "sq": "A ka ndalim, arrest apo paraburgim?",
                "en": "Is anyone detained or in custody?",
                "de": "Gibt es eine Festnahme oder Untersuchungshaft?",
                "sr": "Da li postoji zadržavanje ili pritvor?",
                "tr": "Gözaltı veya tutukluluk var mı?",
                "bs": "Da li postoji zadržavanje ili pritvor?",
                "zh": "是否有人被拘留或羁押？",
            },
        },
        {
            "key": "incident_date",
            "type": "date",
            "label": {
                "sq": "Kur ka ndodhur ngjarja (afërsisht)?",
                "en": "When did the incident happen (approximately)?",
                "de": "Wann ist der Vorfall passiert (ungefähr)?",
                "sr": "Kada se incident desio (približno)?",
                "tr": "Olay ne zaman gerçekleşti (yaklaşık)?",
                "bs": "Kada se incident desio (približno)?",
                "zh": "事件何时发生（大约）？",
            },
        },
    ],
}

# WhatsApp / phone flows keep the conversation short: at most this many of
# the category's questions are asked, in seed order.
CONVERSATIONAL_MAX_QUESTIONS = 3


def questions_for(category: str, country: str = "XK") -> list[dict]:
    """The questionnaire for a category, filtered by country when a question
    declares one. Empty list for categories without a questionnaire."""
    return [
        q for q in CASE_INTAKE_QUESTIONS.get(category, [])
        if country in q.get("countries", (country,))
    ]


def question_label(category: str, key: str, locale: str) -> str:
    """Localized label of one question (for lawyer views and notifications);
    falls back to sq, then the raw key."""
    for q in CASE_INTAKE_QUESTIONS.get(category, []):
        if q["key"] == key:
            return q["label"].get(locale) or q["label"].get("sq") or key
    return key


def choice_label(category: str, key: str, value: str, locale: str) -> str:
    """Localized label of a choice value; free-text answers pass through."""
    for q in CASE_INTAKE_QUESTIONS.get(category, []):
        if q["key"] == key:
            for c in q.get("choices", []):
                if c["value"] == value:
                    return c["label"].get(locale) or c["label"].get("sq") or value
    return value
