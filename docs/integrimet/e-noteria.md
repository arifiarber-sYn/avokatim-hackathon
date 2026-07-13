# Gatishmëria për e-noterinë (noterizimi në distancë)

> Dokument strategjik: çfarë ndryshimi ligjor duhet për noterizimin në
> distancë në Kosovë, dhe pse AvokatIM është infrastruktura e gatshme kur
> të vijë ai moment. Përdoret edhe si argument në pitch-un qeveritar
> (shih `docs/pitch/qasje-ne-drejtesi.md`).

## Gjendja ligjore sot (2026)

- **Ligji Nr. 06/L-010 për Noterinë** kërkon praninë fizike të palës para
  noterit për aktet noteriale dhe solemnizimet; identifikimi bëhet me
  dokument identifikimi në zyrë.
- **Ligji Nr. 08/L-149 (2022)** zgjidhi vetëm mbulimin territorial: ministri
  mund të caktojë noter nga një territor tjetër për komunat pa noter.
- **Ligji Nr. 08/L-272 (2024)** hapi derën e digjitalizimit: nenet 31A/31B
  fusin **nënshkrimin elektronik të noterit** për përgatitjen e akteve
  noteriale në formë elektronike, dhe disiplina kaloi te Ministria e
  Drejtësisë. Por prania fizike e palës mbetet e detyrueshme.
- **Ligji Nr. 04/L-150 për dokumentet elektronike** dhe skema eIDAS-kompatibile
  e Kosovës japin bazën për identifikim elektronik të kualifikuar.

Pra: akti noterial elektronik tashmë ekziston si koncept ligjor; hallka që
mungon është **pjesëmarrja e palës në distancë** (identifikimi dhe vullneti
i shprehur përmes video-lidhjes).

## Modelet ndërkombëtare

| Model | Si funksionon | Çfarë kërkoi ligjërisht |
|---|---|---|
| **Estonia (e-Notar)** | Që nga 2020, aktet noteriale kryhen me video-lidhje përmes portalit shtetëror; identifikimi me eID/Mobile-ID; akti nënshkruhet digjitalisht nga të gjithë | Ndryshim i ligjit të noterisë + infrastruktura eID shtetërore + portali qendror i noterëve |
| **SHBA (RON — Remote Online Notarization)** | Mbi 45 shtete e lejojnë; platforma private të licencuara; identifikim me analizë dokumenti + pyetje sigurie (KBA); seanca inçizohet dhe ruhet 10 vjet | Ligje shtetërore RON; standardet MISMO/ALTA; auditim i regjistrimeve |
| **BE (eIDAS 2.0 / EUDI Wallet)** | Portofoli evropian i identitetit digjital (2026+) do të mundësojë identifikim të kualifikuar ndërkufitar — parakusht natyror për e-noteri | Rregullorja eIDAS 2.0, zbatimi kombëtar |

## Çfarë ndryshimi ligjor duhet në Kosovë

Ndryshim/plotësim i Ligjit 06/L-010 (ose ligj i ri për e-noterinë) që:

1. **Lejon pjesëmarrjen me video-lidhje** të palës për akte të caktuara
   (fillimisht: autorizime, vërtetime nënshkrimi, deklarata — jo domosdo
   patundshmëria në fazën e parë, sipas modelit gradual estonez).
2. **Njeh identifikimin elektronik të kualifikuar** (eID e Kosovës /
   letërnjoftimi biometrik / EUDI Wallet kur të vijë) si ekuivalent të
   paraqitjes së letërnjoftimit në zyrë.
3. **Detyron inçizimin dhe ruajtjen e seancës** (audio+video) si pjesë e
   regjistrit noterial, me afat ruajtjeje të përcaktuar.
4. Përcakton **platformat e licencuara** ose portalin qendror (MD/ONK) ku
   zhvillohen seancat.

## Pse AvokatIM është infrastruktura e gatshme

Çdo bllok teknik që kërkon e-noteria ekziston tashmë në AvokatIM, i ndërtuar
dhe i testuar për skenarë të tjerë:

- **Video/audio në kohë reale**: LiveKit i vetë-hostuar (SOS-thirrjet me
  avokatë) — i njëjti stack mban seancën noteriale në distancë.
- **Inçizimi me vlerë provuese**: kasaforta e dëshmive me zinxhir hash-esh
  (SHA-256 të lidhura), enkriptim në ruajtje dhe gjurmë auditimi — pikërisht
  ajo që kërkon RON-i amerikan (ruajtja 10-vjeçare e seancave).
- **Identifikimi dhe llogaritë**: llogari qytetarësh me verifikim, dhe
  arkitektura multi-tenant ku zyrat noteriale hyjnë njësoj si zyrat e
  avokatëve — pa asnjë ndryshim strukturor.
- **Dokumenti elektronik**: gjenerimi i akteve si PDF me meta të dhëna,
  gati për nënshkrim elektronik të kualifikuar (neni 31A/31B i ligjit
  ekzistues).
- **Përgatitja e palës**: `/noteret` (drejtoria + tarifa) dhe "pako për
  noter" te `/dokumentet` tashmë e çojnë palën te noteri me draft dhe
  dokumente të plota — e-noteria është thjesht hapi i fundit i të njëjtit
  fluks.

## Hapat kur të hapet dritarja

1. Memorandum me ONK-në (shih `docs/rekrutimi/kontakt-onk.md`) — drejtoria
   e verifikuar dhe fluksi i palëve të përgatitura.
2. Pilot me MD-në: seanca në distancë për vërtetime të thjeshta
   (autorizime, deklarata) me inçizim në kasafortën e dëshmive.
3. Integrimi me eID-në shtetërore kur të jetë gati (shih `e-kosova.md`).
