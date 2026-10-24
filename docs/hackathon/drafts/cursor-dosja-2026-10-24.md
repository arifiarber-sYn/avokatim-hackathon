# Cursor — dosja e provave (24.10.2026)

Llogaria: arifi.arber@gmail.com · Plan: **Ultra ($200/mo)** · Anulim i planifikuar: 16.11.2026
Ticket: **T-I12995** · Kundërshtimi: faturim pa bazë (jo çmimi, jo paketa)

## 1. Shpenzimi i verifikuar (dashboard, 1–21 tetor 2026)

| | Shuma |
|---|---|
| Fatura të paguara (29) | **$3 023.01** |
| Fatura të papaguara (2) | **$146.41** |
| **Gjithsej tetor** | **$3 169.42** |

Faturat e papaguara: `OWUYQTEL-0312` $100.09 (21.10) dhe `OWUYQTEL-0311` $46.32 (18.10).

**Modeli që ngre dyshimin:** fatura të shumta mid-month nga ~$100, disa të njëjtën ditë:
1 tetor ×3, 2 tetor ×4, 4 tetor ×3, 5 tetor ×3, 8 tetor ×2, 14 tetor ×2, 16 tetor ×3.

## 2. Pranimi i Cursor-it (email 12.08.2026)

> «Some on-demand usage incurred **on or after July 1, 2026** was not invoiced when the applicable billing cycle ended… We're issuing a **one-time correction invoice**… The invoice may cover **more than one completed billing period**.»

Ky është pranim me shkrim se faturimi ishte i gabuar për periudhë të pacaktuar.

## 3. Njoftimet e dështimit të pagesës (të gjitha)

| Data | Shuma |
|---|---|
| 26.08 | $100.35 |
| 29.08 | $100.35 |
| 18.10 | $46.32 |
| 20.10 | $46.32 |
| 21.10 | $100.09 (×2) |
| 23.10 | $100.09 + $46.32 |

## 4. Historia e komunikimit

| Data | Çka |
|---|---|
| 04.05, 06.06, 10.06, 26.08, 03.09 | «Couldn't process payment» — pa përgjigje përfundimtare |
| 12.08 | Njoftim për faturim të papaguar që nga 1 korriku |
| 19.08 | «Increased included usage and update to Auto pricing» |
| 21–22.10 | Kërkesë për audit; Sam (Cursor) përgjigjet me shpjegim threshold-i + 2 fatura të hapura; nuk jep IP/sesione |
| 23.10 | Addendum: 3 pyetje me shkrim (çka mbulon secila faturë, kur ndodhi «korrigjimi i gushtit», sa herë janë ritentuar pagesat) — **pa përgjigje** |

## 5. Konteksti i shpenzimit

Klienti shpenzon **rregullisht mbi $3 000/muaj**, dhe në muajt e pikut deri **~$5 000/muaj** (deklaratë e klientit; eksporti i plotë i faturave ende s'është nxjerrë).
Pretendimi nuk është për çmimin: është për **fatura pa bazë të dokumentuar**.

## 6. Boshllëku

Dashboard-i shfaq vetëm muajin aktual; faturat e muajve të mëparshëm kërkojnë ciklin përkatës. Totali më lart është **i verifikuar për tetorin**; totali historik mbetet për t'u nxjerrë.

## 7. Totali historik (API i Cursor-it, 24.10.2026)

Burimi: `POST /api/dashboard/list-invoices` me sesionin e llogarisë. **100 fatura** të kthyera.

| Periudha | Fatura | Shuma e paguar |
|---|---|---|
| 23–31 gusht 2026 | 9 | $904.89 |
| Shtator 2026 | **60** | **$6 145.03** |
| 1–21 tetor 2026 | 31 | $3 023.01 |
| **Gjithsej** | **100** | **$10 072.93** |

Plus **$146.41** të hapura (2 fatura) → **$10 219.34** gjithsej i faturuar.

Mesatarja: **$3 357.64/muaj** (mbi tre muaj të pjesshëm). Shtatori i vetëm: **$6 145.03** — 60 fatura në 30 ditë, mesatarisht dy në ditë.

**Kufizim i deklaruar:** endpoint-i kthen 100 fatura (23.08 → 21.10.2026). Faturat më të vjetra (pranverë 2026, kur nisën njoftimet e para të dështimit) nuk ekspozohen nga ky endpoint — për ato duhet portali i Stripe-it.
