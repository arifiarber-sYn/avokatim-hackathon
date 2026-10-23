# Hulumtimi i blerësve gjermanë — kujt i kryen punë softueri ynë së pari

> Dosje interne (shqip). Përditësuar: 2026-08-05. Baza për
> `data/de_companies.csv` dhe fushatën me PO/JO (`de_company_outreach.py`).
> Të dhënat u verifikuan me kërkim web; kontaktet konfirmohen sërish para
> çdo dërgimi (gate PO/JO te Halim).

## Korrigjimi kyç i strategjisë (nga hulumtimi)

Supozimi i mëparshëm ishte "AI-ja jonë (anonimizim lokal + verifikim citimesh
+ agjentë) është unike në DE". Hulumtimi e përgënjeshtron pjesërisht:

- **RA-MICRO** ka tashmë "JURA KI-Assistent": anonimizim lokal para dërgimit
  te ChatGPT/Gemini/Mistral **dhe verifikim automatik i normave e vendimeve**
  të cituara — pikërisht ajo që ne e shisnim si e jona.
- **Wolters Kluwer** (AnNoText/Kleos "Expert AI") ka anonimizim, agjentë dhe
  hulumtim të integruar në softuer, ISO 27001, roadshow në 8 qytete më 2026.

Prandaj argumenti "AI unike" NUK vlen ndaj dy liderëve. Diferencuesit tanë
realë, që askush prej tyre s'i ka të plotë, janë:

1. **Akuizicioni i mandateve 24/7** — recepsion me zë, telefon dhe WhatsApp
   që krijon fallanfrage strukturuar pa staf; portal qytetari + marketplace.
2. **LLM plotësisht lokale** (opsion offline i vërtetë, jo vetëm anonimizim
   para një API të jashtme).
3. **Një kod, shumë juridiksione** (XK+DE sot; AT/CH = konfigurim + korpus).

Kjo e ndryshon renditjen: blerësit më të mirë NUK janë liderët me AI, por
(a) siguruesit e mbrojtjes juridike që jetojnë nga intake-u dhe rrjeti i
avokatëve, dhe (b) vendorët pa shtresë AI. Konsoliduesit mbeten relevantë
për shkallë/blerje, jo për "boshllëkun AI".

## Kriteret e pikëzimit (1–5, sa më lart aq më mirë; rreziku zbritet)

- **boshllëku** — sa e mbush produkti ynë një mungesë reale te ta.
- **blerjet** — a është blerja pjesë e sjelljes së tyre.
- **financat** — kapaciteti për të paguar.
- **shpejtësia** — sa shpejt vendosin (startup/privat > korporatë e madhe).
- **rreziku i kopjimit** (zbritet) — a mund ta kopjojnë në vend që ta blejnë.

## VALA 1 — nis i pari (fit-i më i lartë)

### 1. ADVOCARD (Generali Deutschland) — sigurues mbrojtjeje juridike
- **Kush**: Hamburg, pjesë e Generali (grupi i dytë më i madh i sigurimeve
  në DE). Vorstand: Roland Stoffels (kryesues). Përdor "Legal Techs" si
  ofrues shërbimi dhe rrjet avokatësh me termine të preferuara.
- **Pse i kryen punë**: modeli i tyre është pikërisht lidhja qytetar↔avokat
  me intake dixhital 24/7 — thelbi i platformës sonë. Opsioni OEM (shtresa
  AI + intake me zë/WhatsApp/telefon) hyn direkt në produktin e tyre.
- **Oferta hapëse**: Opsioni 1 (OEM) ose 2 (white-label për segmentin B2C).
- **Kontakt**: nachricht@advocard.de · gjuha: gjermanisht.
- **Pikët**: boshllëk 5 · blerje 4 · financa 5 · shpejtësi 3 · kopjim −2 → **15**

### 2. ROLAND Rechtsschutz — sigurues mbrojtjeje juridike
- **Kush**: Köln, i pavarur. service@roland-rechtsschutz.de. Model me
  **rrjet partner-kanzleien** (jo juristë in-house) + telefon 24/7.
- **Pse i kryen punë**: meqë mbështeten te avokatët e jashtëm, marketplace-i
  ynë + intake-u strukturuar + caktimi i termineve u shkon më mirë se
  kujtdo; s'kanë intake me zë/WhatsApp.
- **Oferta hapëse**: Opsioni 1 (OEM intake+AI) → mundësisht 2.
- **Kontakt**: service@roland-rechtsschutz.de (fillestar) · gjermanisht.
- **Pikët**: boshllëk 5 · blerje 3 · financa 4 · shpejtësi 4 · kopjim −2 → **14**

### 3. Haufe / Advolux — vendor Kanzleisoftware pa shtresë AI
- **Kush**: Advolux nga Haufe Group (Freiburg). beA i integruar, RVG,
  Mahnwesen, cloud/on-prem. Për AI flasin vetëm si "qeverisje e Schatten-KI",
  **pa asistent AI produkt**.
- **Pse i kryen punë**: u mungon pikërisht shtresa jonë AI + intake 24/7;
  Haufe ka para dhe motiv të mos mbetet pas WK/RA-MICRO.
- **Oferta hapëse**: Opsioni 1 (OEM AI mbi Advolux) ose 3 (blerje DACH).
- **Kontakt**: përmes formularit/kontaktit të Haufe (jo support-i i produktit);
  verifiko personin e duhur para dërgimit · gjermanisht.
- **Pikët**: boshllëk 5 · blerje 3 · financa 4 · shpejtësi 3 · kopjim −2 → **13**

### 4. Septeo (pronare e stp.one/Advoware) — konsolidues
- **Kush**: grup francez; përfundoi blerjen e stp.one (shkurt 2026, vlerësim
  ~560 mln €, ~3,600 punonjës). Blerja është motori i tyre i rritjes.
- **Pse i kryen punë**: playbook-u i tyre është blerja; ne u japim hyrje AI
  + akuizicion mandatesh + juridiksion të dytë (XK) me një kod.
- **Oferta hapëse**: Opsioni 3 ose 4 (blerje); fallback 1.
- **Kontakt**: Corporate Development/M&A i Septeo + Geschäftsführung stp.one
  (Karlsruhe) · gjuha: anglisht.
- **Pikët**: boshllëk 3 · blerje 5 · financa 5 · shpejtësi 3 · kopjim −2 → **14**

### 5. ARAG SE — sigurues mbrojtjeje juridike (i madh, ndërkombëtar)
- **Kush**: Düsseldorf, siguruesi më i madh i pavarur i mbrojtjes juridike.
  Vorstand: Dr. Renko Dirksen. Ka JuraTel/JuraCheck (telefon+online 24/7 me
  **juristë in-house**) dhe raportim dixhital.
- **Pse i kryen punë**: intake-u ynë me zë/WhatsApp + verifikimi i citimeve
  automatizon atë që sot e mbajnë me 45+ juristë; por meqë kanë in-house,
  boshllëku është më i vogël se te ROLAND/ADVOCARD.
- **Oferta hapëse**: Opsioni 1 (OEM).
- **Kontakt**: vetëm Kontaktformular publik → duhet gjetur kontakti i
  inovacionit para dërgimit · gjermanisht.
- **Pikët**: boshllëk 4 · blerje 3 · financa 5 · shpejtësi 2 · kopjim −2 → **12**

## VALA 2 — pas përgjigjeve/heshtjes së Valës 1

### 6. Wolters Kluwer Legal Software — konsolidues me AI ekzistuese
- **Kush**: AnNoText/Kleos me Expert AI (anonimizim, agjentë, hulumtim).
  Kontakte publike: Joachim Hofacker, Christian Utikal (LinkedIn).
- **Pse (me kujdes)**: kanë tashmë AI-në; vlera jonë për ta = akuizicioni
  24/7 + juridiksioni i dytë, jo AI. Opsioni 1 vetëm për intake, ose blerje.
- **Oferta hapëse**: Opsioni 1 (vetëm intake/zë) ose 3.
- **Kontakt**: përmes LinkedIn/kontaktit korporativ · anglisht/gjermanisht.
- **Pikët**: boshllëk 2 · blerje 4 · financa 5 · shpejtësi 2 · kopjim −3 → **10**

### 7. Actaport / dokSAFE — vendor cloud-native, M365
- **Kush**: cloud 100%, API, i fokusuar te zyrat e reja/M365. Buxhet blerjeje
  ndoshta i kufizuar, por kulturalisht më i afërti.
- **Pse i kryen punë**: u mungon AI e thellë + intake 24/7; API-first e bën
  integrimin OEM të lehtë. Edhe bashkim strategjik i mundshëm.
- **Oferta hapëse**: Opsioni 1 ose 2.
- **Kontakt**: kontakti i dokSAFE GmbH · gjermanisht.
- **Pikët**: boshllëk 4 · blerje 2 · financa 2 · shpejtësi 4 · kopjim −2 → **10**

### 8. DATEV eG — kooperativë e madhe (Anwalt classic)
- **Kush**: standard për zyrat me lidhje kontabiliteti; produkt që plaket,
  proces vendimmarrjeje i ngadaltë.
- **Pse (rezervë)**: kapacitet i madh, por vendos ngadalë; më mirë si blerës
  i vonë ose partner integrimi.
- **Oferta hapëse**: Opsioni 1.
- **Pikët**: boshllëk 3 · blerje 3 · financa 5 · shpejtësi 1 · kopjim −2 → **10**

## VALA 3 — rezervë / me kujdes

### 9. C.H.Beck & 10. Verlag Otto Schmidt — botues juridikë
- **Pse**: kanë përmbajtjen (beck-online), s'kanë softuerin e zyrës me AI;
  korpusi ynë + përmbajtja e tyre = sinergji. Vendosin ngadalë; hapemi me
  Opsionin 1 (OEM AI/korpus) ose 3.
- **Pikët**: boshllëk 3 · blerje 2 · financa 4 · shpejtësi 2 · kopjim −2 → **9**

### 11. JUPUS (dhe startup-e të tjera AI-native, VC) — KUJDES
- **Pse kujdes**: konkurrent i drejtpërdrejtë në filozofi. Letra u tregon
  çfarë kemi. Vetëm demo sipërfaqësore, me NDA të fortë, dhe vetëm nëse
  Vala 1–2 dështon. Rreziku i kopjimit është maksimal.
- **Pikët**: boshllëk 2 · blerje 2 · financa 3 · shpejtësi 5 · kopjim −5 → **7**

## Rregullat e dërgimit (të gjitha me PO/JO te Halim)

- Asnjë email pa aprovimin PO/JO të pronarit në Telegram.
- Letra në gjuhën e targetit; kurrë çmimet-dysheme interne
  (`qmimet-dyshemete-interne.txt` s'del kurrë jashtë); kurrë Kosova/AvokatIM
  te një blerës gjerman (brandi = Ava Legal).
- Bashkëngjitet oferta e plotë (`ava-legal-platform-offer-de.txt` / `-.txt`).
- Gjithmonë propozohet demo live brenda javës; kod vetëm pas LOI + NDA.
- Follow-up një herë pas 10 ditësh, pastaj heshtje.
