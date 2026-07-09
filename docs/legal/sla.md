# Marrëveshja e Nivelit të Shërbimit (SLA) — BoraLaw

> Model marrëveshjeje ndërmjet ofruesit të BoraLaw ("Ofruesi") dhe zyrës së
> avokatisë kliente ("Klienti"). Plotësohen fushat në kllapa para nënshkrimit.

**Data:** [____] · **Ofruesi:** [____] · **Klienti:** [____]

## 1. Shërbimi

Platforma BoraLaw për menaxhimin e praktikës ligjore: dosjet e lëndëve,
afatet, dokumentet, faturimi, portali i klientit dhe asistenti AI, e
qasshme si shërbim i instaluar në [serverin e Ofruesit / serverin e Klientit].

## 2. Disponueshmëria

| Treguesi | Angazhimi |
|---|---|
| Disponueshmëria mujore | **99.5%** (jashtë mirëmbajtjes së planifikuar) |
| Mirëmbajtja e planifikuar | Njoftim ≥ 48 orë më parë; jashtë orarit 08:00–18:00 të ditëve të punës |
| Dritarja e mirëmbajtjes | E diel 22:00 – 02:00 |

Disponueshmëria matet si përqindja e minutave brenda muajit kur shërbimi
i përgjigjet pikës `/api/health`.

## 3. Koha e reagimit ndaj incidenteve

| Prioriteti | Përkufizimi | Reagimi i parë | Synimi i zgjidhjes |
|---|---|---|---|
| P1 — Kritik | Shërbimi i paarritshëm ose humbje të dhënash | 2 orë pune | 8 orë pune |
| P2 — I lartë | Funksion kryesor i papërdorshëm (afatet, dokumentet, faturimi) | 4 orë pune | 2 ditë pune |
| P3 — Normal | Defekt me anashkalim të mundshëm | 1 ditë pune | 5 ditë pune |
| P4 — I ulët | Pyetje, kërkesa përmirësimi | 2 ditë pune | Sipas planifikimit |

Orari i mbështetjes: **E hënë – E premte, 09:00 – 17:00** (CET), përmes
[email/telefon]. Për P1 jashtë orarit: [numri i kujdestarisë].

## 4. Kopjet rezervë dhe rikthimi

| Treguesi | Angazhimi |
|---|---|
| Frekuenca e kopjeve | Çdo natë, të enkriptuara |
| Ruajtja e kopjeve | 30 ditë |
| RPO (humbja maksimale e të dhënave) | 24 orë |
| RTO (koha maksimale e rikthimit) | 8 orë pune |
| Testi i rikthimit | Çdo 6 muaj |

## 5. Siguria dhe të dhënat

- Dokumentet ruhen të enkriptuara në qetësi; qasja vetëm përmes HTTPS.
- Përpunimi i të dhënave rregullohet me **Marrëveshjen për Përpunimin e të
  Dhënave** (dokument i veçantë, pjesë e kësaj kontrate).
- Klienti mund të eksportojë të gjitha të dhënat e veta në çdo kohë
  (garancia e daljes — pa pagesë shtesë).

## 6. Përditësimet

- Përditësimet e sigurisë instalohen brenda [7] ditëve nga publikimi.
- Funksionet e reja dorëzohen pa ndërprerje të shërbimit kur është e mundur.

## 7. Kompensimi për mosdisponueshmëri

| Disponueshmëria mujore | Kredi mbi abonimin mujor |
|---|---|
| 99.0% – 99.5% | 10% |
| 95.0% – 99.0% | 25% |
| < 95.0% | 50% |

Kredia kërkohet me shkrim brenda 30 ditësh dhe zbatohet në faturën vijuese.

## 8. Përjashtimet

SLA nuk mbulon ndërprerje të shkaktuara nga: (a) infrastruktura e Klientit
ose e internetit; (b) keqpërdorimi i qasjeve; (c) forca madhore; (d) ndërhyrje
të palëve të treta të pa-autorizuara nga Ofruesi.

## 9. Kohëzgjatja dhe ndërprerja

Marrëveshja vlen sa kohë vlen kontrata e abonimit. Me ndërprerje, zbatohet
neni 9 i Marrëveshjes për Përpunimin e të Dhënave (eksporti dhe fshirja).

| Për Klientin | Për Ofruesin |
|---|---|
| Emri: [____] | Emri: [____] |
| Nënshkrimi: ______________ | Nënshkrimi: ______________ |
