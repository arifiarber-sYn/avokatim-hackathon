# Marrëveshja për Përpunimin e të Dhënave Personale (LMDhP)

> Model kontrate ndërmjet ofruesit të platformës AvokatIM ("Përpunuesi") dhe
> zyrës së avokatisë kliente ("Kontrolluesi"), në pajtim me **Ligjin
> Nr. 06/L-082 për Mbrojtjen e të Dhënave Personale** të Republikës së Kosovës.
> Plotësohen fushat në kllapa para nënshkrimit. Ky dokument është model pune —
> rekomandohet shqyrtimi nga një jurist para përdorimit me klientë.

**Data:** [____]
**Kontrolluesi:** [Emri i zyrës së avokatisë], me seli në [adresa], NUI [____]
**Përpunuesi:** [Emri i ofruesit të AvokatIM], me seli në [adresa], NUI [____]

## 1. Objekti dhe kohëzgjatja

1.1. Kjo marrëveshje rregullon përpunimin e të dhënave personale që Përpunuesi
kryen në emër të Kontrolluesit gjatë ofrimit të platformës AvokatIM për
menaxhimin e praktikës ligjore ("Shërbimi").

1.2. Marrëveshja vlen sa kohë që Kontrolluesi përdor Shërbimin dhe deri në
fshirjen ose kthimin e plotë të të dhënave sipas nenit 9.

## 2. Natyra dhe qëllimi i përpunimit

2.1. Përpunimi përfshin: ruajtjen, organizimin, strukturimin, kërkimin,
enkriptimin dhe fshirjen e të dhënave, vetëm për qëllim të funksionimit të
Shërbimit (dosjet e lëndëve, kontaktet, afatet, dokumentet, faturimi,
portali i klientit).

2.2. Përpunuesi nuk përpunon të dhënat për asnjë qëllim tjetër dhe nuk i
shfrytëzon ato për trajnim të modeleve të inteligjencës artificiale.

## 3. Kategoritë e të dhënave dhe të subjekteve

3.1. **Subjektet e të dhënave:** klientët e Kontrolluesit, palët kundërshtare,
dëshmitarët, ekspertët, personeli i Kontrolluesit.

3.2. **Kategoritë e të dhënave:** të dhëna identifikuese (emri, numri personal),
të dhëna kontakti, të dhëna financiare (fatura, pagesa), përmbajtja e
dokumenteve ligjore — përfshirë **kategori të veçanta** (p.sh. të dhëna për
procedura penale) që gëzojnë mbrojtje të shtuar sipas nenit 8 të Ligjit 06/L-082.

## 4. Detyrimet e Përpunuesit

4.1. Përpunon të dhënat vetëm me udhëzim të dokumentuar të Kontrolluesit.

4.2. Siguron që personat e autorizuar janë të detyruar me konfidencialitet.

4.3. Zbaton masat teknike dhe organizative të nenit 5 të kësaj marrëveshjeje.

4.4. Ndihmon Kontrolluesin në përgjigjen ndaj kërkesave të subjekteve të të
dhënave (qasje, korrigjim, fshirje, kufizim, bartje).

4.5. Njofton Kontrolluesin **pa vonesë të paarsyeshme, jo më vonë se 48 orë**,
për çdo shkelje të sigurisë së të dhënave personale, me informacionet e
nevojshme për njoftimin e Agjencisë për Informim dhe Privatësi (AIP).

4.6. Vë në dispozicion informacionin e nevojshëm për të dëshmuar pajtueshmërinë
dhe lejon auditime të arsyeshme nga Kontrolluesi.

## 5. Masat e sigurisë

5.1. **Enkriptimi në qetësi:** dokumentet e klientëve ruhen të enkriptuara
(Fernet/AES) në serverin e Shërbimit.

5.2. **Përpunim lokal:** indeksimi semantik i dokumenteve kryhet me modele
lokale; përmbajtja e dokumenteve **nuk largohet nga serveri** për indeksim.

5.3. **Kontrolli i qasjes:** autentikim me fjalëkalim të koduar (bcrypt),
mbështetje për autentikim dyfaktorësh (TOTP), ndarje e plotë e të dhënave
sipas qiramarrësit (tenant), gjurmë auditimi e çdo veprimi.

5.4. **Transporti:** qasja nga rrjeti bëhet vetëm përmes HTTPS/TLS.

5.5. **Kopjet rezervë:** kopje të rregullta të enkriptuara; rikthimi testohet
periodikisht.

## 6. Nënpërpunuesit

6.1. Përpunuesi angazhon nënpërpunues vetëm me autorizim paraprak me shkrim
të Kontrolluesit. Lista aktuale: [plotësohet — p.sh. ofruesi i email-it,
ofruesi i pagesave me kartelë (Stripe), ofruesi i SMS-ve].

6.2. **Asistenti AI:** kur Kontrolluesi e aktivizon asistentin me ofrues të
jashtëm (p.sh. DeepSeek), pjesë të tekstit që avokati zgjedh t'i dërgojë
përpunohen nga ai ofrues. Kontrolluesi informohet në ndërfaqe dhe mund të
zgjedhë modelin lokal që nuk dërgon asgjë jashtë serverit.

## 7. Transferimi ndërkombëtar

7.1. Të dhënat ruhen në [vendndodhja e serverit]. Çdo transferim jashtë
Republikës së Kosovës bëhet vetëm në pajtim me Kapitullin V të Ligjit
06/L-082 (vendime përshtatshmërie ose masa mbrojtëse të përshtatshme).

## 8. Të drejtat e subjekteve të të dhënave

8.1. Kontrolluesi mbetet pika e kontaktit për subjektet e të dhënave.
Përpunuesi i përcjell Kontrolluesit pa vonesë çdo kërkesë që pranon
drejtpërdrejt dhe ofron mjetet teknike (eksport, fshirje, korrigjim)
për përmbushjen e tyre.

## 9. Kthimi dhe fshirja e të dhënave

9.1. Me përfundimin e Shërbimit, Kontrolluesi mund të eksportojë të gjitha të
dhënat e veta (CSV + dokumentet e dekriptuara) përmes funksionit të eksportit.

9.2. Pas [30] ditësh nga përfundimi, Përpunuesi fshin në mënyrë të
pakthyeshme të gjitha të dhënat e Kontrolluesit, përveç kur ruajtja
kërkohet me ligj.

## 10. Përgjegjësia dhe e drejta e zbatueshme

10.1. Palët përgjigjen sipas Ligjit Nr. 06/L-082 dhe legjislacionit në fuqi
të Republikës së Kosovës. Kontestet zgjidhen nga gjykata kompetente në
[qyteti], Republika e Kosovës.

| Për Kontrolluesin | Për Përpunuesin |
|---|---|
| Emri: [____] | Emri: [____] |
| Pozita: [____] | Pozita: [____] |
| Nënshkrimi: ______________ | Nënshkrimi: ______________ |

---

## Aneksi A — Nënpërpunuesit dhe transferimet ndërkombëtare

*Sipas nenit 49 të Ligjit Nr. 06/L-082: transferimi në shtete pa vendim
përshtatshmërie kërkon masa mbrojtëse të përshtatshme ose autorizim nga
Agjencia për Informim dhe Privatësi (AIP). Kontrolluesi duhet ta shqyrtojë
këtë listë dhe, ku kërkohet, të sigurojë autorizimin përkatës përpara
aktivizimit të shërbimit opsional.*

| Nënpërpunuesi | Shërbimi | Të dhënat | Vendndodhja | Statusi |
|---|---|---|---|---|
| DeepSeek (Hangzhou DeepSeek AI) | Asistenti AI i jashtëm (opsional) | Pyetjet e avokatit, fragmente konteksti të zgjedhura | Kinë | **I çaktivizueshëm** te Cilësimet → "AI e jashtme". Alternativa plotësisht e përputhshme: modeli lokal. |
| Stripe, Inc. | Pagesa me kartelë (opsionale) | Emri i klientit, email, shuma e faturës | SHBA/BE | Aktivizohet vetëm me konfigurim; Stripe operon me klauzola kontraktuale standarde. |
| Ofruesi SMTP (p.sh. Google/Gmail) | Dërgimi i emaileve (opsional) | Adresat email, përmbajtja e njoftimeve | SHBA/BE | Sipas konfigurimit të zyrës në `.env`; mund të përdoret ofrues vendor. |
| Ofruesi SMS (Twilio-kompatibël) | Kujtesa SMS (opsionale) | Numri i telefonit, teksti i kujtesës | SHBA/BE | Vetëm me pëlqim të regjistruar të klientit. |
| Cloudflare (nëse përdoret tunel/proxy) | Qasje nga interneti (opsionale) | Trafiku i enkriptuar TLS | Global | Nuk ruan përmbajtje; alternativa: qasje vetëm LAN/VPN. |

**Parimi:** dokumentet e klientëve ruhen të enkriptuara në serverin e zyrës
dhe **kurrë** nuk dërgohen jashtë për indeksim (embeddings lokale). Vetëm
shërbimet opsionale të listuara më lart përfshijnë transferim, dhe secili
mund të çaktivizohet.
