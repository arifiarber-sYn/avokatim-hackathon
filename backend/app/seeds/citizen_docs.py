"""Citizen self-service document templates (Phase 4) — data, not code.

Deterministic Jinja templates: the citizen fills plain-language fields and
downloads a formal letter as PDF. Bodies are in Albanian (the language of
official correspondence in Kosovo); labels are localized in the UI.
No LLM involved — output is predictable and reviewable.
"""

# Categories group templates in the UI: institucionet / puna / konsumatori /
# te_pergjithshme. Category labels are localized on the frontend.
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
]
