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
    "sms_case_match": "AvokatIM: Rast i ri ({category}, {city}) që përputhet me profilin tënd. Shiko te Tregu: avokatiim.ai/marketplace",
    "sms_sos_alert": "AvokatIM SOS: Rast urgjent ({city})! Hyr menjëherë: avokatiim.ai/marketplace",
    "case_quality_reject": "Përshkrimi nuk duket i mjaftueshëm që një avokat ta kuptojë rastin. Shkruaj çfarë ka ndodhur, kur dhe ku — sa më shumë detaje, aq më shpejt e merr një avokat rastin.",
    # Lawyer onboarding emails
    "lawyer_verify_subject": "AvokatIM — Konfirmo email-in",
    "lawyer_verify_body": (
        "Përshëndetje,\n\nKonfirmo adresën tënde të email-it duke hapur këtë link:\n{url}\n\n"
        "Linku vlen 3 ditë.\n\n— AvokatIM"
    ),
    "lawyer_welcome_subject": "Mirë se erdhe në AvokatIM, {name}!",
    "lawyer_welcome_body": (
        "Zyra jote digjitale është gati. Tri hapa për të nisur:\n\n"
        "1. Aktivizo profilin publik — qytetarët të gjejnë në drejtori dhe merr raste nga tregu:\n{onboarding_url}\n\n"
        "2. Shto numrin e licencës së OAK-së për shenjën e verifikimit — rastet u dërgohen vetëm avokatëve të verifikuar.\n\n"
        "3. Krijo lëndën e parë dhe provo asistenten Ava.\n\n"
        "Prova falas zgjat {trial_days} ditë — pa kartelë, pa detyrime.\n\n"
        "Pyetje? Përgjigjemi te {contact_url}\n\n— Ekipi i AvokatIM"
    ),
    "notary_welcome_subject": "Mirë se erdhe në AvokatIM, {name}!",
    "notary_welcome_body": (
        "Zyra jote noteriale digjitale është gati. Tri hapa për të nisur:\n\n"
        "1. Plotëso profilin e zyrës dhe orarin e termineve:\n{onboarding_url}\n\n"
        "2. Provo asistenten Ava — e njeh Ligjin për Noterinë dhe tarifat zyrtare, "
        "të ndihmon me hartimin e akteve dhe përmbledhjen e dokumenteve.\n\n"
        "3. Krijo lëndën e parë noteriale dhe fto stafin e zyrës.\n\n"
        "Prova falas zgjat {trial_days} ditë — pa kartelë, pa detyrime.\n\n"
        "Pyetje? Përgjigjemi te {contact_url}\n\n— Ekipi i AvokatIM"
    ),
    "lawyer_profile_nudge_subject": "AvokatIM — Profili yt publik ende s'është aktiv",
    "lawyer_profile_nudge_body": (
        "Qytetarët nuk mund të të gjejnë në drejtori dhe nuk merr raste nga tregu.\n\n"
        "Aktivizimi zgjat 2 minuta:\n{url}\n\n— AvokatIM"
    ),
    "citizen_verify_reminder_subject": "AvokatIM — Kujtesë: konfirmo email-in",
    "citizen_verify_reminder_body": (
        "Llogaria jote është gati, por email-i ende s'është konfirmuar — pa të s'mund të postosh raste.\n\n"
        "Konfirmo këtu:\n{url}\n\nLinku vlen 3 ditë.\n\n— AvokatIM"
    ),
    "citizen_case_followup_subject": "AvokatIM — Ende pa e postuar rastin? Ja çfarë mund të bësh falas",
    "citizen_case_followup_body": (
        "Llogaria jote në AvokatIM është gati — por ende s'ke postuar asnjë rast.\n\n"
        "Nëse ke një çështje ligjore, përshkruaje me pak fjalë dhe avokatët e "
        "verifikuar që mbulojnë fushën dhe qytetin tënd të kontaktojnë direkt — falas:\n{post_url}\n\n"
        "Nëse s'je i sigurt a është çështje për avokat, pyete Avën — asistentja "
        "jonë me ligjet e plota të Kosovës të përgjigjet menjëherë, edhe me zë:\n{ava_url}\n\n"
        "Ky është i vetmi email i tillë që marrim — s'të shqetësojmë më.\n\n— AvokatIM"
    ),
    "case_review_request_subject": "AvokatIM — Si shkoi me avokatin? Vlerësimi yt ndihmon të tjerët",
    "case_review_request_body": (
        "Rasti yt në AvokatIM u përmbyll.\n\n"
        "Vlerësimi yt (komunikimi, shpejtësia, qartësia) i ndihmon qytetarët e "
        "tjerë të zgjedhin avokatin e duhur — dhe avokatët e mirë t'i shohin të "
        "gjithë. Merr vetëm 30 sekonda:\n{url}\n\n"
        "Ky është i vetmi email i tillë për këtë rast.\n\n— AvokatIM"
    ),
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
    "citizen_welcome_subject": "Faleminderit, {name} — llogaria jote në AvokatIM është gati!",
    "citizen_welcome_body": (
        "Përshëndetje {name},\n\n"
        "Faleminderit që u bashkove me AvokatIM — llogaria jote u konfirmua "
        "dhe gjithçka është gati.\n\n"
        "Çfarë ke tani, plotësisht falas:\n"
        "• Ava, asistentja ligjore — pyet çfarëdo për ligjin e Kosovës: {ava_url}\n"
        "• Posto rastin tënd dhe avokatët e verifikuar të kontaktojnë: {post_url}\n"
        "• Drejtoria e avokatëve dhe noterëve të verifikuar: {dir_url}\n"
        "• Shkresa e ankesa të gatshme për t'u plotësuar: {docs_url}\n"
        "• SOS për situata urgjente — ndihmë e menjëhershme.\n\n"
        "Për ty si qytetar platforma është dhe do të mbetet falas.\n\n"
        "Me respekt,\nArbër Arifi — AvokatIM"
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
    "verify_approved_subject": "AvokatIM — Urime, {name}! Licenca u verifikua",
    "verify_approved_body": (
        "I/e nderuar {name},\n\n"
        "Licenca juaj u verifikua me sukses — faleminderit që i besuat AvokatIM!\n\n"
        "Nga ky moment profili juaj mban shenjën e verifikimit, shfaqet në "
        "drejtorinë publike dhe qytetarët mund t'ju kontaktojnë direkt. "
        "Avokatët e verifikuar marrin edhe rastet nga Tregu dhe njoftimet SOS.\n\n"
        "🎯 Hapat e ardhshëm (2 minuta):\n"
        "1. Ngarko foton e profilit dhe plotëso biografinë\n"
        "2. Shto specializimet dhe çmimet\n"
        "3. Lidh kalendarin për rezervime automatike\n\n"
        "Profili juaj publik: {url}\n"
        "Cilësimet e profilit: {settings_url}\n\n{founder}"
        "Po ndërtojmë urën mes qytetarëve dhe profesionistëve të drejtësisë në "
        "Kosovë — dhe ju tani jeni pjesë e saj. Për çdo pyetje na shkruani, "
        "përgjigjemi shpejt.\n\n"
        "Me respekt,\nArbër Arifi — AvokatIM"
    ),
    "verify_approved_founder": (
        "Diçka e veçantë: jeni ndër 20 zyrat e para të verifikuara në platformë "
        "dhe mbani përgjithmonë shenjën 'Themelues' — falënderimi ynë për "
        "besimin e hershëm."
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
        "Prova juaj 1-vjeçare falas përfundon për {days} ditë. Kalo në planin "
        "me pagesë ({price} €/përdorues/muaj — gjithçka brenda + raste pa "
        "kufi nga Tregu) te Cilësimet → Abonimi:\n{url}"
    ),
}

_SR = {
    "sms_case_match": "AvokatIM: Novi predmet ({category}, {city}) koji odgovara vašem profilu. Pogledajte: avokatiim.ai/marketplace",
    "sms_sos_alert": "AvokatIM SOS: Hitan slučaj ({city})! Prijavite se odmah: avokatiim.ai/marketplace",
    "case_quality_reject": "Opis ne izgleda dovoljan da advokat razume slučaj. Napišite šta se dogodilo, kada i gde — što više detalja, to će advokat brže preuzeti slučaj.",
    # Lawyer onboarding emails
    "lawyer_verify_subject": "AvokatIM — Potvrdite email",
    "lawyer_verify_body": (
        "Poštovani,\n\nPotvrdite svoju email adresu otvaranjem ovog linka:\n{url}\n\n"
        "Link važi 3 dana.\n\n— AvokatIM"
    ),
    "lawyer_welcome_subject": "Dobro došli u AvokatIM, {name}!",
    "lawyer_welcome_body": (
        "Vaša digitalna kancelarija je spremna. Tri koraka za početak:\n\n"
        "1. Aktivirajte javni profil — građani vas pronalaze u imeniku i dobijate predmete sa tržišta:\n{onboarding_url}\n\n"
        "2. Dodajte broj licence AKK za oznaku verifikacije — predmeti se šalju samo verifikovanim advokatima.\n\n"
        "3. Kreirajte prvi predmet i isprobajte asistentkinju Avu.\n\n"
        "Besplatni probni period traje {trial_days} dana — bez kartice, bez obaveza.\n\n"
        "Pitanja? Odgovaramo na {contact_url}\n\n— Tim AvokatIM"
    ),
    "notary_welcome_subject": "Dobro došli u AvokatIM, {name}!",
    "notary_welcome_body": (
        "Vaša digitalna notarska kancelarija je spremna. Tri koraka za početak:\n\n"
        "1. Popunite profil kancelarije i raspored termina:\n{onboarding_url}\n\n"
        "2. Isprobajte asistentkinju Avu — poznaje Zakon o javnom beležništvu i "
        "zvanične tarife, pomaže u izradi akata i sažimanju dokumenata.\n\n"
        "3. Otvorite prvi predmet i pozovite osoblje kancelarije.\n\n"
        "Besplatan probni period traje {trial_days} dana — bez kartice, bez obaveza.\n\n"
        "Pitanja? Odgovaramo na {contact_url}\n\n— Tim AvokatIM"
    ),
    "lawyer_profile_nudge_subject": "AvokatIM — Vaš javni profil još nije aktivan",
    "lawyer_profile_nudge_body": (
        "Građani ne mogu da vas pronađu u imeniku i ne dobijate predmete sa tržišta.\n\n"
        "Aktivacija traje 2 minuta:\n{url}\n\n— AvokatIM"
    ),
    "citizen_verify_reminder_subject": "AvokatIM — Podsetnik: potvrdite email",
    "citizen_verify_reminder_body": (
        "Vaš nalog je spreman, ali email još nije potvrđen — bez toga ne možete objavljivati predmete.\n\n"
        "Potvrdite ovde:\n{url}\n\nLink važi 3 dana.\n\n— AvokatIM"
    ),
    "citizen_case_followup_subject": "AvokatIM — Još niste objavili predmet? Evo šta možete besplatno",
    "citizen_case_followup_body": (
        "Vaš nalog na AvokatIM je spreman — ali još niste objavili nijedan predmet.\n\n"
        "Ako imate pravno pitanje, opišite ga ukratko i verifikovani advokati koji "
        "pokrivaju vašu oblast i grad će vas kontaktirati direktno — besplatno:\n{post_url}\n\n"
        "Ako niste sigurni da li je to pitanje za advokata, pitajte Avu — naša "
        "asistentkinja sa kompletnim zakonima Kosova odgovara odmah, i glasom:\n{ava_url}\n\n"
        "Ovo je jedini ovakav email — nećemo vas više uznemiravati.\n\n— AvokatIM"
    ),
    "case_review_request_subject": "AvokatIM — Kako je prošlo sa advokatom? Vaša ocena pomaže drugima",
    "case_review_request_body": (
        "Vaš predmet na AvokatIM je zaključen.\n\n"
        "Vaša ocena (komunikacija, brzina, jasnoća) pomaže drugim građanima da "
        "izaberu pravog advokata — a dobrim advokatima da budu vidljivi. "
        "Potrebno je samo 30 sekundi:\n{url}\n\n"
        "Ovo je jedini ovakav email za ovaj predmet.\n\n— AvokatIM"
    ),
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
    "citizen_welcome_subject": "Hvala, {name} — vaš AvokatIM nalog je spreman!",
    "citizen_welcome_body": (
        "Zdravo {name},\n\n"
        "Hvala što ste se pridružili AvokatIM-u — vaš nalog je potvrđen i sve "
        "je spremno.\n\n"
        "Šta sada imate, potpuno besplatno:\n"
        "• Ava, pravna asistentkinja — pitajte bilo šta o zakonu Kosova: {ava_url}\n"
        "• Objavite svoj slučaj i verifikovani advokati vas kontaktiraju: {post_url}\n"
        "• Imenik verifikovanih advokata i notara: {dir_url}\n"
        "• Gotovi podnesci i žalbe za popunjavanje: {docs_url}\n"
        "• SOS za hitne situacije — trenutna pomoć.\n\n"
        "Za vas kao građanina platforma jeste i ostaće besplatna.\n\n"
        "S poštovanjem,\nArbër Arifi — AvokatIM"
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
    "verify_approved_subject": "AvokatIM — Čestitamo, {name}! Licenca je verifikovana",
    "verify_approved_body": (
        "Poštovani/a {name},\n\n"
        "Vaša licenca je uspešno verifikovana — hvala vam na poverenju!\n\n"
        "Od ovog trenutka vaš profil nosi oznaku verifikacije, vidljiv je u "
        "javnom imeniku i građani mogu direktno da vas kontaktiraju. "
        "Verifikovani advokati dobijaju i slučajeve sa Tržišta i SOS "
        "obaveštenja.\n\n"
        "Vaš profil: {url}\n"
        "Podešavanja profila: {settings_url}\n\n{founder}"
        "Gradimo most između građana i pravnih profesionalaca na Kosovu — i vi "
        "ste sada deo toga. Za svako pitanje pišite nam, odgovaramo brzo.\n\n"
        "S poštovanjem,\nArbër Arifi — AvokatIM"
    ),
    "verify_approved_founder": (
        "Nešto posebno: među prvih ste 20 verifikovanih kancelarija na "
        "platformi i zauvek nosite oznaku 'Osnivač' — naša zahvalnost za rano "
        "ukazano poverenje."
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
        "Vaša besplatna proba od godinu dana ističe za {days} dana. Pređite na "
        "plaćeni plan ({price} €/korisnik/mesečno — sve uključeno + neograničeni "
        "slučajevi sa Tržišta) u Podešavanja → Pretplata:\n{url}"
    ),
}

_TR = {
    "sms_case_match": "AvokatIM: Profilinize uyan yeni dosya ({category}, {city}). Görüntüleyin: avokatiim.ai/marketplace",
    "sms_sos_alert": "AvokatIM SOS: Acil dosya ({city})! Hemen giriş yapın: avokatiim.ai/marketplace",
    "case_quality_reject": "Açıklama, bir avukatın davayı anlaması için yeterli görünmüyor. Ne olduğunu, ne zaman ve nerede olduğunu yazın — ne kadar çok ayrıntı, o kadar hızlı bir avukat davayı üstlenir.",
    # Lawyer onboarding emails
    "lawyer_verify_subject": "AvokatIM — E-postanızı doğrulayın",
    "lawyer_verify_body": (
        "Merhaba,\n\nBu bağlantıyı açarak e-posta adresinizi doğrulayın:\n{url}\n\n"
        "Bağlantı 3 gün geçerlidir.\n\n— AvokatIM"
    ),
    "lawyer_welcome_subject": "AvokatIM'e hoş geldiniz, {name}!",
    "lawyer_welcome_body": (
        "Dijital ofisiniz hazır. Başlamak için üç adım:\n\n"
        "1. Herkese açık profilinizi etkinleştirin — vatandaşlar sizi rehberde bulur ve pazar yerinden dosyalar alırsınız:\n{onboarding_url}\n\n"
        "2. Doğrulama rozeti için KBB lisans numaranızı ekleyin — dosyalar yalnızca doğrulanmış avukatlara gönderilir.\n\n"
        "3. İlk dosyanızı oluşturun ve asistan Ava'yı deneyin.\n\n"
        "Ücretsiz deneme {trial_days} gün sürer — kart yok, taahhüt yok.\n\n"
        "Sorular? {contact_url} adresinden yanıtlıyoruz\n\n— AvokatIM Ekibi"
    ),
    "notary_welcome_subject": "AvokatIM'e hoş geldiniz, {name}!",
    "notary_welcome_body": (
        "Dijital noterlik ofisiniz hazır. Başlamak için üç adım:\n\n"
        "1. Ofis profilini ve randevu takvimini doldurun:\n{onboarding_url}\n\n"
        "2. Asistan Ava'yı deneyin — Noterlik Kanunu'nu ve resmi tarifeleri bilir, "
        "senet hazırlamada ve belge özetlemede yardımcı olur.\n\n"
        "3. İlk noterlik dosyanızı açın ve ofis personelini davet edin.\n\n"
        "Ücretsiz deneme {trial_days} gün sürer — kart yok, taahhüt yok.\n\n"
        "Sorular? {contact_url} adresinden yanıtlıyoruz\n\n— AvokatIM Ekibi"
    ),
    "lawyer_profile_nudge_subject": "AvokatIM — Herkese açık profiliniz hâlâ etkin değil",
    "lawyer_profile_nudge_body": (
        "Vatandaşlar sizi rehberde bulamıyor ve pazar yerinden dosya almıyorsunuz.\n\n"
        "Etkinleştirme 2 dakika sürer:\n{url}\n\n— AvokatIM"
    ),
    "citizen_verify_reminder_subject": "AvokatIM — Hatırlatma: e-postanızı doğrulayın",
    "citizen_verify_reminder_body": (
        "Hesabınız hazır, ancak e-postanız henüz doğrulanmadı — doğrulamadan dosya yayınlayamazsınız.\n\n"
        "Buradan doğrulayın:\n{url}\n\nBağlantı 3 gün geçerlidir.\n\n— AvokatIM"
    ),
    "citizen_case_followup_subject": "AvokatIM — Henüz dosya yayınlamadınız mı? Ücretsiz yapabilecekleriniz",
    "citizen_case_followup_body": (
        "AvokatIM hesabınız hazır — ancak henüz bir dosya yayınlamadınız.\n\n"
        "Hukuki bir sorununuz varsa, kısaca anlatın; alanınızı ve şehrinizi kapsayan "
        "doğrulanmış avukatlar sizinle doğrudan iletişime geçer — ücretsiz:\n{post_url}\n\n"
        "Avukatlık bir konu olup olmadığından emin değilseniz Ava'ya sorun — Kosova'nın "
        "tüm yasalarını bilen asistanımız anında yanıtlar, sesli de:\n{ava_url}\n\n"
        "Bu türden tek e-postadır — sizi bir daha rahatsız etmeyeceğiz.\n\n— AvokatIM"
    ),
    "case_review_request_subject": "AvokatIM — Avukatla nasıl geçti? Değerlendirmeniz başkalarına yardımcı olur",
    "case_review_request_body": (
        "AvokatIM'deki dosyanız sonuçlandı.\n\n"
        "Değerlendirmeniz (iletişim, hız, açıklık) diğer vatandaşların doğru "
        "avukatı seçmesine — iyi avukatların da görünür olmasına yardımcı olur. "
        "Sadece 30 saniye sürer:\n{url}\n\n"
        "Bu dosya için bu türden tek e-postadır.\n\n— AvokatIM"
    ),
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
    "citizen_welcome_subject": "Teşekkürler, {name} — AvokatIM hesabınız hazır!",
    "citizen_welcome_body": (
        "Merhaba {name},\n\n"
        "AvokatIM'e katıldığınız için teşekkürler — hesabınız doğrulandı ve "
        "her şey hazır.\n\n"
        "Artık tamamen ücretsiz olarak sahip olduklarınız:\n"
        "• Hukuk asistanı Ava — Kosova hukuku hakkında her şeyi sorun: {ava_url}\n"
        "• Davanızı yayınlayın, doğrulanmış avukatlar sizinle iletişime geçsin: {post_url}\n"
        "• Doğrulanmış avukat ve noter rehberi: {dir_url}\n"
        "• Doldurulmaya hazır dilekçe ve itirazlar: {docs_url}\n"
        "• Acil durumlar için SOS — anında yardım.\n\n"
        "Vatandaş olarak sizin için platform ücretsizdir ve öyle kalacaktır.\n\n"
        "Saygılarımızla,\nArbër Arifi — AvokatIM"
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
    "verify_approved_subject": "AvokatIM — Tebrikler, {name}! Lisansınız doğrulandı",
    "verify_approved_body": (
        "Sayın {name},\n\n"
        "Lisansınız başarıyla doğrulandı — güveniniz için teşekkür ederiz!\n\n"
        "Şu andan itibaren profiliniz doğrulama işareti taşıyor, kamu "
        "rehberinde görünüyor ve vatandaşlar sizinle doğrudan iletişim "
        "kurabilir. Doğrulanmış avukatlar Pazar'dan davalar ve SOS "
        "bildirimleri de alır.\n\n"
        "Profiliniz: {url}\n"
        "Profil ayarları: {settings_url}\n\n{founder}"
        "Kosova'da vatandaşlar ile hukuk profesyonelleri arasında bir köprü "
        "kuruyoruz — ve artık siz de bunun bir parçasısınız. Her sorunuz için "
        "bize yazın, hızla yanıtlıyoruz.\n\n"
        "Saygılarımızla,\nArbër Arifi — AvokatIM"
    ),
    "verify_approved_founder": (
        "Özel bir not: platformda doğrulanan ilk 20 ofis arasındasınız ve "
        "'Kurucu' rozetini kalıcı olarak taşıyorsunuz — erken güveniniz için "
        "teşekkürlerimiz."
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
        "1 yıllık ücretsiz denemeniz {days} gün içinde bitiyor. Ücretli plana "
        "geçin ({price} €/kullanıcı/ay — her şey dahil + Pazar'dan sınırsız "
        "dava) Ayarlar → Abonelik:\n{url}"
    ),
}

_BS = {
    "sms_case_match": "AvokatIM: Novi predmet ({category}, {city}) koji odgovara vašem profilu. Pogledajte: avokatiim.ai/marketplace",
    "sms_sos_alert": "AvokatIM SOS: Hitan slučaj ({city})! Prijavite se odmah: avokatiim.ai/marketplace",
    "case_quality_reject": "Opis ne izgleda dovoljan da advokat razumije slučaj. Napišite šta se dogodilo, kada i gdje — što više detalja, to će advokat brže preuzeti slučaj.",
    # Lawyer onboarding emails
    "lawyer_verify_subject": "AvokatIM — Potvrdite email",
    "lawyer_verify_body": (
        "Poštovani,\n\nPotvrdite svoju email adresu otvaranjem ovog linka:\n{url}\n\n"
        "Link vrijedi 3 dana.\n\n— AvokatIM"
    ),
    "lawyer_welcome_subject": "Dobro došli u AvokatIM, {name}!",
    "lawyer_welcome_body": (
        "Vaš digitalni ured je spreman. Tri koraka za početak:\n\n"
        "1. Aktivirajte javni profil — građani vas pronalaze u imeniku i dobijate predmete s tržišta:\n{onboarding_url}\n\n"
        "2. Dodajte broj licence AKK za oznaku verifikacije — predmeti se šalju samo verificiranim advokatima.\n\n"
        "3. Kreirajte prvi predmet i isprobajte asistenticu Avu.\n\n"
        "Besplatni probni period traje {trial_days} dana — bez kartice, bez obaveza.\n\n"
        "Pitanja? Odgovaramo na {contact_url}\n\n— Tim AvokatIM"
    ),
    "notary_welcome_subject": "Dobro došli u AvokatIM, {name}!",
    "notary_welcome_body": (
        "Vaša digitalna notarska kancelarija je spremna. Tri koraka za početak:\n\n"
        "1. Popunite profil kancelarije i raspored termina:\n{onboarding_url}\n\n"
        "2. Isprobajte asistenticu Avu — poznaje Zakon o notarima i zvanične "
        "tarife, pomaže u izradi akata i sažimanju dokumenata.\n\n"
        "3. Otvorite prvi predmet i pozovite osoblje kancelarije.\n\n"
        "Besplatni probni period traje {trial_days} dana — bez kartice, bez obaveza.\n\n"
        "Pitanja? Odgovaramo na {contact_url}\n\n— Tim AvokatIM"
    ),
    "lawyer_profile_nudge_subject": "AvokatIM — Vaš javni profil još nije aktivan",
    "lawyer_profile_nudge_body": (
        "Građani vas ne mogu pronaći u imeniku i ne dobijate predmete s tržišta.\n\n"
        "Aktivacija traje 2 minute:\n{url}\n\n— AvokatIM"
    ),
    "citizen_verify_reminder_subject": "AvokatIM — Podsjetnik: potvrdite email",
    "citizen_verify_reminder_body": (
        "Vaš račun je spreman, ali email još nije potvrđen — bez toga ne možete objavljivati predmete.\n\n"
        "Potvrdite ovdje:\n{url}\n\nLink vrijedi 3 dana.\n\n— AvokatIM"
    ),
    "citizen_case_followup_subject": "AvokatIM — Još niste objavili predmet? Evo šta možete besplatno",
    "citizen_case_followup_body": (
        "Vaš račun na AvokatIM je spreman — ali još niste objavili nijedan predmet.\n\n"
        "Ako imate pravno pitanje, opišite ga ukratko i verificirani advokati koji "
        "pokrivaju vašu oblast i grad će vas kontaktirati direktno — besplatno:\n{post_url}\n\n"
        "Ako niste sigurni je li to pitanje za advokata, pitajte Avu — naša "
        "asistentica s kompletnim zakonima Kosova odgovara odmah, i glasom:\n{ava_url}\n\n"
        "Ovo je jedini ovakav email — nećemo vas više uznemiravati.\n\n— AvokatIM"
    ),
    "case_review_request_subject": "AvokatIM — Kako je prošlo s advokatom? Vaša ocjena pomaže drugima",
    "case_review_request_body": (
        "Vaš predmet na AvokatIM je zaključen.\n\n"
        "Vaša ocjena (komunikacija, brzina, jasnoća) pomaže drugim građanima da "
        "izaberu pravog advokata — a dobrim advokatima da budu vidljivi. "
        "Potrebno je samo 30 sekundi:\n{url}\n\n"
        "Ovo je jedini ovakav email za ovaj predmet.\n\n— AvokatIM"
    ),
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
    "citizen_welcome_subject": "Hvala, {name} — vaš AvokatIM nalog je spreman!",
    "citizen_welcome_body": (
        "Zdravo {name},\n\n"
        "Hvala što ste se pridružili AvokatIM-u — vaš nalog je potvrđen i sve "
        "je spremno.\n\n"
        "Šta sada imate, potpuno besplatno:\n"
        "• Ava, pravna asistentica — pitajte bilo šta o zakonu Kosova: {ava_url}\n"
        "• Objavite svoj slučaj i verificirani advokati vas kontaktiraju: {post_url}\n"
        "• Imenik verificiranih advokata i notara: {dir_url}\n"
        "• Gotovi podnesci i žalbe za popunjavanje: {docs_url}\n"
        "• SOS za hitne situacije — trenutna pomoć.\n\n"
        "Za vas kao građanina platforma jeste i ostat će besplatna.\n\n"
        "S poštovanjem,\nArbër Arifi — AvokatIM"
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
    "verify_approved_subject": "AvokatIM — Čestitamo, {name}! Licenca je verificirana",
    "verify_approved_body": (
        "Poštovani/a {name},\n\n"
        "Vaša licenca je uspješno verificirana — hvala vam na povjerenju!\n\n"
        "Od ovog trenutka vaš profil nosi oznaku verifikacije, vidljiv je u "
        "javnom imeniku i građani mogu direktno da vas kontaktiraju. "
        "Verificirani advokati dobijaju i slučajeve s Tržišta i SOS "
        "obavještenja.\n\n"
        "Vaš profil: {url}\n"
        "Podešavanja profila: {settings_url}\n\n{founder}"
        "Gradimo most između građana i pravnih profesionalaca na Kosovu — i vi "
        "ste sada dio toga. Za svako pitanje pišite nam, odgovaramo brzo.\n\n"
        "S poštovanjem,\nArbër Arifi — AvokatIM"
    ),
    "verify_approved_founder": (
        "Nešto posebno: među prvih ste 20 verificiranih kancelarija na "
        "platformi i zauvijek nosite oznaku 'Osnivač' — naša zahvalnost za "
        "rano ukazano povjerenje."
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
        "Vaša besplatna proba od godinu dana ističe za {days} dana. Pređite na "
        "plaćeni plan ({price} €/korisnik/mjesečno — sve uključeno + neograničeni "
        "slučajevi s Tržišta) u Postavke → Pretplata:\n{url}"
    ),
}

_EN = {
    "sms_case_match": "AvokatIM: New case ({category}, {city}) matching your profile. View it: avokatiim.ai/marketplace",
    "sms_sos_alert": "AvokatIM SOS: Urgent case ({city})! Log in now: avokatiim.ai/marketplace",
    "case_quality_reject": "The description doesn't look sufficient for a lawyer to understand the case. Write what happened, when and where — the more detail, the faster a lawyer takes the case.",
    # Lawyer onboarding emails
    "lawyer_verify_subject": "AvokatIM — Confirm your email",
    "lawyer_verify_body": (
        "Hello,\n\nConfirm your email address by opening this link:\n{url}\n\n"
        "The link is valid for 3 days.\n\n— AvokatIM"
    ),
    "lawyer_welcome_subject": "Welcome to AvokatIM, {name}!",
    "lawyer_welcome_body": (
        "Your digital office is ready. Three steps to get started:\n\n"
        "1. Activate your public profile — citizens find you in the directory and you receive cases from the marketplace:\n{onboarding_url}\n\n"
        "2. Add your KBA license number for the verification badge — cases are sent only to verified lawyers.\n\n"
        "3. Create your first matter and try the Ava assistant.\n\n"
        "The free trial lasts {trial_days} days — no card, no commitment.\n\n"
        "Questions? We answer at {contact_url}\n\n— The AvokatIM Team"
    ),
    "notary_welcome_subject": "Welcome to AvokatIM, {name}!",
    "notary_welcome_body": (
        "Your digital notary office is ready. Three steps to get started:\n\n"
        "1. Complete your office profile and appointment schedule:\n{onboarding_url}\n\n"
        "2. Try the assistant Ava — she knows the Law on Notary and the official "
        "tariffs, and helps with drafting acts and summarizing documents.\n\n"
        "3. Open your first notarial matter and invite your office staff.\n\n"
        "The free trial lasts {trial_days} days — no card, no obligations.\n\n"
        "Questions? We answer at {contact_url}\n\n— The AvokatIM team"
    ),
    "lawyer_profile_nudge_subject": "AvokatIM — Your public profile is still not active",
    "lawyer_profile_nudge_body": (
        "Citizens cannot find you in the directory and you receive no cases from the marketplace.\n\n"
        "Activation takes 2 minutes:\n{url}\n\n— AvokatIM"
    ),
    "citizen_verify_reminder_subject": "AvokatIM — Reminder: confirm your email",
    "citizen_verify_reminder_body": (
        "Your account is ready, but your email is not yet confirmed — without it you cannot post cases.\n\n"
        "Confirm here:\n{url}\n\nThe link is valid for 3 days.\n\n— AvokatIM"
    ),
    "citizen_case_followup_subject": "AvokatIM — Haven't posted your case yet? Here's what you can do for free",
    "citizen_case_followup_body": (
        "Your AvokatIM account is ready — but you haven't posted a case yet.\n\n"
        "If you have a legal issue, describe it briefly and verified lawyers covering "
        "your area and city will contact you directly — free of charge:\n{post_url}\n\n"
        "Not sure whether it's a matter for a lawyer? Ask Ava — our assistant with "
        "the complete laws of Kosovo answers instantly, by voice too:\n{ava_url}\n\n"
        "This is the only email of its kind — we won't bother you again.\n\n— AvokatIM"
    ),
    "case_review_request_subject": "AvokatIM — How did it go with your lawyer? Your rating helps others",
    "case_review_request_body": (
        "Your case on AvokatIM has concluded.\n\n"
        "Your rating (communication, speed, clarity) helps other citizens pick "
        "the right lawyer — and helps good lawyers get seen. It takes just 30 "
        "seconds:\n{url}\n\n"
        "This is the only email of its kind for this case.\n\n— AvokatIM"
    ),
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
    "citizen_welcome_subject": "Thank you, {name} — your AvokatIM account is ready!",
    "citizen_welcome_body": (
        "Hello {name},\n\n"
        "Thank you for joining AvokatIM — your account is confirmed and "
        "everything is ready.\n\n"
        "What you now have, completely free:\n"
        "• Ava, the legal assistant — ask anything about Kosovo law: {ava_url}\n"
        "• Post your case and verified lawyers contact you: {post_url}\n"
        "• Directory of verified lawyers and notaries: {dir_url}\n"
        "• Ready-to-fill letters and complaints: {docs_url}\n"
        "• SOS for urgent situations — immediate help.\n\n"
        "For you as a citizen the platform is and will remain free.\n\n"
        "Respectfully,\nArbër Arifi — AvokatIM"
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
    "verify_approved_subject": "AvokatIM — Congratulations, {name}! Your license is verified",
    "verify_approved_body": (
        "Dear {name},\n\n"
        "Your license was verified successfully — thank you for trusting "
        "AvokatIM!\n\n"
        "From this moment your profile carries the verification badge, appears "
        "in the public directory and citizens can contact you directly. "
        "Verified lawyers also receive Marketplace cases and SOS alerts.\n\n"
        "Your profile: {url}\n"
        "Profile settings: {settings_url}\n\n{founder}"
        "We are building the bridge between citizens and legal professionals "
        "in Kosovo — and you are now part of it. Write to us with any "
        "question, we reply fast.\n\n"
        "Respectfully,\nArbër Arifi — AvokatIM"
    ),
    "verify_approved_founder": (
        "Something special: you are among the first 20 verified offices on the "
        "platform and keep the 'Founder' badge forever — our thanks for your "
        "early trust."
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
        "Your one-year free trial ends in {days} days. Switch to the paid plan "
        "({price} €/user/month — everything included + unlimited Marketplace "
        "cases) under Settings → Subscription:\n{url}"
    ),
}

_ZH = {
    "sms_case_match": "AvokatIM：有与您资料匹配的新案件（{category}，{city}）。查看：avokatiim.ai/marketplace",
    "sms_sos_alert": "AvokatIM SOS：紧急案件（{city}）！立即登录：avokatiim.ai/marketplace",
    "case_quality_reject": "描述似乎不足以让律师理解案件。请写明发生了什么、何时、何地——细节越多，律师接案越快。",
    # Lawyer onboarding emails
    "lawyer_verify_subject": "AvokatIM — 确认您的电子邮箱",
    "lawyer_verify_body": "您好，\n\n请打开此链接确认您的电子邮箱地址：\n{url}\n\n链接有效期为3天。\n\n— AvokatIM",
    "lawyer_welcome_subject": "欢迎来到 AvokatIM，{name}！",
    "lawyer_welcome_body": (
        "您的数字律所已就绪。三步开始：\n\n"
        "1. 激活公开资料——公民可以在目录中找到您，您也能从市场接收案件：\n{onboarding_url}\n\n"
        "2. 添加科索沃律师协会执照号码以获得验证徽章——案件仅发送给已验证的律师。\n\n"
        "3. 创建第一个案件并试用助手 Ava。\n\n"
        "免费试用期为 {trial_days} 天——无需银行卡，无任何承诺。\n\n"
        "有问题？请访问 {contact_url}\n\n— AvokatIM 团队"
    ),
    "notary_welcome_subject": "欢迎来到 AvokatIM，{name}！",
    "notary_welcome_body": (
        "您的数字公证处已就绪。三步开始使用：\n\n"
        "1. 完善公证处资料和预约时间表：\n{onboarding_url}\n\n"
        "2. 试用助手 Ava——她熟悉《公证法》和官方收费标准，可协助起草公证文书和总结文件。\n\n"
        "3. 创建第一个公证案卷并邀请公证处工作人员。\n\n"
        "免费试用期为 {trial_days} 天——无需银行卡，无任何义务。\n\n"
        "有问题？请访问 {contact_url}\n\n— AvokatIM 团队"
    ),
    "lawyer_profile_nudge_subject": "AvokatIM — 您的公开资料尚未激活",
    "lawyer_profile_nudge_body": "公民无法在目录中找到您，您也无法从市场接收案件。\n\n激活只需2分钟：\n{url}\n\n— AvokatIM",
    "citizen_verify_reminder_subject": "AvokatIM — 提醒：确认您的电子邮箱",
    "citizen_verify_reminder_body": "您的账户已就绪，但电子邮箱尚未确认——未确认前无法发布案件。\n\n请在此确认：\n{url}\n\n链接有效期为3天。\n\n— AvokatIM",
    "citizen_case_followup_subject": "AvokatIM — 还没有发布案件？这些服务全部免费",
    "citizen_case_followup_body": "您的 AvokatIM 账户已就绪——但您还没有发布任何案件。\n\n如果您有法律问题，请简要描述，覆盖您所在领域和城市的认证律师会直接联系您——完全免费：\n{post_url}\n\n不确定是否需要律师？问问 Ava——我们掌握科索沃全部法律的助手会立即回答，还支持语音：\n{ava_url}\n\n这是唯一一封此类邮件——我们不会再打扰您。\n\n— AvokatIM",
    "case_review_request_subject": "AvokatIM — 与律师合作得如何？您的评价能帮助他人",
    "case_review_request_body": "您在 AvokatIM 上的案件已结束。\n\n您的评价（沟通、速度、清晰度）能帮助其他公民选择合适的律师，也能让优秀的律师被更多人看到。只需30秒：\n{url}\n\n针对此案件，这是唯一一封此类邮件。\n\n— AvokatIM",
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
    "citizen_welcome_subject": "谢谢您，{name} — 您的 AvokatIM 账户已就绪！",
    "citizen_welcome_body": (
        "您好，{name}：\n\n"
        "感谢您加入 AvokatIM——您的账户已确认，一切就绪。\n\n"
        "您现在可以完全免费使用：\n"
        "• 法律助手 Ava——咨询任何科索沃法律问题：{ava_url}\n"
        "• 发布您的案件，经过验证的律师会与您联系：{post_url}\n"
        "• 经过验证的律师和公证人名录：{dir_url}\n"
        "• 可直接填写的申请书和投诉书：{docs_url}\n"
        "• 紧急情况 SOS——即时帮助。\n\n"
        "对公民而言，本平台现在免费，将来也保持免费。\n\n"
        "此致，\nArbër Arifi — AvokatIM"
    ),
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
    "verify_approved_subject": "AvokatIM — 恭喜，{name}！您的执照已通过验证",
    "verify_approved_body": (
        "尊敬的{name}：\n\n"
        "您的执照已成功通过验证——感谢您对 AvokatIM 的信任！\n\n"
        "从现在起，您的资料带有验证标志，显示在公开名录中，公民可以直接联系您。"
        "经过验证的律师还会收到市场案件和 SOS 通知。\n\n"
        "您的资料：{url}\n"
        "资料设置：{settings_url}\n\n{founder}"
        "我们正在科索沃搭建公民与法律专业人士之间的桥梁——您现在是其中的一员。"
        "有任何问题请写信给我们，我们会尽快回复。\n\n"
        "此致，\nArbër Arifi — AvokatIM"
    ),
    "verify_approved_founder": (
        "特别之处：您是平台上最早通过验证的 20 家事务所之一，"
        "将永久保留“创始人”徽章——感谢您的早期信任。"
    ),
    "verify_rejected_subject": "AvokatIM — 执照验证未通过",
    "verify_rejected_body": "您的律师执照验证未通过。备注：{note}\n请在设置中更正执照号码后重新提交：\n{url}",
    "platform_invoice_subject": "AvokatIM — 订阅发票 {number}",
    "platform_invoice_body": "订阅发票 {number}（账期 {period}）：\n{seats} 位用户 × {price} € = {amount} €\n付款截止日期：{due}\n\n银行转账付款（请以发票号作为备注）：\n{bank}\n\n详情及刷卡支付（如已启用）请见 设置 → 订阅：\n{url}",
    "platform_overdue_subject": "AvokatIM — 发票 {number} 已逾期",
    "platform_overdue_body": "订阅发票 {number}（{amount} €）已逾期 {days} 天。逾期超过 {grace} 天后，将暂停接收市场新案件——您的数据始终可以访问。请在 设置 → 订阅 中付款：\n{url}",
    "trial_ending_subject": "AvokatIM — 免费试用将在 {days} 天后结束",
    "trial_ending_body": "您的 1 年免费试用将在 {days} 天后结束。请切换到付费方案（{price} €/用户/月——全部功能 + 市场案件不限量），路径：设置 → 订阅：\n{url}",
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
