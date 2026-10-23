"""Citizen self-service document templates (Phase 4) — data, not code.

Deterministic Jinja templates: the citizen fills plain-language fields and
downloads a formal letter as PDF. Bodies are in Albanian (the language of
official correspondence in Kosovo); labels are localized in the UI.
No LLM involved — output is predictable and reviewable.
"""

# Categories group templates in the UI: institucionet / puna / konsumatori /
# te_pergjithshme / noteria. Category labels are localized on the frontend.
# Templates with "requires_notary" gain full legal force only after
# certification/solemnization before a notary; "notary_act" links them to the
# matching act in seeds/notary.py (checklist + fee on /noteret).
CITIZEN_DOC_TEMPLATES: list[dict] = [
    {
        "code": "kerkese",
        "category": "institucionet",
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
        "category": "institucionet",
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
        "category": "te_pergjithshme",
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
    {
        "code": "qasje_dokumente",
        "category": "institucionet",
        "name": {
            "sq": "Kërkesë për qasje në dokumente publike",
            "sr": "Zahtev za pristup javnim dokumentima",
            "tr": "Kamu belgelerine erişim talebi",
            "bs": "Zahtjev za pristup javnim dokumentima",
            "en": "Request for access to public documents",
            "zh": "查阅公共文件申请",
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
                "sq": "Institucioni publik (p.sh. Ministria, Komuna)",
                "sr": "Javna institucija (npr. ministarstvo, opština)",
                "tr": "Kamu kurumu (örn. bakanlık, belediye)",
                "bs": "Javna institucija (npr. ministarstvo, opština)",
                "en": "Public institution (e.g. ministry, municipality)",
                "zh": "公共机构（例如部委、市政府）"}},
            {"key": "documents", "type": "textarea", "label": {
                "sq": "Cilat dokumente ose informacione kërkon (sa më saktë)",
                "sr": "Koja dokumenta ili informacije tražite (što preciznije)",
                "tr": "Hangi belge veya bilgileri talep ediyorsunuz (mümkün olduğunca kesin)",
                "bs": "Koja dokumenta ili informacije tražite (što preciznije)",
                "en": "Which documents or information you request (as precisely as possible)",
                "zh": "您申请查阅哪些文件或信息（尽量具体）"}},
            {"key": "city", "type": "text", "label": {
                "sq": "Qyteti", "sr": "Grad", "tr": "Şehir", "bs": "Grad",
                "en": "City", "zh": "城市"}},
        ],
        "body_sq": (
            "{{ sender_name }}\n{{ sender_address }}\n{{ sender_phone }}\n\n"
            "PËR: {{ institution }}\nZyrtarit përgjegjës për qasje në dokumente publike\n\n"
            "LËNDA: Kërkesë për qasje në dokumente publike\n\n"
            "I/E nderuar,\n\n"
            "Në bazë të Ligjit Nr. 06/L-081 për Qasje në Dokumente Publike, unë "
            "{{ sender_name }} kërkoj qasje në dokumentet/informacionet si më poshtë:\n\n"
            "{{ documents }}\n\n"
            "Kërkoj që dokumentet të më ofrohen në formë elektronike ose kopje fizike. "
            "Ju kujtoj se sipas nenit 12 të ligjit të lartcekur, institucioni publik "
            "është i detyruar të vendosë për kërkesën brenda 7 (shtatë) ditëve nga "
            "pranimi i saj.\n\n"
            "Ju faleminderit për bashkëpunimin.\n\n"
            "{{ city }}, më {{ date }}\n\n"
            "Me respekt,\n\n_____________________\n{{ sender_name }}"
        ),
    },
    {
        "code": "ankese_konsumatori",
        "category": "konsumatori",
        "name": {
            "sq": "Ankesë konsumatori ndaj një biznesi",
            "sr": "Potrošačka žalba protiv preduzeća",
            "tr": "Bir işletmeye karşı tüketici şikayeti",
            "bs": "Potrošačka žalba protiv preduzeća",
            "en": "Consumer complaint against a business",
            "zh": "针对商家的消费者投诉",
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
            {"key": "business", "type": "text", "label": {
                "sq": "Emri i biznesit dhe adresa e tij",
                "sr": "Naziv i adresa preduzeća",
                "tr": "İşletmenin adı ve adresi",
                "bs": "Naziv i adresa preduzeća",
                "en": "Business name and address", "zh": "商家名称和地址"}},
            {"key": "purchase", "type": "text", "label": {
                "sq": "Produkti/shërbimi dhe data e blerjes",
                "sr": "Proizvod/usluga i datum kupovine",
                "tr": "Ürün/hizmet ve satın alma tarihi",
                "bs": "Proizvod/usluga i datum kupovine",
                "en": "Product/service and purchase date", "zh": "产品/服务及购买日期"}},
            {"key": "complaint", "type": "textarea", "label": {
                "sq": "Çfarë ndodhi — problemi me produktin/shërbimin",
                "sr": "Šta se desilo — problem sa proizvodom/uslugom",
                "tr": "Ne oldu — ürün/hizmetle ilgili sorun",
                "bs": "Šta se desilo — problem s proizvodom/uslugom",
                "en": "What happened — the problem with the product/service",
                "zh": "发生了什么——产品/服务的问题"}},
            {"key": "demand", "type": "textarea", "label": {
                "sq": "Çfarë kërkon (kthim parash, riparim, ndërrim…)",
                "sr": "Šta tražite (povraćaj novca, popravka, zamena…)",
                "tr": "Ne talep ediyorsunuz (para iadesi, onarım, değişim…)",
                "bs": "Šta tražite (povrat novca, popravka, zamjena…)",
                "en": "What you demand (refund, repair, replacement…)",
                "zh": "您的诉求（退款、维修、更换等）"}},
            {"key": "city", "type": "text", "label": {
                "sq": "Qyteti", "sr": "Grad", "tr": "Şehir", "bs": "Grad",
                "en": "City", "zh": "城市"}},
        ],
        "body_sq": (
            "{{ sender_name }}\n{{ sender_address }}\n{{ sender_phone }}\n\n"
            "PËR: {{ business }}\n\n"
            "LËNDA: Ankesë konsumatori — {{ purchase }}\n\n"
            "I/E nderuar,\n\n"
            "Si konsumator, në bazë të Ligjit Nr. 06/L-034 për Mbrojtjen e "
            "Konsumatorit, paraqes këtë ankesë lidhur me produktin/shërbimin e "
            "lartcekur:\n\n"
            "{{ complaint }}\n\n"
            "Për zgjidhjen e këtij problemi, kërkoj:\n\n"
            "{{ demand }}\n\n"
            "Kërkoj përgjigje me shkrim brenda afatit ligjor. Në rast se ankesa nuk "
            "trajtohet, do të detyrohem t'i drejtohem Inspektoratit të Tregut dhe "
            "organeve tjera kompetente.\n\n"
            "{{ city }}, më {{ date }}\n\n"
            "Me respekt,\n\n_____________________\n{{ sender_name }}"
        ),
    },
    {
        "code": "verejtje_pune",
        "category": "puna",
        "name": {
            "sq": "Kërkesë/vërejtje ndaj punëdhënësit",
            "sr": "Zahtev/prigovor poslodavcu",
            "tr": "İşverene talep/ihtar",
            "bs": "Zahtjev/prigovor poslodavcu",
            "en": "Request/notice to your employer",
            "zh": "致雇主的请求/申告",
        },
        "fields": [
            {"key": "sender_name", "type": "text", "label": {
                "sq": "Emri dhe mbiemri yt", "sr": "Vaše ime i prezime",
                "tr": "Adınız ve soyadınız", "bs": "Vaše ime i prezime",
                "en": "Your full name", "zh": "您的全名"}},
            {"key": "position", "type": "text", "label": {
                "sq": "Pozita jote e punës", "sr": "Vaše radno mesto",
                "tr": "İş pozisyonunuz", "bs": "Vaše radno mjesto",
                "en": "Your job position", "zh": "您的工作岗位"}},
            {"key": "employer", "type": "text", "label": {
                "sq": "Punëdhënësi (emri i kompanisë/institucionit)",
                "sr": "Poslodavac (naziv firme/institucije)",
                "tr": "İşveren (şirket/kurum adı)",
                "bs": "Poslodavac (naziv firme/institucije)",
                "en": "Employer (company/institution name)", "zh": "雇主（公司/机构名称）"}},
            {"key": "issue", "type": "textarea", "label": {
                "sq": "Problemi (p.sh. paga e papaguar, pushimi i pamundësuar, orët shtesë)",
                "sr": "Problem (npr. neisplaćena plata, uskraćen odmor, prekovremeni rad)",
                "tr": "Sorun (örn. ödenmemiş maaş, kullandırılmayan izin, fazla mesai)",
                "bs": "Problem (npr. neisplaćena plata, uskraćen odmor, prekovremeni rad)",
                "en": "The issue (e.g. unpaid salary, denied leave, overtime)",
                "zh": "问题（例如未付工资、被拒的休假、加班）"}},
            {"key": "demand", "type": "textarea", "label": {
                "sq": "Çfarë kërkon nga punëdhënësi dhe deri kur",
                "sr": "Šta tražite od poslodavca i do kada",
                "tr": "İşverenden ne talep ediyorsunuz ve ne zamana kadar",
                "bs": "Šta tražite od poslodavca i do kada",
                "en": "What you demand from the employer and by when",
                "zh": "您向雇主提出的要求及期限"}},
            {"key": "city", "type": "text", "label": {
                "sq": "Qyteti", "sr": "Grad", "tr": "Şehir", "bs": "Grad",
                "en": "City", "zh": "城市"}},
        ],
        "body_sq": (
            "{{ sender_name }}\n{{ position }}\n\n"
            "PËR: {{ employer }}\n\n"
            "LËNDA: Kërkesë për respektimin e të drejtave nga marrëdhënia e punës\n\n"
            "I/E nderuar,\n\n"
            "Si i/e punësuar në pozitën e lartcekur, ju drejtohem me këtë shkresë "
            "lidhur me problemin si më poshtë:\n\n"
            "{{ issue }}\n\n"
            "Në bazë të Ligjit Nr. 03/L-212 të Punës dhe kontratës sime të punës, "
            "kërkoj:\n\n"
            "{{ demand }}\n\n"
            "Në rast se kjo kërkesë nuk trajtohet, do të detyrohem t'i drejtohem "
            "Inspektoratit të Punës dhe organeve tjera kompetente për mbrojtjen e "
            "të drejtave të mia.\n\n"
            "{{ city }}, më {{ date }}\n\n"
            "Me respekt,\n\n_____________________\n{{ sender_name }}"
        ),
    },
    {
        "code": "kundershtim_urdherpagese",
        "category": "te_pergjithshme",
        "name": {
            "sq": "Kundërshtim ndaj urdhërpagese",
            "sr": "Prigovor na platni nalog",
            "tr": "Ödeme emrine itiraz",
            "bs": "Prigovor na platni nalog",
            "en": "Objection to a payment order",
            "zh": "对支付令的异议",
        },
        "fields": [
            {"key": "sender_name", "type": "text", "label": {
                "sq": "Emri dhe mbiemri yt", "sr": "Vaše ime i prezime",
                "tr": "Adınız ve soyadınız", "bs": "Vaše ime i prezime",
                "en": "Your full name", "zh": "您的全名"}},
            {"key": "sender_address", "type": "text", "label": {
                "sq": "Adresa jote", "sr": "Vaša adresa", "tr": "Adresiniz",
                "bs": "Vaša adresa", "en": "Your address", "zh": "您的地址"}},
            {"key": "court", "type": "text", "label": {
                "sq": "Gjykata/organi që e lëshoi urdhërpagesën",
                "sr": "Sud/organ koji je izdao platni nalog",
                "tr": "Ödeme emrini veren mahkeme/makam",
                "bs": "Sud/organ koji je izdao platni nalog",
                "en": "Court/authority that issued the payment order",
                "zh": "签发支付令的法院/机关"}},
            {"key": "case_no", "type": "text", "label": {
                "sq": "Numri i lëndës / urdhërpagesës",
                "sr": "Broj predmeta / platnog naloga",
                "tr": "Dosya / ödeme emri numarası",
                "bs": "Broj predmeta / platnog naloga",
                "en": "Case / payment order number", "zh": "案件/支付令编号"}},
            {"key": "order_date", "type": "text", "label": {
                "sq": "Data e urdhërpagesës", "sr": "Datum platnog naloga",
                "tr": "Ödeme emrinin tarihi", "bs": "Datum platnog naloga",
                "en": "Date of the payment order", "zh": "支付令日期"}},
            {"key": "reason", "type": "textarea", "label": {
                "sq": "Pse e kundërshton (borxhi nuk ekziston, është paguar, shuma e gabuar…)",
                "sr": "Zašto ga osporavate (dug ne postoji, plaćen je, pogrešan iznos…)",
                "tr": "Neden itiraz ediyorsunuz (borç yok, ödendi, tutar yanlış…)",
                "bs": "Zašto ga osporavate (dug ne postoji, plaćen je, pogrešan iznos…)",
                "en": "Why you object (debt does not exist, already paid, wrong amount…)",
                "zh": "异议理由（债务不存在、已支付、金额错误等）"}},
            {"key": "city", "type": "text", "label": {
                "sq": "Qyteti", "sr": "Grad", "tr": "Şehir", "bs": "Grad",
                "en": "City", "zh": "城市"}},
        ],
        "body_sq": (
            "{{ sender_name }}\n{{ sender_address }}\n\n"
            "PËR: {{ court }}\n\n"
            "LËNDA: Kundërshtim ndaj urdhërpagesës nr. {{ case_no }} të datës "
            "{{ order_date }}\n\n"
            "I/E nderuar,\n\n"
            "Unë {{ sender_name }}, në cilësinë e debitorit të pretenduar, brenda "
            "afatit ligjor paraqes kundërshtim ndaj urdhërpagesës së lartcekur, për "
            "arsyet si më poshtë:\n\n"
            "{{ reason }}\n\n"
            "Në bazë të dispozitave të Ligjit Nr. 03/L-006 për Procedurën "
            "Kontestimore që rregullojnë procedurën e urdhërpagesës, kërkoj që "
            "urdhërpagesa të shfuqizohet dhe procedura të vazhdojë sipas rregullave "
            "të procedurës kontestimore, ku do të paraqes provat e mia.\n\n"
            "{{ city }}, më {{ date }}\n\n"
            "Me respekt,\n\n_____________________\n{{ sender_name }}"
        ),
    },
    # ---------- notary pack: drafts the citizen takes to the notary ----------
    {
        "code": "kontrate_veture",
        "category": "noteria",
        "requires_notary": True,
        "notary_act": "kontrate_veture",
        "name": {
            "sq": "Kontratë për shitblerje të veturës",
            "sr": "Ugovor o kupoprodaji vozila",
            "tr": "Araç satış sözleşmesi",
            "bs": "Ugovor o kupoprodaji vozila",
            "en": "Vehicle sale contract",
            "zh": "车辆买卖合同",
        },
        "fields": [
            {"key": "seller_name", "type": "text", "label": {
                "sq": "Shitësi — emri dhe mbiemri", "sr": "Prodavac — ime i prezime",
                "tr": "Satıcı — ad ve soyad", "bs": "Prodavac — ime i prezime",
                "en": "Seller — full name", "zh": "卖方——全名"}},
            {"key": "seller_id", "type": "text", "label": {
                "sq": "Numri personal i shitësit", "sr": "Lični broj prodavca",
                "tr": "Satıcının kişisel numarası", "bs": "Lični broj prodavca",
                "en": "Seller's personal ID number", "zh": "卖方身份证号"}},
            {"key": "buyer_name", "type": "text", "label": {
                "sq": "Blerësi — emri dhe mbiemri", "sr": "Kupac — ime i prezime",
                "tr": "Alıcı — ad ve soyad", "bs": "Kupac — ime i prezime",
                "en": "Buyer — full name", "zh": "买方——全名"}},
            {"key": "buyer_id", "type": "text", "label": {
                "sq": "Numri personal i blerësit", "sr": "Lični broj kupca",
                "tr": "Alıcının kişisel numarası", "bs": "Lični broj kupca",
                "en": "Buyer's personal ID number", "zh": "买方身份证号"}},
            {"key": "vehicle", "type": "text", "label": {
                "sq": "Vetura (marka, modeli, viti, ngjyra)",
                "sr": "Vozilo (marka, model, godina, boja)",
                "tr": "Araç (marka, model, yıl, renk)",
                "bs": "Vozilo (marka, model, godina, boja)",
                "en": "Vehicle (make, model, year, color)",
                "zh": "车辆（品牌、型号、年份、颜色）"}},
            {"key": "chassis_no", "type": "text", "label": {
                "sq": "Numri i shasisë (VIN) dhe i targave",
                "sr": "Broj šasije (VIN) i registarske tablice",
                "tr": "Şasi numarası (VIN) ve plaka",
                "bs": "Broj šasije (VIN) i registarske tablice",
                "en": "Chassis number (VIN) and plates", "zh": "车架号（VIN）和车牌"}},
            {"key": "price", "type": "text", "label": {
                "sq": "Çmimi i dakorduar në euro",
                "sr": "Ugovorena cena u evrima", "tr": "Anlaşılan fiyat (euro)",
                "bs": "Ugovorena cijena u evrima", "en": "Agreed price in euros",
                "zh": "约定价格（欧元）"}},
            {"key": "city", "type": "text", "label": {
                "sq": "Qyteti", "sr": "Grad", "tr": "Şehir", "bs": "Grad",
                "en": "City", "zh": "城市"}},
        ],
        "body_sq": (
            "KONTRATË PËR SHITBLERJEN E VETURËS\n\n"
            "E lidhur më {{ date }} në {{ city }}, ndërmjet:\n\n"
            "SHITËSI: {{ seller_name }}, numër personal {{ seller_id }}\n"
            "BLERËSI: {{ buyer_name }}, numër personal {{ buyer_id }}\n\n"
            "Neni 1 — Objekti\n"
            "Shitësi ia shet blerësit veturën: {{ vehicle }}, me numër shasie "
            "dhe targa: {{ chassis_no }}.\n\n"
            "Neni 2 — Çmimi\n"
            "Çmimi i dakorduar është {{ price }} euro, të cilin blerësi ia "
            "paguan shitësit me rastin e nënshkrimit të kësaj kontrate.\n\n"
            "Neni 3 — Deklarimet e shitësit\n"
            "Shitësi deklaron se vetura është pronë e tij, e lirë nga barrët, "
            "pengjet dhe të drejtat e personave të tretë.\n\n"
            "Neni 4 — Dorëzimi dhe rreziku\n"
            "Vetura, çelësat dhe dokumentacioni i dorëzohen blerësit me "
            "nënshkrimin e kontratës; nga ai moment rreziku dhe shpenzimet "
            "kalojnë te blerësi, i cili detyrohet ta regjistrojë veturën në "
            "emrin e tij brenda afatit ligjor.\n\n"
            "Neni 5 — E drejta e zbatueshme\n"
            "Për çka nuk është paraparë me këtë kontratë zbatohet Ligji "
            "Nr. 04/L-077 për Marrëdhëniet e Detyrimeve.\n\n"
            "{{ city }}, më {{ date }}\n\n"
            "SHITËSI                                    BLERËSI\n\n"
            "_____________________          _____________________\n"
            "{{ seller_name }}                  {{ buyer_name }}\n\n"
            "VËREJTJE: Nënshkrimet vërtetohen te noteri — kontrata pa "
            "vërtetim noterial nuk mund të përdoret për regjistrimin e "
            "veturës."
        ),
    },
    {
        "code": "prokure",
        "category": "noteria",
        "requires_notary": True,
        "notary_act": "autorizim_noterial",
        "name": {
            "sq": "Prokurë / autorizim për te noteri",
            "sr": "Punomoćje za notara",
            "tr": "Noter için vekaletname",
            "bs": "Punomoć za notara",
            "en": "Power of attorney (for the notary)",
            "zh": "授权书（公证用）",
        },
        "fields": [
            {"key": "sender_name", "type": "text", "label": {
                "sq": "Autorizuesi — emri dhe mbiemri", "sr": "Davalac punomoćja — ime i prezime",
                "tr": "Vekalet veren — ad ve soyad", "bs": "Davalac punomoći — ime i prezime",
                "en": "Principal — full name", "zh": "委托人——全名"}},
            {"key": "sender_id", "type": "text", "label": {
                "sq": "Numri personal dhe adresa e autorizuesit",
                "sr": "Lični broj i adresa davaoca",
                "tr": "Vekalet verenin kişisel numarası ve adresi",
                "bs": "Lični broj i adresa davaoca",
                "en": "Principal's ID number and address", "zh": "委托人身份证号和地址"}},
            {"key": "agent_name", "type": "text", "label": {
                "sq": "I autorizuari — emri dhe mbiemri", "sr": "Punomoćnik — ime i prezime",
                "tr": "Vekil — ad ve soyad", "bs": "Punomoćnik — ime i prezime",
                "en": "Agent — full name", "zh": "受托人——全名"}},
            {"key": "agent_id", "type": "text", "label": {
                "sq": "Numri personal dhe adresa e të autorizuarit",
                "sr": "Lični broj i adresa punomoćnika",
                "tr": "Vekilin kişisel numarası ve adresi",
                "bs": "Lični broj i adresa punomoćnika",
                "en": "Agent's ID number and address", "zh": "受托人身份证号和地址"}},
            {"key": "powers", "type": "textarea", "label": {
                "sq": "Veprimet për të cilat e autorizon (sa më saktë: p.sh. "
                      "të nënshkruajë kontratën e shitjes së banesës në adresën X)",
                "sr": "Radnje za koje ga/je ovlašćujete (što preciznije)",
                "tr": "Yetki verilen işlemler (mümkün olduğunca kesin)",
                "bs": "Radnje za koje ga/je ovlašćujete (što preciznije)",
                "en": "The powers granted (as precisely as possible)",
                "zh": "授权事项（尽量具体）"}},
            {"key": "duration", "type": "text", "label": {
                "sq": "Afati i vlefshmërisë (p.sh. 6 muaj, deri më 31.12.2026)",
                "sr": "Rok važenja (npr. 6 meseci)", "tr": "Geçerlilik süresi (örn. 6 ay)",
                "bs": "Rok važenja (npr. 6 mjeseci)", "en": "Validity period (e.g. 6 months)",
                "zh": "有效期（例如6个月）"}},
            {"key": "city", "type": "text", "label": {
                "sq": "Qyteti", "sr": "Grad", "tr": "Şehir", "bs": "Grad",
                "en": "City", "zh": "城市"}},
        ],
        "body_sq": (
            "PROKURË (AUTORIZIM)\n\n"
            "Unë, {{ sender_name }}, {{ sender_id }} (në vijim: Autorizuesi), "
            "me vullnetin tim të lirë autorizoj\n\n"
            "{{ agent_name }}, {{ agent_id }} (në vijim: I Autorizuari),\n\n"
            "që në emrin tim dhe për llogarinë time të ndërmarrë veprimet "
            "si në vijim:\n\n"
            "{{ powers }}\n\n"
            "I Autorizuari ka të drejtë të nënshkruajë dokumentet dhe të "
            "ndërmarrë veprimet e nevojshme brenda kufijve të këtij "
            "autorizimi. Kjo prokurë vlen: {{ duration }}, dhe mund të "
            "revokohet në çdo kohë me deklaratë me shkrim.\n\n"
            "{{ city }}, më {{ date }}\n\n"
            "Autorizuesi,\n\n_____________________\n{{ sender_name }}\n\n"
            "VËREJTJE: Për punët për të cilat ligji kërkon formën e aktit "
            "noterial (p.sh. shitja e paluajtshmërisë), kjo prokurë duhet "
            "të përpilohet ose vërtetohet te noteri."
        ),
    },
    {
        "code": "marreveshje_bashkeshortore",
        "category": "noteria",
        "requires_notary": True,
        "notary_act": "marreveshje_bashkeshortore",
        "name": {
            "sq": "Marrëveshje pasurore mes bashkëshortëve (draft)",
            "sr": "Imovinski sporazum između supružnika (nacrt)",
            "tr": "Eşler arası mal rejimi sözleşmesi (taslak)",
            "bs": "Imovinski sporazum između supružnika (nacrt)",
            "en": "Spousal property agreement (draft)",
            "zh": "夫妻财产协议（草案）",
        },
        "fields": [
            {"key": "spouse1", "type": "text", "label": {
                "sq": "Bashkëshorti/ja I — emri dhe numri personal",
                "sr": "Supružnik I — ime i lični broj",
                "tr": "Eş I — ad ve kimlik numarası",
                "bs": "Supružnik I — ime i lični broj",
                "en": "Spouse I — name and ID number", "zh": "配偶一——姓名及身份证号"}},
            {"key": "spouse2", "type": "text", "label": {
                "sq": "Bashkëshorti/ja II — emri dhe numri personal",
                "sr": "Supružnik II — ime i lični broj",
                "tr": "Eş II — ad ve kimlik numarası",
                "bs": "Supružnik II — ime i lični broj",
                "en": "Spouse II — name and ID number", "zh": "配偶二——姓名及身份证号"}},
            {"key": "marriage", "type": "text", "label": {
                "sq": "Data dhe vendi i lidhjes së martesës",
                "sr": "Datum i mesto zaključenja braka",
                "tr": "Evliliğin tarihi ve yeri",
                "bs": "Datum i mjesto zaključenja braka",
                "en": "Date and place of marriage", "zh": "结婚日期和地点"}},
            {"key": "arrangement", "type": "textarea", "label": {
                "sq": "Si dëshironi ta rregulloni pasurinë (p.sh. banesa në "
                      "adresën X mbetet pronë e veçantë e..., të ardhurat...)",
                "sr": "Kako želite urediti imovinu (jednostavnim rečima)",
                "tr": "Mal varlığını nasıl düzenlemek istiyorsunuz",
                "bs": "Kako želite urediti imovinu (jednostavnim riječima)",
                "en": "How you want to arrange the property (in plain words)",
                "zh": "您希望如何安排财产（用简单的话）"}},
            {"key": "city", "type": "text", "label": {
                "sq": "Qyteti", "sr": "Grad", "tr": "Şehir", "bs": "Grad",
                "en": "City", "zh": "城市"}},
        ],
        "body_sq": (
            "MARRËVESHJE PËR RREGULLIMIN E MARRËDHËNIEVE PASURORE\n"
            "NDËRMJET BASHKËSHORTËVE (DRAFT PËR SOLEMNIZIM TE NOTERI)\n\n"
            "E lidhur më {{ date }} në {{ city }}, ndërmjet:\n\n"
            "1. {{ spouse1 }}\n2. {{ spouse2 }}\n\n"
            "të cilët kanë lidhur martesë më: {{ marriage }}.\n\n"
            "Neni 1 — Qëllimi\n"
            "Me këtë marrëveshje palët i rregullojnë me vullnet të lirë "
            "marrëdhëniet e tyre pasurore, në pajtim me Ligjin Nr. 2004/32 "
            "për Familjen e Kosovës.\n\n"
            "Neni 2 — Rregullimi i pasurisë\n"
            "{{ arrangement }}\n\n"
            "Neni 3 — Dispozita të fundit\n"
            "Palët deklarojnë se e kanë lexuar marrëveshjen, e kuptojnë "
            "përmbajtjen dhe pasojat e saj dhe e nënshkruajnë me vullnet "
            "të lirë, pa mashtrim a shtrëngim.\n\n"
            "{{ city }}, më {{ date }}\n\n"
            "Bashkëshorti/ja I                     Bashkëshorti/ja II\n\n"
            "_____________________          _____________________\n\n"
            "VËREJTJE E RËNDËSISHME: Sipas Ligjit Nr. 06/L-010 për Noterinë "
            "(neni 41), kjo marrëveshje është e vlefshme VETËM pasi të "
            "solemnizohet te noteri, me praninë personale të të dy "
            "bashkëshortëve."
        ),
    },
    {
        "code": "kerkese_trashegimie",
        "category": "noteria",
        "requires_notary": True,
        "notary_act": "trashegimi",
        "name": {
            "sq": "Kërkesë për fillimin e procedurës së trashëgimisë",
            "sr": "Zahtev za pokretanje ostavinskog postupka",
            "tr": "Miras işleminin başlatılması talebi",
            "bs": "Zahtjev za pokretanje ostavinskog postupka",
            "en": "Request to open the inheritance procedure",
            "zh": "启动继承程序申请",
        },
        "fields": [
            {"key": "sender_name", "type": "text", "label": {
                "sq": "Emri dhe mbiemri yt", "sr": "Vaše ime i prezime",
                "tr": "Adınız ve soyadınız", "bs": "Vaše ime i prezime",
                "en": "Your full name", "zh": "您的全名"}},
            {"key": "sender_id", "type": "text", "label": {
                "sq": "Numri personal dhe adresa jote",
                "sr": "Vaš lični broj i adresa",
                "tr": "Kişisel numaranız ve adresiniz",
                "bs": "Vaš lični broj i adresa",
                "en": "Your ID number and address", "zh": "您的身份证号和地址"}},
            {"key": "deceased", "type": "text", "label": {
                "sq": "Trashëgimlënësi — emri, data e vdekjes, vendbanimi i fundit",
                "sr": "Ostavilac — ime, datum smrti, poslednje prebivalište",
                "tr": "Miras bırakan — adı, ölüm tarihi, son ikametgahı",
                "bs": "Ostavilac — ime, datum smrti, posljednje prebivalište",
                "en": "Deceased — name, date of death, last residence",
                "zh": "被继承人——姓名、死亡日期、最后居住地"}},
            {"key": "relation", "type": "text", "label": {
                "sq": "Lidhja jote me trashëgimlënësin (p.sh. bir/bijë, bashkëshort/e)",
                "sr": "Vaš odnos sa ostaviocem (npr. sin/ćerka, supružnik)",
                "tr": "Miras bırakanla ilişkiniz (örn. oğlu/kızı, eşi)",
                "bs": "Vaš odnos s ostaviocem (npr. sin/kćerka, supružnik)",
                "en": "Your relation to the deceased (e.g. son/daughter, spouse)",
                "zh": "您与被继承人的关系（例如子女、配偶）"}},
            {"key": "heirs", "type": "textarea", "label": {
                "sq": "Trashëgimtarët e tjerë të njohur (emrat dhe lidhja)",
                "sr": "Ostali poznati naslednici (imena i srodstvo)",
                "tr": "Bilinen diğer mirasçılar (adlar ve yakınlık)",
                "bs": "Ostali poznati nasljednici (imena i srodstvo)",
                "en": "Other known heirs (names and relation)",
                "zh": "其他已知继承人（姓名和关系）"}},
            {"key": "estate", "type": "textarea", "label": {
                "sq": "Pasuria e trashëgimlënësit që e njeh (prona, llogari, vetura...)",
                "sr": "Imovina ostavioca koju poznajete (nepokretnosti, računi, vozila...)",
                "tr": "Bildiğiniz tereke (taşınmazlar, hesaplar, araçlar...)",
                "bs": "Imovina ostavioca koju poznajete (nekretnine, računi, vozila...)",
                "en": "The estate you know of (properties, accounts, vehicles...)",
                "zh": "您所知的遗产（不动产、账户、车辆等）"}},
            {"key": "city", "type": "text", "label": {
                "sq": "Qyteti", "sr": "Grad", "tr": "Şehir", "bs": "Grad",
                "en": "City", "zh": "城市"}},
        ],
        "body_sq": (
            "{{ sender_name }}\n{{ sender_id }}\n\n"
            "PËR: Noterin kompetent\n\n"
            "LËNDA: Kërkesë për fillimin e procedurës trashëgimore\n\n"
            "I/E nderuar,\n\n"
            "Unë {{ sender_name }}, në cilësinë e trashëgimtarit "
            "({{ relation }}), kërkoj fillimin e procedurës së trashëgimisë "
            "pas vdekjes së trashëgimlënësit:\n\n{{ deceased }}\n\n"
            "Trashëgimtarët e tjerë të njohur:\n{{ heirs }}\n\n"
            "Pasuria trashëgimore sipas njohurive të mia:\n{{ estate }}\n\n"
            "Bashkëngjitur do të dorëzoj certifikatën e vdekjes, certifikatën "
            "familjare dhe dëshmitë e pronësisë me rastin e paraqitjes te "
            "noteri.\n\n"
            "{{ city }}, më {{ date }}\n\n"
            "Me respekt,\n\n_____________________\n{{ sender_name }}"
        ),
    },
]


# ---------------------------------------------------------------------------
# Small-claims lawsuit (padia e vlerës së vogël) — guided public flow.
# Kept OUT of CITIZEN_DOC_TEMPLATES: it has its own wizard UI, a value cap
# (LPK neni 485.1: <= 500 EUR) and computed fields (competent court from the
# municipality via XK_BASIC_COURTS, court fee via UA 03/2025). Document tool,
# not representation and not legal advice.
XK_SMALL_CLAIM_TEMPLATE: dict = {
    "code": "padia_vlere_vogel",
    "name": {
        "sq": "Padi për kontest të vlerës së vogël (deri 500 €)",
        "sr": "Tužba u sporu male vrednosti (do 500 €)",
        "tr": "Küçük değerli uyuşmazlık davası (500 €'ya kadar)",
        "bs": "Tužba u sporu male vrijednosti (do 500 €)",
        "en": "Small-claims lawsuit (up to €500)",
        "zh": "小额诉讼起诉状（最高500欧元）",
    },
    "fields": [
        {"key": "sender_name", "type": "text", "label": {
            "sq": "Emri dhe mbiemri yt (paditësi)", "sr": "Vaše ime i prezime (tužilac)",
            "tr": "Adınız ve soyadınız (davacı)", "bs": "Vaše ime i prezime (tužilac)",
            "en": "Your full name (plaintiff)", "zh": "您的全名（原告）"}},
        {"key": "sender_address", "type": "text", "label": {
            "sq": "Adresa jote e plotë", "sr": "Vaša puna adresa",
            "tr": "Tam adresiniz", "bs": "Vaša puna adresa",
            "en": "Your full address", "zh": "您的完整地址"}},
        {"key": "sender_phone", "type": "text", "label": {
            "sq": "Telefoni / email-i yt", "sr": "Vaš telefon / imejl",
            "tr": "Telefonunuz / e-postanız", "bs": "Vaš telefon / e-mail",
            "en": "Your phone / email", "zh": "您的电话/电子邮件"}},
        {"key": "defendant_name", "type": "text", "label": {
            "sq": "Emri i të paditurit (personi ose firma që të detyrohet)",
            "sr": "Ime tuženog (osoba ili firma koja vam duguje)",
            "tr": "Davalının adı (size borçlu olan kişi veya şirket)",
            "bs": "Ime tuženog (osoba ili firma koja vam duguje)",
            "en": "Defendant's name (the person or business that owes you)",
            "zh": "被告姓名（欠您钱的个人或公司）"}},
        {"key": "defendant_address", "type": "text", "label": {
            "sq": "Adresa e të paditurit", "sr": "Adresa tuženog",
            "tr": "Davalının adresi", "bs": "Adresa tuženog",
            "en": "Defendant's address", "zh": "被告地址"}},
        {"key": "claim_amount", "type": "text", "label": {
            "sq": "Shuma që kërkon në euro (maksimumi 500)",
            "sr": "Iznos koji tražite u evrima (najviše 500)",
            "tr": "Talep ettiğiniz tutar, euro (en fazla 500)",
            "bs": "Iznos koji tražite u evrima (najviše 500)",
            "en": "Amount you claim in euros (max 500)",
            "zh": "您要求的金额（欧元，最高500）"}},
        {"key": "claim_basis", "type": "textarea", "label": {
            "sq": "Çfarë ndodhi? (kur, ku, çfarë u premtua dhe çfarë nuk u përmbush)",
            "sr": "Šta se dogodilo? (kada, gde, šta je obećano a nije ispunjeno)",
            "tr": "Ne oldu? (ne zaman, nerede, ne söz verildi ve ne yerine getirilmedi)",
            "bs": "Šta se dogodilo? (kada, gdje, šta je obećano a nije ispunjeno)",
            "en": "What happened? (when, where, what was promised and not fulfilled)",
            "zh": "发生了什么？（何时、何地、承诺了什么、未履行什么）"}},
        {"key": "evidence", "type": "textarea", "label": {
            "sq": "Provat që i ke (fatura, kontrata, foto, mesazhe, dëshmitarë...)",
            "sr": "Dokazi koje imate (računi, ugovori, fotografije, poruke, svedoci...)",
            "tr": "Elinizdeki kanıtlar (faturalar, sözleşmeler, fotoğraflar, mesajlar, tanıklar...)",
            "bs": "Dokazi koje imate (računi, ugovori, fotografije, poruke, svjedoci...)",
            "en": "Evidence you have (invoices, contracts, photos, messages, witnesses...)",
            "zh": "您拥有的证据（发票、合同、照片、信息、证人等）"}},
        # "city" is picked from XK_BASIC_COURTS municipalities in the wizard;
        # court_name/court_branch/court_fee are computed server-side.
    ],
    "body_sq": (
        "GJYKATA THEMELORE NË {{ court_name | upper }}\n"
        "{{ court_branch_line }}"
        "Departamenti i Përgjithshëm\n\n"
        "PADITËSI: {{ sender_name }}, {{ sender_address }}, "
        "kontakt: {{ sender_phone }}\n"
        "I PADITURI: {{ defendant_name }}, {{ defendant_address }}\n\n"
        "P A D I\n"
        "për kontest të vlerës së vogël\n"
        "(nenet 484–491 të Ligjit Nr. 03/L-006 për Procedurën Kontestimore)\n\n"
        "Vlera e kontestit: {{ claim_amount }} €\n\n"
        "I. GJENDJA FAKTIKE\n\n"
        "{{ claim_basis }}\n\n"
        "Përkundër kërkesave të paditësit, i padituri nuk e ka përmbushur "
        "detyrimin deri në ditën e paraqitjes së kësaj padie.\n\n"
        "II. KËRKESËPADIA\n\n"
        "Paditësi i propozon Gjykatës që, pas administrimit të provave, të "
        "APROVOHET kërkesëpadia dhe të DETYROHET i padituri që paditësit t'ia "
        "paguajë shumën prej {{ claim_amount }} €, me kamatë ligjore nga dita "
        "e paraqitjes së padisë deri në pagesën definitive, si dhe t'ia "
        "kompensojë shpenzimet e procedurës, të gjitha brenda 7 ditësh nga "
        "dita e plotfuqishmërisë së aktgjykimit.\n\n"
        "III. PROVAT\n\n"
        "{{ evidence }}\n\n"
        "Taksa gjyqësore: {{ court_fee }} € "
        "(UA Nr. 03/2025 i KGJK-së për Unifikimin e Taksave Gjyqësore).\n\n"
        "{{ city }}, më {{ date }}\n\n"
        "Paditësi:\n\n_____________________\n{{ sender_name }}"
    ),
}
