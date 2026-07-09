"""Backend i18n for client-facing output (emails, SMS, invoice PDF,
signature certificate). Kosovo's Law No. 02/L-37 on the Use of Languages makes
Albanian and Serbian official state-wide (Turkish and Bosnian in several
municipalities), so everything a client receives must follow the client's
language (Contact.locale), falling back to the tenant default, then Albanian.

UI strings live in frontend/src/lib/dictionaries.ts — this catalog is only
for text generated on the server.
"""
from app.config import settings

_SQ = {
    # Deadline reminder (lawyer)
    "reminder_subject": "[BoraLaw] Afat pas {days} ditësh: {title}",
    "reminder_matter": "Lënda",
    "reminder_deadline": "Afati",
    "reminder_expires": "Skadon",
    "reminder_legal_basis": "Baza ligjore",
    # SMS to client
    "sms_hearing_reminder": (
        "Kujtesë nga avokati juaj: {title} më {when} (lënda {ref}). "
        "Ju lutemi të jeni të pranishëm."
    ),
    # Shared email pieces
    "email_greeting": "E nderuar/i nderuar {name},",
    "email_signoff": "Me respekt,",
    "email_open_portal": "Kyçuni në portalin tuaj:",
    # Invoice email
    "email_invoice_subject": "Fatura {number} — {firm}",
    "email_invoice_attached": (
        "Në bashkëngjitje gjeni faturën {number} me vlerë {total} {currency}"
    ),
    "email_invoice_due": ", me afat pagese deri më {due}",
    "email_invoice_paylink": "Mund të paguani online me kartelë: {link}",
    # Signature request email
    "email_signature_subject": "Dokument për nënshkrim elektronik",
    "email_signature_body": (
        '{lawyer} ju ka dërguar dokumentin "{filename}" për nënshkrim elektronik.'
    ),
    "email_note": "Shënim: {note}",
    # Invoice PDF labels
    "inv_title": "FATURË",
    "inv_no": "Nr.",
    "inv_billed_to": "Faturuar për",
    "inv_details": "Detajet",
    "inv_issued": "Data e lëshimit",
    "inv_due": "Afati i pagesës",
    "inv_matter": "Lënda",
    "inv_desc": "Përshkrimi",
    "inv_qty": "Sasia",
    "inv_unit_price": "Çmimi njësi",
    "inv_amount": "Shuma",
    "inv_subtotal": "Nëntotali",
    "inv_vat": "TVSH",
    "inv_total_due": "TOTALI PËR PAGESË",
    "inv_payment": "Pagesa.",
    "inv_paid_on": "Paguar më {date}.",
    "inv_paid": "E paguar.",
    "inv_ref": "Referenca: {ref}.",
    "inv_pay_head": "Udhëzime pagese.",
    "inv_pay_body": (
        "Ju lutemi kryeni pagesën me transfer bankar duke shënuar numrin e "
        "faturës {number} si përshkrim."
    ),
    "inv_national_id": "Nr. identifikues",
    "inv_status_paid": "E PAGUAR",
    "inv_status_draft": "DRAFT",
    "inv_status_sent": "E DËRGUAR",
    "inv_status_void": "E ANULUAR",
    # Signature certificate subtitle (body stays Albanian — official record)
    "cert_subtitle": "Certifikatë e nënshkrimit elektronik",
    # Portal notifications to the lawyer
    "email_new_message_subject": "[{ref}] Mesazh i ri nga klienti",
    "email_new_message_body": '{client} ju shkroi për lëndën "{title}":',
    "email_signed_subject": "Dokumenti u nënshkrua",
    "email_signed_body": "{client} sapo nënshkroi dokumentin e kërkuar (kërkesa {request_id}).",
}

_SR = {
    "reminder_subject": "[BoraLaw] Rok za {days} dana: {title}",
    "reminder_matter": "Predmet",
    "reminder_deadline": "Rok",
    "reminder_expires": "Ističe",
    "reminder_legal_basis": "Pravni osnov",
    "sms_hearing_reminder": (
        "Podsetnik od vašeg advokata: {title} dana {when} (predmet {ref}). "
        "Molimo vas da budete prisutni."
    ),
    "email_greeting": "Poštovani/a {name},",
    "email_signoff": "S poštovanjem,",
    "email_open_portal": "Prijavite se na svoj portal:",
    "email_invoice_subject": "Faktura {number} — {firm}",
    "email_invoice_attached": (
        "U prilogu se nalazi faktura {number} u iznosu od {total} {currency}"
    ),
    "email_invoice_due": ", sa rokom plaćanja do {due}",
    "email_invoice_paylink": "Možete platiti onlajn karticom: {link}",
    "email_signature_subject": "Dokument za elektronski potpis",
    "email_signature_body": (
        '{lawyer} vam je poslao/la dokument "{filename}" na elektronsko potpisivanje.'
    ),
    "email_note": "Napomena: {note}",
    "inv_title": "FAKTURA",
    "inv_no": "Br.",
    "inv_billed_to": "Fakturisano za",
    "inv_details": "Detalji",
    "inv_issued": "Datum izdavanja",
    "inv_due": "Rok plaćanja",
    "inv_matter": "Predmet",
    "inv_desc": "Opis",
    "inv_qty": "Količina",
    "inv_unit_price": "Jedinična cena",
    "inv_amount": "Iznos",
    "inv_subtotal": "Međuzbir",
    "inv_vat": "PDV",
    "inv_total_due": "UKUPNO ZA PLAĆANJE",
    "inv_payment": "Plaćanje.",
    "inv_paid_on": "Plaćeno dana {date}.",
    "inv_paid": "Plaćeno.",
    "inv_ref": "Referenca: {ref}.",
    "inv_pay_head": "Uputstva za plaćanje.",
    "inv_pay_body": (
        "Molimo izvršite plaćanje bankovnim transferom navodeći broj fakture "
        "{number} u opisu."
    ),
    "inv_national_id": "Identifikacioni br.",
    "inv_status_paid": "PLAĆENA",
    "inv_status_draft": "NACRT",
    "inv_status_sent": "POSLATA",
    "inv_status_void": "PONIŠTENA",
    "cert_subtitle": "Sertifikat elektronskog potpisa",
    "email_new_message_subject": "[{ref}] Nova poruka od klijenta",
    "email_new_message_body": '{client} vam je pisao/la o predmetu "{title}":',
    "email_signed_subject": "Dokument je potpisan",
    "email_signed_body": "{client} je upravo potpisao/la traženi dokument (zahtev {request_id}).",
}

_TR = {
    "reminder_subject": "[BoraLaw] {days} gün sonra süre: {title}",
    "reminder_matter": "Dosya",
    "reminder_deadline": "Süre",
    "reminder_expires": "Son tarih",
    "reminder_legal_basis": "Yasal dayanak",
    "sms_hearing_reminder": (
        "Avukatınızdan hatırlatma: {title}, {when} tarihinde (dosya {ref}). "
        "Lütfen hazır bulunun."
    ),
    "email_greeting": "Sayın {name},",
    "email_signoff": "Saygılarımızla,",
    "email_open_portal": "Portalınıza giriş yapın:",
    "email_invoice_subject": "Fatura {number} — {firm}",
    "email_invoice_attached": (
        "Ekte {total} {currency} tutarındaki {number} numaralı faturayı bulabilirsiniz"
    ),
    "email_invoice_due": ", son ödeme tarihi {due}",
    "email_invoice_paylink": "Kartla online ödeyebilirsiniz: {link}",
    "email_signature_subject": "Elektronik imza için belge",
    "email_signature_body": (
        '{lawyer} size "{filename}" belgesini elektronik imza için gönderdi.'
    ),
    "email_note": "Not: {note}",
    "inv_title": "FATURA",
    "inv_no": "No.",
    "inv_billed_to": "Fatura edilen",
    "inv_details": "Detaylar",
    "inv_issued": "Düzenleme tarihi",
    "inv_due": "Son ödeme tarihi",
    "inv_matter": "Dosya",
    "inv_desc": "Açıklama",
    "inv_qty": "Miktar",
    "inv_unit_price": "Birim fiyat",
    "inv_amount": "Tutar",
    "inv_subtotal": "Ara toplam",
    "inv_vat": "KDV",
    "inv_total_due": "ÖDENECEK TOPLAM",
    "inv_payment": "Ödeme.",
    "inv_paid_on": "{date} tarihinde ödendi.",
    "inv_paid": "Ödendi.",
    "inv_ref": "Referans: {ref}.",
    "inv_pay_head": "Ödeme talimatları.",
    "inv_pay_body": (
        "Lütfen açıklamaya {number} fatura numarasını yazarak banka havalesi "
        "ile ödeme yapınız."
    ),
    "inv_national_id": "Kimlik no.",
    "inv_status_paid": "ÖDENDİ",
    "inv_status_draft": "TASLAK",
    "inv_status_sent": "GÖNDERİLDİ",
    "inv_status_void": "İPTAL",
    "cert_subtitle": "Elektronik imza sertifikası",
    "email_new_message_subject": "[{ref}] Müvekkilden yeni mesaj",
    "email_new_message_body": '{client} size "{title}" dosyası hakkında yazdı:',
    "email_signed_subject": "Belge imzalandı",
    "email_signed_body": "{client} az önce istenen belgeyi imzaladı (talep {request_id}).",
}

_BS = {
    "reminder_subject": "[BoraLaw] Rok za {days} dana: {title}",
    "reminder_matter": "Predmet",
    "reminder_deadline": "Rok",
    "reminder_expires": "Ističe",
    "reminder_legal_basis": "Pravni osnov",
    "sms_hearing_reminder": (
        "Podsjetnik od vašeg advokata: {title} dana {when} (predmet {ref}). "
        "Molimo vas da budete prisutni."
    ),
    "email_greeting": "Poštovani/a {name},",
    "email_signoff": "S poštovanjem,",
    "email_open_portal": "Prijavite se na svoj portal:",
    "email_invoice_subject": "Faktura {number} — {firm}",
    "email_invoice_attached": (
        "U prilogu se nalazi faktura {number} u iznosu od {total} {currency}"
    ),
    "email_invoice_due": ", s rokom plaćanja do {due}",
    "email_invoice_paylink": "Možete platiti online karticom: {link}",
    "email_signature_subject": "Dokument za elektronski potpis",
    "email_signature_body": (
        '{lawyer} vam je poslao/la dokument "{filename}" na elektronsko potpisivanje.'
    ),
    "email_note": "Napomena: {note}",
    "inv_title": "FAKTURA",
    "inv_no": "Br.",
    "inv_billed_to": "Fakturisano za",
    "inv_details": "Detalji",
    "inv_issued": "Datum izdavanja",
    "inv_due": "Rok plaćanja",
    "inv_matter": "Predmet",
    "inv_desc": "Opis",
    "inv_qty": "Količina",
    "inv_unit_price": "Jedinična cijena",
    "inv_amount": "Iznos",
    "inv_subtotal": "Međuzbir",
    "inv_vat": "PDV",
    "inv_total_due": "UKUPNO ZA PLAĆANJE",
    "inv_payment": "Plaćanje.",
    "inv_paid_on": "Plaćeno dana {date}.",
    "inv_paid": "Plaćeno.",
    "inv_ref": "Referenca: {ref}.",
    "inv_pay_head": "Upute za plaćanje.",
    "inv_pay_body": (
        "Molimo izvršite plaćanje bankovnim transferom navodeći broj fakture "
        "{number} u opisu."
    ),
    "inv_national_id": "Identifikacijski br.",
    "inv_status_paid": "PLAĆENA",
    "inv_status_draft": "NACRT",
    "inv_status_sent": "POSLANA",
    "inv_status_void": "PONIŠTENA",
    "cert_subtitle": "Certifikat elektronskog potpisa",
    "email_new_message_subject": "[{ref}] Nova poruka od klijenta",
    "email_new_message_body": '{client} vam je pisao/la o predmetu "{title}":',
    "email_signed_subject": "Dokument je potpisan",
    "email_signed_body": "{client} je upravo potpisao/la traženi dokument (zahtjev {request_id}).",
}

_EN = {
    "reminder_subject": "[BoraLaw] Deadline in {days} days: {title}",
    "reminder_matter": "Matter",
    "reminder_deadline": "Deadline",
    "reminder_expires": "Due",
    "reminder_legal_basis": "Legal basis",
    "sms_hearing_reminder": (
        "Reminder from your lawyer: {title} on {when} (matter {ref}). "
        "Please make sure to attend."
    ),
    "email_greeting": "Dear {name},",
    "email_signoff": "Kind regards,",
    "email_open_portal": "Log in to your portal:",
    "email_invoice_subject": "Invoice {number} — {firm}",
    "email_invoice_attached": (
        "Attached you will find invoice {number} for {total} {currency}"
    ),
    "email_invoice_due": ", due by {due}",
    "email_invoice_paylink": "You can pay online by card: {link}",
    "email_signature_subject": "Document for electronic signature",
    "email_signature_body": (
        '{lawyer} sent you the document "{filename}" for electronic signature.'
    ),
    "email_note": "Note: {note}",
    "inv_title": "INVOICE",
    "inv_no": "No.",
    "inv_billed_to": "Billed to",
    "inv_details": "Details",
    "inv_issued": "Issue date",
    "inv_due": "Payment due",
    "inv_matter": "Matter",
    "inv_desc": "Description",
    "inv_qty": "Quantity",
    "inv_unit_price": "Unit price",
    "inv_amount": "Amount",
    "inv_subtotal": "Subtotal",
    "inv_vat": "VAT",
    "inv_total_due": "TOTAL DUE",
    "inv_payment": "Payment.",
    "inv_paid_on": "Paid on {date}.",
    "inv_paid": "Paid.",
    "inv_ref": "Reference: {ref}.",
    "inv_pay_head": "Payment instructions.",
    "inv_pay_body": (
        "Please pay by bank transfer, quoting invoice number {number} in the "
        "description."
    ),
    "inv_national_id": "ID no.",
    "inv_status_paid": "PAID",
    "inv_status_draft": "DRAFT",
    "inv_status_sent": "SENT",
    "inv_status_void": "VOID",
    "cert_subtitle": "Certificate of electronic signature",
    "email_new_message_subject": "[{ref}] New message from the client",
    "email_new_message_body": '{client} wrote to you about the matter "{title}":',
    "email_signed_subject": "Document signed",
    "email_signed_body": "{client} just signed the requested document (request {request_id}).",
}

_ZH = {
    "reminder_subject": "[BoraLaw] {days} 天后到期：{title}",
    "reminder_matter": "案件",
    "reminder_deadline": "期限",
    "reminder_expires": "到期",
    "reminder_legal_basis": "法律依据",
    "sms_hearing_reminder": (
        "您的律师提醒：{title}，时间 {when}（案件 {ref}）。请务必出席。"
    ),
    "email_greeting": "尊敬的 {name}：",
    "email_signoff": "此致",
    "email_open_portal": "登录您的门户：",
    "email_invoice_subject": "发票 {number} — {firm}",
    "email_invoice_attached": "附件为发票 {number}，金额 {total} {currency}",
    "email_invoice_due": "，付款期限至 {due}",
    "email_invoice_paylink": "您可以在线刷卡支付：{link}",
    "email_signature_subject": "待电子签署的文件",
    "email_signature_body": "{lawyer} 向您发送了文件“{filename}”以供电子签署。",
    "email_note": "备注：{note}",
    "inv_title": "发票",
    "inv_no": "编号",
    "inv_billed_to": "收票方",
    "inv_details": "详情",
    "inv_issued": "开具日期",
    "inv_due": "付款期限",
    "inv_matter": "案件",
    "inv_desc": "描述",
    "inv_qty": "数量",
    "inv_unit_price": "单价",
    "inv_amount": "金额",
    "inv_subtotal": "小计",
    "inv_vat": "增值税",
    "inv_total_due": "应付总额",
    "inv_payment": "付款。",
    "inv_paid_on": "已于 {date} 付款。",
    "inv_paid": "已付款。",
    "inv_ref": "参考号：{ref}。",
    "inv_pay_head": "付款说明。",
    "inv_pay_body": "请通过银行转账付款，并在备注中注明发票号 {number}。",
    "inv_national_id": "证件号",
    "inv_status_paid": "已付款",
    "inv_status_draft": "草稿",
    "inv_status_sent": "已发送",
    "inv_status_void": "已作废",
    "cert_subtitle": "电子签名证书",
    "email_new_message_subject": "[{ref}] 客户发来新消息",
    "email_new_message_body": "{client} 就案件“{title}”给您留言：",
    "email_signed_subject": "文件已签署",
    "email_signed_body": "{client} 刚刚签署了所请求的文件（请求 {request_id}）。",
}

CATALOG: dict[str, dict[str, str]] = {
    "sq": _SQ, "sr": _SR, "tr": _TR, "bs": _BS, "en": _EN, "zh": _ZH,
}


def normalize_locale(locale: str | None) -> str:
    """Best supported locale for a raw value, falling back to the default."""
    if locale:
        code = locale.lower().split("-")[0].split("_")[0]
        if code in CATALOG:
            return code
    default = settings.default_locale
    return default if default in CATALOG else "sq"


def pick_locale(*candidates: str | None) -> str:
    """First supported locale from the candidates (e.g. contact's, then the
    tenant default), falling back to the app default."""
    for candidate in candidates:
        if candidate:
            code = candidate.lower().split("-")[0].split("_")[0]
            if code in CATALOG:
                return code
    return normalize_locale(None)


def tr(locale: str | None, key: str, **kwargs) -> str:
    """Translate a backend string; falls back to Albanian, then the key."""
    loc = normalize_locale(locale)
    text = CATALOG[loc].get(key) or CATALOG["sq"].get(key) or key
    return text.format(**kwargs) if kwargs else text


def bilabel(locale: str | None, key: str) -> str:
    """'Albanian / client language' label for official bilingual documents
    (invoices). Returns just the Albanian label when the locales match."""
    loc = normalize_locale(locale)
    sq_text = CATALOG["sq"].get(key, key)
    if loc == "sq":
        return sq_text
    other = CATALOG[loc].get(key)
    if not other or other == sq_text:
        return sq_text
    return f"{sq_text} / {other}"
