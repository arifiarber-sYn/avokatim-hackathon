# Gatishmëria për integrim me e-Kosova dhe gjykatat

> Dokument përgatitor (korrik 2026). Sot nuk ekziston API publike e e-Kosova
> apo e sistemit informativ të gjykatave (SMIL/CMIS) për palë të treta —
> ky dokument përshkruan pikat e integrimit që AvokatIM i ka të gatshme
> arkitekturalisht, që kur qasja të hapet, integrimi të jetë punë ditësh
> e jo muajsh.

## Konteksti

- **e-Kosova** (ekosova.rks-gov.net) është portali qendror i shërbimeve
  qeveritare me identifikim eID; ofron certifikata, aplikime dhe pagesa,
  por ende pa API të dokumentuar publike për integrime private.
- **SMIL/CMIS** është sistemi i menaxhimit informativ të lëndëve në gjykatat
  e Kosovës (Këshilli Gjyqësor i Kosovës). Qasja e jashtme sot bëhet vetëm
  përmes portalit publik të vendimeve të publikuara.
- Strategjia e digjitalizimit të drejtësisë parasheh hapjen graduale të
  shërbimeve — AvokatIM synon të jetë ndër integruesit e parë.

## Pikat e integrimit të parapërgatitura

| # | Integrimi i ardhshëm | Çfarë kemi gati sot |
|---|---|---|
| 1 | **Statusi i lëndës nga gjykata** (pull/webhook nga SMIL) | `Matter.court_name` + `court_case_number` janë fusha të strukturuara; historia e lëndës është append-only; audit log për çdo ndryshim. Një sync-service i ri do të përditësonte statusin pa prekur skemën. |
| 2 | **Oraret e seancave** | Modeli `Deadline` (kind=hearing) + kalendari ICS ekzistues; seancat e importuara nga gjykata do të hynin në të njëjtin kanal njoftimesh (email/push/SMS) që tashmë funksionon. |
| 3 | **Dorëzimi elektronik i shkresave (e-filing)** | Shabllonet gjenerojnë PDF/DOCX të strukturuar me metadata (lënda, gjykata, numri); dokumentet kanë hash SHA-256 dhe nënshkrim të thjeshtë elektronik — gati për t'u lidhur me nënshkrimin e kualifikuar (QTSP, Ligji 08/L-022) kur e-filing të hapet. |
| 4 | **Identifikimi eID i qytetarit** | Llogaria e qytetarit (`CitizenUser`) është e ndarë nga avokatët; rrjedha e verifikimit me email mund të zëvendësohet/plotësohet me eID të e-Kosova si Identity Provider (OIDC) pa ndryshuar modelin. |
| 5 | **Regjistri i avokatëve të OAK** | Verifikimi i licencës sot bëhet manualisht kundrejt regjistrit të OAK; një API e OAK do ta bënte verifikimin automatik — fusha `oak_license_no` + `verification_status` ekzistojnë. |
| 6 | **Ndihma juridike falas shtetërore** | Tregu i rasteve mund të kanalizojë rastet që s'i mbulon tregu drejt Agjencisë për Ndihmë Juridike Falas — mjafton një tenant i dedikuar + rregull rutimi. |

## Parimet e integrimit

1. **Të dhënat e klientit nuk dalin pa bazë ligjore** — çdo integrim kalon
   nëpër pëlqimin e qytetarit (ConsentRecord) dhe audit log.
2. **Jurisdiksioni si të dhëna** — statuset/oraret e importuara ruhen si
   të dhëna të jurisdiksionit XK, jo si logjikë e ngurtë në kod.
3. **Degradim i butë** — si çdo integrim ekzistues (SMS, Stripe, IMAP),
   edhe këto do të jenë opsionale me konfigurim në `.env` dhe pa efekt
   kur s'janë të konfiguruara.

## Hapat e propozuar (kur qasja të hapet)

1. Marrëveshje qasjeje me KGjK/MD për SMIL read-only (statuse + seanca).
2. Pilot me një gjykatë themelore: sync i statuseve për lëndët e
   regjistruara në AvokatIM me numër të lëndës gjyqësore.
3. eID login për qytetarët përmes e-Kosova (OIDC).
4. E-filing me nënshkrim të kualifikuar (pas integrimit QTSP — shih D-007).
