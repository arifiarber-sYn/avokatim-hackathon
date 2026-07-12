"""Citizen self-service document templates (Phase 4) — data, not code.

Deterministic Jinja templates: the citizen fills plain-language fields and
downloads a formal letter as PDF. Bodies are in Albanian (the language of
official correspondence in Kosovo); labels are localized in the UI.
No LLM involved — output is predictable and reviewable.
"""

CITIZEN_DOC_TEMPLATES: list[dict] = [
    {
        "code": "kerkese",
        "name": {
            "sq": "Letër kërkese drejtuar një institucioni",
            "sr": "Pismo zahteva instituciji",
            "tr": "Bir kuruma talep mektubu",
            "bs": "Pismo zahtjeva instituciji",
            "en": "Request letter to an institution",
            "zh": "致机构的请求信",
        },
        "fields": [
            {"key": "sender_name", "type": "text", "label": {
                "sq": "Emri dhe mbiemri yt", "sr": "Vaše ime i prezime",
                "tr": "Adınız ve soyadınız", "bs": "Vaše ime i prezime",
                "en": "Your full name", "zh": "您的全名"}},
            {"key": "sender_address", "type": "text", "label": {
                "sq": "Adresa jote", "sr": "Vaša adresa", "tr": "Adresiniz",
                "bs": "Vaša adresa", "en": "Your address", "zh": "您的地址"}},
            {"key": "sender_phone", "type": "text", "label": {
                "sq": "Telefoni / email-i", "sr": "Telefon / imejl",
                "tr": "Telefon / e-posta", "bs": "Telefon / e-mail",
                "en": "Phone / email", "zh": "电话/电子邮件"}},
            {"key": "institution", "type": "text", "label": {
                "sq": "Institucioni (p.sh. Komuna e Prishtinës)",
                "sr": "Institucija (npr. Opština Priština)",
                "tr": "Kurum (örn. Priştine Belediyesi)",
                "bs": "Institucija (npr. Opština Priština)",
                "en": "Institution (e.g. Municipality of Prishtina)",
                "zh": "机构（例如普里什蒂纳市政府）"}},
            {"key": "subject", "type": "text", "label": {
                "sq": "Lënda e kërkesës", "sr": "Predmet zahteva",
                "tr": "Talebin konusu", "bs": "Predmet zahtjeva",
                "en": "Subject of the request", "zh": "请求主题"}},
            {"key": "body", "type": "textarea", "label": {
                "sq": "Çfarë kërkon dhe pse (me fjalë të thjeshta)",
                "sr": "Šta tražite i zašto (jednostavnim rečima)",
                "tr": "Ne talep ediyorsunuz ve neden (basit kelimelerle)",
                "bs": "Šta tražite i zašto (jednostavnim riječima)",
                "en": "What you request and why (in plain words)",
                "zh": "您请求什么以及原因（用简单的话）"}},
            {"key": "city", "type": "text", "label": {
                "sq": "Qyteti", "sr": "Grad", "tr": "Şehir", "bs": "Grad",
                "en": "City", "zh": "城市"}},
        ],
        "body_sq": (
            "{{ sender_name }}\n{{ sender_address }}\n{{ sender_phone }}\n\n"
            "PËR: {{ institution }}\n\n"
            "LËNDA: Kërkesë — {{ subject }}\n\n"
            "I/E nderuar,\n\n"
            "Me këtë shkresë, unë {{ sender_name }}, parashtroj kërkesën si më poshtë:\n\n"
            "{{ body }}\n\n"
            "Duke u bazuar në Ligjin nr. 05/L-031 për Procedurën e Përgjithshme "
            "Administrative, kërkoj që kjo kërkesë të shqyrtohet dhe të marr përgjigje "
            "brenda afatit ligjor.\n\n"
            "Ju faleminderit për mirëkuptimin.\n\n"
            "{{ city }}, më {{ date }}\n\n"
            "Me respekt,\n\n_____________________\n{{ sender_name }}"
        ),
    },
    {
        "code": "ankese",
        "name": {
            "sq": "Ankesë ndaj një vendimi administrativ",
            "sr": "Žalba na upravnu odluku",
            "tr": "İdari karara itiraz",
            "bs": "Žalba na upravnu odluku",
            "en": "Appeal against an administrative decision",
            "zh": "对行政决定的申诉",
        },
        "fields": [
            {"key": "sender_name", "type": "text", "label": {
                "sq": "Emri dhe mbiemri yt", "sr": "Vaše ime i prezime",
                "tr": "Adınız ve soyadınız", "bs": "Vaše ime i prezime",
                "en": "Your full name", "zh": "您的全名"}},
            {"key": "sender_address", "type": "text", "label": {
                "sq": "Adresa jote", "sr": "Vaša adresa", "tr": "Adresiniz",
                "bs": "Vaša adresa", "en": "Your address", "zh": "您的地址"}},
            {"key": "institution", "type": "text", "label": {
                "sq": "Institucioni që e mori vendimin",
                "sr": "Institucija koja je donela odluku",
                "tr": "Kararı veren kurum",
                "bs": "Institucija koja je donijela odluku",
                "en": "Institution that issued the decision", "zh": "作出决定的机构"}},
            {"key": "decision_no", "type": "text", "label": {
                "sq": "Numri i vendimit", "sr": "Broj odluke", "tr": "Karar numarası",
                "bs": "Broj odluke", "en": "Decision number", "zh": "决定编号"}},
            {"key": "decision_date", "type": "text", "label": {
                "sq": "Data e vendimit", "sr": "Datum odluke", "tr": "Karar tarihi",
                "bs": "Datum odluke", "en": "Decision date", "zh": "决定日期"}},
            {"key": "reason", "type": "textarea", "label": {
                "sq": "Pse mendon se vendimi është i gabuar (me fjalë të thjeshta)",
                "sr": "Zašto smatrate da je odluka pogrešna (jednostavnim rečima)",
                "tr": "Kararın neden yanlış olduğunu düşünüyorsunuz (basit kelimelerle)",
                "bs": "Zašto smatrate da je odluka pogrešna (jednostavnim riječima)",
                "en": "Why you believe the decision is wrong (in plain words)",
                "zh": "您认为决定错误的原因（用简单的话）"}},
            {"key": "city", "type": "text", "label": {
                "sq": "Qyteti", "sr": "Grad", "tr": "Şehir", "bs": "Grad",
                "en": "City", "zh": "城市"}},
        ],
        "body_sq": (
            "{{ sender_name }}\n{{ sender_address }}\n\n"
            "PËR: {{ institution }}\n\n"
            "LËNDA: Ankesë kundër vendimit nr. {{ decision_no }} të datës "
            "{{ decision_date }}\n\n"
            "I/E nderuar,\n\n"
            "Unë {{ sender_name }}, brenda afatit ligjor, paraqes ankesë kundër "
            "vendimit të lartcekur për arsyet si më poshtë:\n\n"
            "{{ reason }}\n\n"
            "Duke u bazuar në Ligjin nr. 05/L-031 për Procedurën e Përgjithshme "
            "Administrative, kërkoj që vendimi i ankimuar të anulohet ose të "
            "ndryshohet dhe çështja të rishqyrtohet.\n\n"
            "{{ city }}, më {{ date }}\n\n"
            "Me respekt,\n\n_____________________\n{{ sender_name }}"
        ),
    },
    {
        "code": "autorizim",
        "name": {
            "sq": "Autorizim i thjeshtë",
            "sr": "Jednostavno ovlašćenje",
            "tr": "Basit yetkilendirme",
            "bs": "Jednostavno ovlaštenje",
            "en": "Simple authorization",
            "zh": "简单授权书",
        },
        "fields": [
            {"key": "sender_name", "type": "text", "label": {
                "sq": "Emri yt (autorizuesi)", "sr": "Vaše ime (davalac ovlašćenja)",
                "tr": "Adınız (yetki veren)", "bs": "Vaše ime (davalac ovlaštenja)",
                "en": "Your name (authorizer)", "zh": "您的姓名（授权人）"}},
            {"key": "sender_id", "type": "text", "label": {
                "sq": "Numri personal yt", "sr": "Vaš lični broj",
                "tr": "Kişisel numaranız", "bs": "Vaš lični broj",
                "en": "Your personal ID number", "zh": "您的个人身份证号"}},
            {"key": "agent_name", "type": "text", "label": {
                "sq": "Emri i personit të autorizuar", "sr": "Ime ovlašćenog lica",
                "tr": "Yetkilendirilen kişinin adı", "bs": "Ime ovlaštene osobe",
                "en": "Name of the authorized person", "zh": "被授权人姓名"}},
            {"key": "agent_id", "type": "text", "label": {
                "sq": "Numri personal i të autorizuarit", "sr": "Lični broj ovlašćenog",
                "tr": "Yetkilendirilenin kişisel numarası", "bs": "Lični broj ovlaštenog",
                "en": "Authorized person's ID number", "zh": "被授权人身份证号"}},
            {"key": "purpose", "type": "textarea", "label": {
                "sq": "Për çfarë e autorizon (p.sh. të tërheqë dokumente në komunë)",
                "sr": "Za šta ga/je ovlašćujete (npr. preuzimanje dokumenata u opštini)",
                "tr": "Ne için yetkilendiriyorsunuz (örn. belediyeden belge almak)",
                "bs": "Za šta ga/je ovlašćujete (npr. preuzimanje dokumenata u opštini)",
                "en": "What you authorize them for (e.g. collecting documents)",
                "zh": "授权事项（例如在市政府领取文件）"}},
            {"key": "city", "type": "text", "label": {
                "sq": "Qyteti", "sr": "Grad", "tr": "Şehir", "bs": "Grad",
                "en": "City", "zh": "城市"}},
        ],
        "body_sq": (
            "AUTORIZIM\n\n"
            "Unë, {{ sender_name }}, me numër personal {{ sender_id }}, "
            "autorizoj {{ agent_name }}, me numër personal {{ agent_id }}, "
            "që në emrin tim dhe për llogarinë time të veprojë si më poshtë:\n\n"
            "{{ purpose }}\n\n"
            "Ky autorizim vlen deri në revokimin e tij me shkrim.\n\n"
            "{{ city }}, më {{ date }}\n\n"
            "Autorizuesi,\n\n_____________________\n{{ sender_name }}"
        ),
    },
]
