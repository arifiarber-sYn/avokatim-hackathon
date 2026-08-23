# Porta e lansimit publik në Gjermani (D-034)

> Ky dokument liston kushtet që DUHEN plotësuar para se `de.avokatiim.ai`
> të promovohet publikisht në Gjermani. Zhvillimi dhe testimi NUK bllokohen
> nga kjo listë — vetëm marketingu/lansimi publik.

## Statusi aktual

Platforma gjermane është funksionale në `de.avokatiim.ai`: juridiksioni DE,
korpusi ligjor federal (gesetze-im-internet.de) + DSGVO + Landesrecht NRW/BY,
Ava në gjermanisht me kufij RDG dhe deklarim AI Act, afatet ZPO/StPO/KSchG/
VwGO/SGG me muaj ekzaktë dhe festa landesh, template dokumentesh, AGB +
Datenschutzerklärung draft, Impressum me placeholder.

**Pariteti me tregun (D-037, 2026-08-01):** motori i plotë RVG (§ 13 tabela
KostBRÄG 2025 + kalkulatori publik /rvg), E-Rechnung ZUGFeRD/Factur-X
(PDF/A-3b, validuar me Mustangproject), sigurimi juridik në rrjedhën e
rastit + shablloni Deckungsanfrage, eksporti DATEV EXTF. Verifikuar E2E me
`backend/scripts/de_simulation.py` (15 kontrolle). **LLM lokal aktiv**:
`PROFILES["DE"].llm_provider="local"` → Ollama `gemma3:27b` në RTX 5090
(17.5 GB VRAM, ~50 tok/s) — asnjë e dhënë qytetari gjerman s'del nga serveri.

## Kushtet e portës (para lansimit publik)

1. **Server në BE për të dhënat e qytetarëve gjermanë** — GDPR Art. 3(2);
   "Serverstandort Deutschland/EU" është edhe argument shitjeje. Hostimi
   aktual në makinën e pronarit mjafton vetëm për beta të mbyllur.
2. **Përfaqësues në BE sipas GDPR Art. 27** — i detyrueshëm për ofrues
   jashtë BE-së që përpunojnë të dhëna të banorëve të BE-së.
3. **LLM lokal për kërkesat DE** — ⚠️ **RIHAPUR: kërkon RI-VALIDIM (D-082, 2026-08-15)**.
   Baseline-i i vjetër `gemma3:27b` u **fshi** në konsolidimin fleet-wide të modeleve
   (openclaw-knowledge D-082). Modeli i ri lokal = **`qwen3.8:27b`**
   (`backend/.env: LOCAL_LLM_MODEL=qwen3.8:27b`; `backend/app/llm/local.py` shton
   `reasoning_effort=low` sepse qwen3.8 është model "thinking"). Validim informal i mëparshëm:
   shootout-i DE i D-081 (pa përgjigje boshe, dallim korrekt Mieter/Vermieter § 573c BGB,
   citim korrekt "Art. 17 DSGVO", latencë 1.7–3.5s). **⚠️ PËRKOHËSISHT në DeepSeek**
   (kërkesa e pronarit 2026-08-01).
   **RI-VALIDIMI FORMAL I EKZEKUTUAR 2026-08-23 (P-07, `backend/scripts/eval_de_quality.py`):**
   kriteret e cilësisë (a) KALOJAAN me `qwen3.8:27b` — 20/20 jo-bosh, 19/20 citim ref+§,
   20/20 gjermanisht e pastër, 0 statute të shpikura — por **kriteret infrastrukturore
   DËSHTOJNË**: p95 latencë 19.3s (kërkohet ≤5s) dhe prompt max 15.3K tokena > 80% e ctx
   16384 të shërbyer (chunk-e gjigantë në korpus). Varianti `qwen3.8:27b-agent` (ctx 98K)
   s'është praktik në këtë makinë (VRAM e pamjaftueshme → CPU offload). **DE QËNDRON NË
   DeepSeek** derisa: (1) të rregullohet chunk-ing-u i korpusit DE, (2) të zgjidhet latenca
   (GPU e lirë/dedikuar ose kriter i rishikuar), (3) të ri-ekzekutohet eval-i. Detaje: JOURNAL 2026-08-23.
4. **Rishikim ligjor nga avokat gjerman** i AGB-ve, Datenschutzerklärung
   dhe Impressum (draftet janë në `frontend/src/lib/legal.ts` dhe
   `frontend/src/app/impressum/page.tsx`). Plotëso adresën fizike te
   Impressum (§ 5 DDG kërkon "ladungsfähige Anschrift").
5. **TVSH gjermane (19%)** — çështja e regjistrimit tatimor shtyhet:
   viti i parë falas s'ka pagesa. Rishiko para faturimit të parë real.
6. **Verifikimi BRAV** — procesi manual njëklikësh me link BRAV funksionon;
   vlerëso scraper automatik kur BRAV të jetë i qëndrueshëm
   (bravsearch.bea-brak.de kthente 503 më 2026-08-01).

## Kufijtë ligjorë të respektuar në kod

- **§ 2 RDG**: Ava publike DE jep vetëm Rechtsinformation, kurrë vlerësim
  të rastit individual (prompt në `backend/app/api/marketplace.py`,
  `PUBLIC_AVA_SYSTEM_PROMPT_DE`).
- **EU AI Act Art. 50** (në fuqi 2 gusht 2026): deklarimi "po flisni me AI"
  në prompt + UI.
- **§ 49b(3) BRAO**: modeli ynë i abonimit fiks mujor është i lejuar;
  asnjë komision për mandate konkrete.
- **SOS dhe noteria janë të fshehura/bllokuara për DE** (frontend + guard
  në backend) deri në përshtatje të veçantë ligjore.
