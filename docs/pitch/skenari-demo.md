# Skenari i demonstrimit — 20 minuta

> Rrjedha e provuar për prezantim me një avokat ose zyrë ligjore.
> **Para çdo takimi:** `cd backend && .venv/bin/python scripts/seed_demo.py`
> (rikrijon tenant-in "Zyra Demo" nga zeroja — demoja s'nis kurrë bosh).

## Kredencialet

| Kush | Ku | Email | Fjalëkalimi |
|---|---|---|---|
| Avokatja | http://127.0.0.1:3000 (ose https://boraarifi.ai) | `demo@boralaw.app` | `Demo2026!bora` |
| Klienti (portal) | `/portal` — hapeni në **telefon** | `klienti.demo@boralaw.app` | `Demo2026!klient` |

---

## Rrjedha minutë-pas-minute

### 1. Paneli (2 min)
Kyçuni si avokatja. Tregoni me një shikim: agjenda e sotme, **Detyrat e mia**,
afatet e ardhshme, KPI-të (orë, fatura të papaguara, arkëtimi).
> "Gjithçka që ju duhet në mëngjes, në një ekran — në shqip."

### 2. Pranimi publik i klientëve (3 min)
Settings → kopjoni linkun e formularit publik → hapeni në tab tjetër.
Plotësoni një kërkesë si klient i ri. Kthehuni te **Pranimi**: kërkesa shfaqet me
**kontrollin automatik të konfliktit të interesit** dhe klasifikimin AI.
Një klik → lënda hapet me referencë automatike.
> "Asnjë klient s'ju humb më nga email-i apo telefonatat e harruara."

### 3. Lënda dhe afatet ligjore (4 min)
Hapni lëndën "Përmbarimi i borxhit 48.000 €". Tregoni tab-et: palët, dokumentet,
afatet, **detyrat**, mesazhet.
Te Afatet: shtoni afat **nga rregulli ligjor** (p.sh. kundërshtimi i urdhërpagesës,
LPK neni 156) — data llogaritet vetë, duke i anashkaluar fundjavat dhe **festat e Kosovës**.
Te Dokumentet: hapni **parapamjen** e kontratës, pastaj klikoni **"Nxirr afatet me AI"**
— Bora i lexon vendimet gjyqësore dhe i propozon afatet vetë.
> "Ky është ai gabimi që i kushton karrierën një avokati — afati i humbur. Këtu s'ndodh."

### 4. Bora — asistentja ligjore (3 min)
Tab-i AI në lëndë ose faqja e Bora-s. Pyesni:
*"Sa është afati për kundërshtim të urdhërpagesës dhe cili nen e rregullon?"*
Tregoni **citimet nga ligjet reale të Kosovës** (GZK). Pastaj "Përmblidhe lëndën".
> "Nuk është chatbot i përgjithshëm — përgjigjet me nene konkrete nga korpusi ynë ligjor."

### 5. Shkresa nga shablloni (2 min)
Te Shabllonet: zgjidhni "Padi", zgjidhni lëndën — fushat mbushen vetë nga lënda,
çka mungon del si `__________` për plotësim. Klikoni **"Ruaje në lëndë"** —
bëhet dokument PDF i lëndës, i kërkueshëm.
> "Shkresa juaj standarde për 30 sekonda, jo 30 minuta."

### 6. Faturimi (3 min)
Te Faturimi: orët e punës, **shpenzimet** (taksa gjyqësore, përmbaruesi), krijoni
faturë me një klik — orët + shpenzimet + artikull flat-fee, **TVSH 18%** vetë.
Klikoni **"Shkarko PDF"** — faturë fiskale me NUI, TVSH dhe IBAN.
Butoni **"Dërgoja klientit"** e nis me email dhe e kalon në "E dërguar".
> "Nga puna te paraja pa Excel dhe pa Word."

### 7. Portali i klientit — NË TELEFON (3 min)
Hapni `/portal` në telefonin tuaj si klienti. Tregoni: lënda + seancat e ardhshme,
**dokumentet e ndara nga avokati**, mesazhet dy-kahëshe (dërgoni një — avokatit i
shkon email), **nënshkrimi elektronik** i dokumentit me certifikatë PDF (SHA-256, IP, ora).
> "Klienti juaj s'ju telefonon më për 'çka po ndodh me lëndën time' — e sheh vetë."

### 8. Mbyllja (1 min)
Settings si admin: **Regjistri i veprimeve** (kush bëri çka, kur) dhe
**Eksporti i të dhënave** (ZIP me CSV + dokumentet).
> "Të dhënat janë tuajat, të enkriptuara në serverin tuaj — dhe i merrni kurdo."

---

## Pikat e forta për t'u theksuar

- **I vetmi sistem i lokalizuar për Kosovë**: afatet nga LPK/KPPRK, festat zyrtare,
  TVSH 18%, shabllonet në shqip, korpusi ligjor i GZK-së.
- **AI që citon ligjin**, jo që improvizon.
- Dokumentet **të enkriptuara at-rest**, indeksim **lokal** (teksti s'del nga serveri).
- Multi-tenant: nga avokati solo te zyra me ekip (role, lëndë të kufizuara, 2FA).
- Çmimi konkurrues ndaj Clio/Smokeball (~49–129 $/muaj/user) që s'kanë asgjë për Kosovën.

## Përgjigjet e gatshme për pyetjet e njohura

| Pyetja | Përgjigjja |
|---|---|
| "A lidhet me email-in tim (Gmail/Outlook)?" | Në zhvillim — faza tjetër. Sot: njoftimet email dalin vetë nga sistemi. |
| "A pranon pagesa me kartelë?" | Në plan me kërkesë — sot fatura PDF me IBAN + shënimi i pagesës me referencë. |
| "Tarifat e Odës së Avokatëve?" | Në backlog — sot tarifa orare + flat-fee për artikull. |
| "SMS për klientët?" | Sot email + push në telefon (PWA); SMS me kërkesë. |
| "A i marr të dhënat po u largova?" | Po — eksporti ZIP me një klik (CSV + të gjitha dokumentet). |
| "Ku ruhen të dhënat?" | Në serverin tuaj/tonë në lokal, të enkriptuara; asgjë s'indeksohet në cloud. |

## Pas takimit

```bash
cd backend && .venv/bin/python scripts/seed_demo.py            # rikthe demon të pastër
cd backend && .venv/bin/python scripts/seed_demo.py --delete   # ose fshije fare
```
