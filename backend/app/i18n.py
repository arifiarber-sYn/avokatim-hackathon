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
    "reminder_subject": "[AvokatIM] Afat pas {days} ditësh: {title}",
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
    # Marketplace (citizens)
    "citizen_verify_subject": "AvokatIM — Konfirmo email-in",
    "citizen_verify_body": (
        "Konfirmo adresën tënde të email-it duke hapur këtë link:\n{url}\n\n"
        "Linku vlen 3 ditë."
    ),
    "citizen_reset_subject": "AvokatIM — Rivendos fjalëkalimin",
    "citizen_reset_body": (
        "Ke kërkuar rivendosjen e fjalëkalimit. Hape këtë link për të vendosur një fjalëkalim të ri:\n{url}\n\n"
        "Linku vlen 1 orë. Nëse s'e ke kërkuar ti, injoroje këtë email."
    ),
    "case_claimed_subject": "AvokatIM — Një avokat e mori rastin tënd",
    "case_claimed_body": (
        "Rasti yt u mor nga {firm}. Avokati do të të kontaktojë së shpejti — "
        "mund t'i shkruash edhe ti te 'Rasti im':\n{url}"
    ),
    "case_directed_subject": "AvokatIM — Kërkesë e re nga një qytetar",
    "case_directed_body": (
        "Një qytetar ju ka dërguar një kërkesë ({category}, {city}). "
        "Shikojeni te Tregu në AvokatIM:\n{url}"
    ),
    "case_message_subject": "AvokatIM — Mesazh i ri për rastin tënd",
    "case_message_body": "Keni një mesazh të ri për rastin tuaj:\n{url}",
    "case_portal_ready_subject": "AvokatIM — Rasti u pranua, portali yt është gati",
    "case_portal_ready_body": (
        "{firm} e pranoi rastin tënd. Tani ke qasje në portalin e klientit me "
        "të njëjtin email dhe fjalëkalim:\n{url}"
    ),
    "booking_new_subject": "AvokatIM — Kërkesë e re për konsultë",
    "booking_new_body": (
        "{citizen} kërkoi një konsultë më {when}. Konfirmoje ose refuzoje "
        "te Tregu → Konsultat:\n{url}"
    ),
    "booking_confirmed_subject": "AvokatIM — Konsulta u konfirmua",
    "booking_confirmed_body": "{lawyer} e konfirmoi konsultën tënde më {when}.",
    "booking_declined_subject": "AvokatIM — Konsulta nuk u konfirmua",
    "booking_declined_body": (
        "{lawyer} nuk mund ta mbajë konsultën më {when}. "
        "Zgjidh një termin tjetër:\n{url}"
    ),
    "sos_alert_subject": "AvokatIM — SOS: qytetar kërkon ndihmë URGJENTE",
    "sos_alert_body": (
        "Një qytetar kërkon ndihmë urgjente ({city}). Ti je kujdestar SOS — "
        "hape Tregun dhe merre rastin sa më parë:\n{url}"
    ),
    "case_match_subject": "AvokatIM — Rast i ri që përputhet me profilin tënd",
    "case_match_body": (
        "Në Treg sapo u postua një rast që përputhet me profilin tënd "
        "({category}, {city}). Avokati i parë që e merr, e fiton:\n{url}"
    ),
    "verify_approved_subject": "AvokatIM — Licenca juaj OAK u verifikua",
    "verify_approved_body": (
        "Licenca juaj OAK u verifikua me sukses. Profili juaj tani shfaqet "
        "në drejtorinë publike dhe mund të merrni raste nga Tregu:\n{url}"
    ),
    "verify_rejected_subject": "AvokatIM — Verifikimi i licencës OAK nuk u aprovua",
    "verify_rejected_body": (
        "Verifikimi i licencës suaj OAK nuk u aprovua. Shënim: {note}\n"
        "Korrigjoni numrin e licencës në Cilësimet për ta ridërguar:\n{url}"
    ),
    "platform_invoice_subject": "AvokatIM — Fatura e abonimit {number}",
    "platform_invoice_body": (
        "Fatura e abonimit {number} për periudhën {period}:\n"
        "{seats} përdorues × {price} € = {amount} €\n"
        "Afati i pagesës: {due}\n\n"
        "Pagesa me transfer bankar (shëno numrin e faturës si referencë):\n{bank}\n\n"
        "Detajet dhe pagesa me kartelë (nëse është aktive) te Cilësimet → Abonimi:\n{url}"
    ),
    "platform_overdue_subject": "AvokatIM — Fatura {number} ka kaluar afatin",
    "platform_overdue_body": (
        "Fatura e abonimit {number} ({amount} €) ka kaluar afatin {days} ditë. "
        "Pas {grace} ditësh vonesë ndalen rastet e reja nga Tregu — të dhënat "
        "tuaja mbeten gjithmonë të qasshme. Paguaje te Cilësimet → Abonimi:\n{url}"
    ),
    "trial_ending_subject": "AvokatIM — Prova falas përfundon për {days} ditë",
    "trial_ending_body": (
        "Prova juaj 3-mujore falas përfundon për {days} ditë. Kalo në planin "
        "me pagesë ({price} €/përdorues/muaj — gjithçka brenda + raste pa "
        "kufi nga Tregu) te Cilësimet → Abonimi:\n{url}"
    ),
}

_SR = {
    "reminder_subject": "[AvokatIM] Rok za {days} dana: {title}",
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
    # Marketplace (citizens)
    "citizen_verify_subject": "AvokatIM — Potvrdite email",
    "citizen_verify_body": (
        "Potvrdite svoju email adresu otvaranjem ovog linka:\n{url}\n\n"
        "Link važi 3 dana."
    ),
    "citizen_reset_subject": "AvokatIM — Resetujte lozinku",
    "citizen_reset_body": (
        "Zatražili ste resetovanje lozinke. Otvorite ovaj link da postavite novu lozinku:\n{url}\n\n"
        "Link važi 1 sat. Ako niste vi tražili, ignorišite ovaj email."
    ),
    "case_claimed_subject": "AvokatIM — Advokat je preuzeo vaš slučaj",
    "case_claimed_body": (
        "Vaš slučaj je preuzela kancelarija {firm}. Advokat će vas uskoro "
        "kontaktirati — možete i vi pisati na 'Moj slučaj':\n{url}"
    ),
    "case_directed_subject": "AvokatIM — Novi zahtev od građanina",
    "case_directed_body": (
        "Građanin vam je poslao zahtev ({category}, {city}). "
        "Pogledajte na Tržištu u AvokatIM:\n{url}"
    ),
    "case_message_subject": "AvokatIM — Nova poruka za vaš slučaj",
    "case_message_body": "Imate novu poruku za vaš slučaj:\n{url}",
    "case_portal_ready_subject": "AvokatIM — Slučaj je prihvaćen, vaš portal je spreman",
    "case_portal_ready_body": (
        "{firm} je prihvatila vaš slučaj. Sada imate pristup klijentskom "
        "portalu sa istim emailom i lozinkom:\n{url}"
    ),
    "booking_new_subject": "AvokatIM — Novi zahtev za konsultaciju",
    "booking_new_body": (
        "{citizen} je zatražio/la konsultaciju {when}. Potvrdite ili odbijte "
        "u Tržištu → Konsultacije:\n{url}"
    ),
    "booking_confirmed_subject": "AvokatIM — Konsultacija je potvrđena",
    "booking_confirmed_body": "{lawyer} je potvrdio/la vašu konsultaciju {when}.",
    "booking_declined_subject": "AvokatIM — Konsultacija nije potvrđena",
    "booking_declined_body": (
        "{lawyer} ne može održati konsultaciju {when}. "
        "Izaberite drugi termin:\n{url}"
    ),
    "sos_alert_subject": "AvokatIM — SOS: građanin traži HITNU pomoć",
    "sos_alert_body": (
        "Građanin traži hitnu pomoć ({city}). Vi ste SOS dežurni — "
        "otvorite Tržište i preuzmite slučaj što pre:\n{url}"
    ),
    "case_match_subject": "AvokatIM — Novi slučaj koji odgovara vašem profilu",
    "case_match_body": (
        "Na Tržištu je upravo objavljen slučaj koji odgovara vašem profilu "
        "({category}, {city}). Prvi advokat koji ga preuzme — dobija ga:\n{url}"
    ),
    "verify_approved_subject": "AvokatIM — Vaša AKK licenca je verifikovana",
    "verify_approved_body": (
        "Vaša advokatska licenca je uspešno verifikovana. Vaš profil je sada "
        "vidljiv u javnom imeniku i možete preuzimati slučajeve sa Tržišta:\n{url}"
    ),
    "verify_rejected_subject": "AvokatIM — Verifikacija licence nije odobrena",
    "verify_rejected_body": (
        "Verifikacija vaše advokatske licence nije odobrena. Napomena: {note}\n"
        "Ispravite broj licence u Podešavanjima da biste je ponovo poslali:\n{url}"
    ),
    "platform_invoice_subject": "AvokatIM — Faktura pretplate {number}",
    "platform_invoice_body": (
        "Faktura pretplate {number} za period {period}:\n"
        "{seats} korisnika × {price} € = {amount} €\n"
        "Rok plaćanja: {due}\n\n"
        "Plaćanje bankovnim transferom (navedite broj fakture kao referencu):\n{bank}\n\n"
        "Detalji i plaćanje karticom (ako je aktivno) u Podešavanja → Pretplata:\n{url}"
    ),
    "platform_overdue_subject": "AvokatIM — Faktura {number} je prekoračila rok",
    "platform_overdue_body": (
        "Faktura pretplate {number} ({amount} €) kasni {days} dana. "
        "Nakon {grace} dana kašnjenja obustavljaju se novi slučajevi sa Tržišta — "
        "vaši podaci ostaju uvek dostupni. Platite u Podešavanja → Pretplata:\n{url}"
    ),
    "trial_ending_subject": "AvokatIM — Besplatna proba ističe za {days} dana",
    "trial_ending_body": (
        "Vaša besplatna proba od 3 meseca ističe za {days} dana. Pređite na "
        "plaćeni plan ({price} €/korisnik/mesečno — sve uključeno + neograničeni "
        "slučajevi sa Tržišta) u Podešavanja → Pretplata:\n{url}"
    ),
}

_TR = {
    "reminder_subject": "[AvokatIM] {days} gün sonra süre: {title}",
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
    # Marketplace (citizens)
    "citizen_verify_subject": "AvokatIM — E-postanızı doğrulayın",
    "citizen_verify_body": (
        "E-posta adresinizi bu bağlantıyı açarak doğrulayın:\n{url}\n\n"
        "Bağlantı 3 gün geçerlidir."
    ),
    "citizen_reset_subject": "AvokatIM — Şifrenizi sıfırlayın",
    "citizen_reset_body": (
        "Şifre sıfırlama talebinde bulundunuz. Yeni bir şifre belirlemek için bu bağlantıyı açın:\n{url}\n\n"
        "Bağlantı 1 saat geçerlidir. Siz talep etmediyseniz bu e-postayı yok sayın."
    ),
    "case_claimed_subject": "AvokatIM — Bir avukat davanızı üstlendi",
    "case_claimed_body": (
        "Davanız {firm} tarafından üstlenildi. Avukat kısa süre içinde sizinle "
        "iletişime geçecek — 'Davam' bölümünden siz de yazabilirsiniz:\n{url}"
    ),
    "case_directed_subject": "AvokatIM — Bir vatandaştan yeni talep",
    "case_directed_body": (
        "Bir vatandaş size talep gönderdi ({category}, {city}). "
        "AvokatIM'de Pazar bölümünden inceleyin:\n{url}"
    ),
    "case_message_subject": "AvokatIM — Davanız için yeni mesaj",
    "case_message_body": "Davanız için yeni bir mesajınız var:\n{url}",
    "case_portal_ready_subject": "AvokatIM — Davanız kabul edildi, portalınız hazır",
    "case_portal_ready_body": (
        "{firm} davanızı kabul etti. Artık aynı e-posta ve şifreyle müvekkil "
        "portalına erişebilirsiniz:\n{url}"
    ),
    "booking_new_subject": "AvokatIM — Yeni danışma talebi",
    "booking_new_body": (
        "{citizen}, {when} için danışma talep etti. Pazar → Danışmalar "
        "bölümünden onaylayın veya reddedin:\n{url}"
    ),
    "booking_confirmed_subject": "AvokatIM — Danışma onaylandı",
    "booking_confirmed_body": "{lawyer}, {when} tarihli danışmanızı onayladı.",
    "booking_declined_subject": "AvokatIM — Danışma onaylanmadı",
    "booking_declined_body": (
        "{lawyer}, {when} tarihli danışmayı gerçekleştiremiyor. "
        "Başka bir zaman seçin:\n{url}"
    ),
    "sos_alert_subject": "AvokatIM — SOS: bir vatandaş ACİL yardım istiyor",
    "sos_alert_body": (
        "Bir vatandaş acil yardım istiyor ({city}). SOS nöbetçisisiniz — "
        "Pazar'ı açın ve davayı en kısa sürede üstlenin:\n{url}"
    ),
    "case_match_subject": "AvokatIM — Profilinize uyan yeni bir dava",
    "case_match_body": (
        "Pazar'da profilinize uyan bir dava yayınlandı ({category}, {city}). "
        "Davayı ilk üstlenen avukat kazanır:\n{url}"
    ),
    "verify_approved_subject": "AvokatIM — Baro lisansınız doğrulandı",
    "verify_approved_body": (
        "Avukatlık lisansınız başarıyla doğrulandı. Profiliniz artık kamu "
        "rehberinde görünüyor ve Pazar'dan dava üstlenebilirsiniz:\n{url}"
    ),
    "verify_rejected_subject": "AvokatIM — Lisans doğrulaması onaylanmadı",
    "verify_rejected_body": (
        "Avukatlık lisansınızın doğrulaması onaylanmadı. Not: {note}\n"
        "Yeniden göndermek için Ayarlar'da lisans numarasını düzeltin:\n{url}"
    ),
    "platform_invoice_subject": "AvokatIM — Abonelik faturası {number}",
    "platform_invoice_body": (
        "{period} dönemi için abonelik faturası {number}:\n"
        "{seats} kullanıcı × {price} € = {amount} €\n"
        "Son ödeme tarihi: {due}\n\n"
        "Banka havalesiyle ödeme (fatura numarasını referans olarak yazın):\n{bank}\n\n"
        "Detaylar ve kartla ödeme (aktifse) Ayarlar → Abonelik bölümünde:\n{url}"
    ),
    "platform_overdue_subject": "AvokatIM — {number} numaralı fatura vadesini geçti",
    "platform_overdue_body": (
        "Abonelik faturası {number} ({amount} €) {days} gündür gecikmiş durumda. "
        "{grace} gün gecikmeden sonra Pazar'dan yeni davalar durdurulur — "
        "verileriniz her zaman erişilebilir kalır. Ayarlar → Abonelik'ten ödeyin:\n{url}"
    ),
    "trial_ending_subject": "AvokatIM — Ücretsiz deneme {days} gün içinde bitiyor",
    "trial_ending_body": (
        "3 aylık ücretsiz denemeniz {days} gün içinde bitiyor. Ücretli plana "
        "geçin ({price} €/kullanıcı/ay — her şey dahil + Pazar'dan sınırsız "
        "dava) Ayarlar → Abonelik:\n{url}"
    ),
}

_BS = {
    "reminder_subject": "[AvokatIM] Rok za {days} dana: {title}",
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
    # Marketplace (citizens)
    "citizen_verify_subject": "AvokatIM — Potvrdite email",
    "citizen_verify_body": (
        "Potvrdite svoju email adresu otvaranjem ovog linka:\n{url}\n\n"
        "Link vrijedi 3 dana."
    ),
    "citizen_reset_subject": "AvokatIM — Resetujte lozinku",
    "citizen_reset_body": (
        "Zatražili ste resetovanje lozinke. Otvorite ovaj link da postavite novu lozinku:\n{url}\n\n"
        "Link vrijedi 1 sat. Ako niste vi tražili, ignorišite ovaj e-mail."
    ),
    "case_claimed_subject": "AvokatIM — Advokat je preuzeo vaš slučaj",
    "case_claimed_body": (
        "Vaš slučaj je preuzela kancelarija {firm}. Advokat će vas uskoro "
        "kontaktirati — možete i vi pisati na 'Moj slučaj':\n{url}"
    ),
    "case_directed_subject": "AvokatIM — Novi zahtjev od građanina",
    "case_directed_body": (
        "Građanin vam je poslao zahtjev ({category}, {city}). "
        "Pogledajte na Tržištu u AvokatIM:\n{url}"
    ),
    "case_message_subject": "AvokatIM — Nova poruka za vaš slučaj",
    "case_message_body": "Imate novu poruku za vaš slučaj:\n{url}",
    "case_portal_ready_subject": "AvokatIM — Slučaj je prihvaćen, vaš portal je spreman",
    "case_portal_ready_body": (
        "{firm} je prihvatila vaš slučaj. Sada imate pristup klijentskom "
        "portalu s istim emailom i lozinkom:\n{url}"
    ),
    "booking_new_subject": "AvokatIM — Novi zahtjev za konsultaciju",
    "booking_new_body": (
        "{citizen} je zatražio/la konsultaciju {when}. Potvrdite ili odbijte "
        "u Tržištu → Konsultacije:\n{url}"
    ),
    "booking_confirmed_subject": "AvokatIM — Konsultacija je potvrđena",
    "booking_confirmed_body": "{lawyer} je potvrdio/la vašu konsultaciju {when}.",
    "booking_declined_subject": "AvokatIM — Konsultacija nije potvrđena",
    "booking_declined_body": (
        "{lawyer} ne može održati konsultaciju {when}. "
        "Odaberite drugi termin:\n{url}"
    ),
    "sos_alert_subject": "AvokatIM — SOS: građanin traži HITNU pomoć",
    "sos_alert_body": (
        "Građanin traži hitnu pomoć ({city}). Vi ste SOS dežurni — "
        "otvorite Tržište i preuzmite slučaj što prije:\n{url}"
    ),
    "case_match_subject": "AvokatIM — Novi slučaj koji odgovara vašem profilu",
    "case_match_body": (
        "Na Tržištu je upravo objavljen slučaj koji odgovara vašem profilu "
        "({category}, {city}). Prvi advokat koji ga preuzme — dobija ga:\n{url}"
    ),
    "verify_approved_subject": "AvokatIM — Vaša advokatska licenca je verificirana",
    "verify_approved_body": (
        "Vaša advokatska licenca je uspješno verificirana. Vaš profil je sada "
        "vidljiv u javnom imeniku i možete preuzimati slučajeve s Tržišta:\n{url}"
    ),
    "verify_rejected_subject": "AvokatIM — Verifikacija licence nije odobrena",
    "verify_rejected_body": (
        "Verifikacija vaše advokatske licence nije odobrena. Napomena: {note}\n"
        "Ispravite broj licence u Postavkama da biste je ponovo poslali:\n{url}"
    ),
    "platform_invoice_subject": "AvokatIM — Faktura pretplate {number}",
    "platform_invoice_body": (
        "Faktura pretplate {number} za period {period}:\n"
        "{seats} korisnika × {price} € = {amount} €\n"
        "Rok plaćanja: {due}\n\n"
        "Plaćanje bankovnim transferom (navedite broj fakture kao referencu):\n{bank}\n\n"
        "Detalji i plaćanje karticom (ako je aktivno) u Postavke → Pretplata:\n{url}"
    ),
    "platform_overdue_subject": "AvokatIM — Faktura {number} je prekoračila rok",
    "platform_overdue_body": (
        "Faktura pretplate {number} ({amount} €) kasni {days} dana. "
        "Nakon {grace} dana kašnjenja obustavljaju se novi slučajevi s Tržišta — "
        "vaši podaci ostaju uvijek dostupni. Platite u Postavke → Pretplata:\n{url}"
    ),
    "trial_ending_subject": "AvokatIM — Besplatna proba ističe za {days} dana",
    "trial_ending_body": (
        "Vaša besplatna proba od 3 mjeseca ističe za {days} dana. Pređite na "
        "plaćeni plan ({price} €/korisnik/mjesečno — sve uključeno + neograničeni "
        "slučajevi s Tržišta) u Postavke → Pretplata:\n{url}"
    ),
}

_EN = {
    "reminder_subject": "[AvokatIM] Deadline in {days} days: {title}",
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
    # Marketplace (citizens)
    "citizen_verify_subject": "AvokatIM — Confirm your email",
    "citizen_verify_body": (
        "Confirm your email address by opening this link:\n{url}\n\n"
        "The link is valid for 3 days."
    ),
    "citizen_reset_subject": "AvokatIM — Reset your password",
    "citizen_reset_body": (
        "You requested a password reset. Open this link to set a new password:\n{url}\n\n"
        "The link is valid for 1 hour. If you did not request this, ignore this email."
    ),
    "case_claimed_subject": "AvokatIM — A lawyer took your case",
    "case_claimed_body": (
        "Your case was taken by {firm}. The lawyer will contact you shortly — "
        "you can also write to them under 'My case':\n{url}"
    ),
    "case_directed_subject": "AvokatIM — New request from a citizen",
    "case_directed_body": (
        "A citizen sent you a request ({category}, {city}). "
        "See it in the AvokatIM Marketplace:\n{url}"
    ),
    "case_message_subject": "AvokatIM — New message about your case",
    "case_message_body": "You have a new message about your case:\n{url}",
    "case_portal_ready_subject": "AvokatIM — Case accepted, your portal is ready",
    "case_portal_ready_body": (
        "{firm} accepted your case. You now have access to the client portal "
        "with the same email and password:\n{url}"
    ),
    "booking_new_subject": "AvokatIM — New consultation request",
    "booking_new_body": (
        "{citizen} requested a consultation on {when}. Confirm or decline "
        "in Marketplace → Consultations:\n{url}"
    ),
    "booking_confirmed_subject": "AvokatIM — Consultation confirmed",
    "booking_confirmed_body": "{lawyer} confirmed your consultation on {when}.",
    "booking_declined_subject": "AvokatIM — Consultation not confirmed",
    "booking_declined_body": (
        "{lawyer} cannot hold the consultation on {when}. "
        "Pick another slot:\n{url}"
    ),
    "sos_alert_subject": "AvokatIM — SOS: a citizen needs URGENT help",
    "sos_alert_body": (
        "A citizen is asking for urgent help ({city}). You are on SOS duty — "
        "open the Marketplace and take the case as soon as possible:\n{url}"
    ),
    "case_match_subject": "AvokatIM — New case matching your profile",
    "case_match_body": (
        "A case matching your profile was just posted on the Marketplace "
        "({category}, {city}). The first lawyer to claim it wins:\n{url}"
    ),
    "verify_approved_subject": "AvokatIM — Your OAK license is verified",
    "verify_approved_body": (
        "Your bar license was verified successfully. Your profile is now "
        "listed in the public directory and you can claim Marketplace cases:\n{url}"
    ),
    "verify_rejected_subject": "AvokatIM — License verification not approved",
    "verify_rejected_body": (
        "Your bar license verification was not approved. Note: {note}\n"
        "Correct the license number in Settings to resubmit:\n{url}"
    ),
    "platform_invoice_subject": "AvokatIM — Subscription invoice {number}",
    "platform_invoice_body": (
        "Subscription invoice {number} for {period}:\n"
        "{seats} users × {price} € = {amount} €\n"
        "Due date: {due}\n\n"
        "Pay by bank transfer (use the invoice number as reference):\n{bank}\n\n"
        "Details and card payment (when enabled) under Settings → Subscription:\n{url}"
    ),
    "platform_overdue_subject": "AvokatIM — Invoice {number} is overdue",
    "platform_overdue_body": (
        "Subscription invoice {number} ({amount} €) is {days} days overdue. "
        "After {grace} days of delay new Marketplace cases are paused — your "
        "data always stays accessible. Pay under Settings → Subscription:\n{url}"
    ),
    "trial_ending_subject": "AvokatIM — Your free trial ends in {days} days",
    "trial_ending_body": (
        "Your 3-month free trial ends in {days} days. Switch to the paid plan "
        "({price} €/user/month — everything included + unlimited Marketplace "
        "cases) under Settings → Subscription:\n{url}"
    ),
}

_ZH = {
    "reminder_subject": "[AvokatIM] {days} 天后到期：{title}",
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
    # Marketplace (citizens)
    "citizen_verify_subject": "AvokatIM — 确认您的邮箱",
    "citizen_verify_body": "请打开以下链接确认您的邮箱地址：\n{url}\n\n链接有效期为 3 天。",
    "citizen_reset_subject": "AvokatIM — 重置密码",
    "citizen_reset_body": "您请求了密码重置。请打开以下链接设置新密码：\n{url}\n\n链接有效期为 1 小时。如果不是您本人操作，请忽略此邮件。",
    "case_claimed_subject": "AvokatIM — 一位律师接受了您的案件",
    "case_claimed_body": (
        "您的案件已由 {firm} 接手。律师将很快与您联系——您也可以在"
        "“我的案件”中给他们留言：\n{url}"
    ),
    "case_directed_subject": "AvokatIM — 来自公民的新请求",
    "case_directed_body": "一位公民向您发送了请求（{category}，{city}）。请在 AvokatIM 市场中查看：\n{url}",
    "case_message_subject": "AvokatIM — 您的案件有新消息",
    "case_message_body": "您的案件收到新消息：\n{url}",
    "case_portal_ready_subject": "AvokatIM — 案件已受理，您的门户已就绪",
    "case_portal_ready_body": "{firm} 已受理您的案件。您现在可以使用相同的邮箱和密码访问客户门户：\n{url}",
    "booking_new_subject": "AvokatIM — 新的咨询请求",
    "booking_new_body": (
        "{citizen} 请求于 {when} 进行咨询。请在市场 → 咨询中确认或拒绝：\n{url}"
    ),
    "booking_confirmed_subject": "AvokatIM — 咨询已确认",
    "booking_confirmed_body": "{lawyer} 已确认您 {when} 的咨询。",
    "booking_declined_subject": "AvokatIM — 咨询未确认",
    "booking_declined_body": (
        "{lawyer} 无法进行 {when} 的咨询。请选择其他时间：\n{url}"
    ),
    "sos_alert_subject": "AvokatIM — SOS：一位公民需要紧急帮助",
    "sos_alert_body": "一位公民请求紧急帮助（{city}）。您是 SOS 值班律师——请尽快打开市场并接手案件：\n{url}",
    "case_match_subject": "AvokatIM — 有一个与您的资料匹配的新案件",
    "case_match_body": "市场上刚发布了一个与您的资料匹配的案件（{category}，{city}）。先接手的律师获得该案件：\n{url}",
    "verify_approved_subject": "AvokatIM — 您的律师执照已通过验证",
    "verify_approved_body": "您的律师执照已成功验证。您的资料现已列入公开名录，并可以从市场接手案件：\n{url}",
    "verify_rejected_subject": "AvokatIM — 执照验证未通过",
    "verify_rejected_body": "您的律师执照验证未通过。备注：{note}\n请在设置中更正执照号码后重新提交：\n{url}",
    "platform_invoice_subject": "AvokatIM — 订阅发票 {number}",
    "platform_invoice_body": "订阅发票 {number}（账期 {period}）：\n{seats} 位用户 × {price} € = {amount} €\n付款截止日期：{due}\n\n银行转账付款（请以发票号作为备注）：\n{bank}\n\n详情及刷卡支付（如已启用）请见 设置 → 订阅：\n{url}",
    "platform_overdue_subject": "AvokatIM — 发票 {number} 已逾期",
    "platform_overdue_body": "订阅发票 {number}（{amount} €）已逾期 {days} 天。逾期超过 {grace} 天后，将暂停接收市场新案件——您的数据始终可以访问。请在 设置 → 订阅 中付款：\n{url}",
    "trial_ending_subject": "AvokatIM — 免费试用将在 {days} 天后结束",
    "trial_ending_body": "您的 3 个月免费试用将在 {days} 天后结束。请切换到付费方案（{price} €/用户/月——全部功能 + 市场案件不限量），路径：设置 → 订阅：\n{url}",
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
