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
3. **LLM lokal për kërkesat DE** — infrastruktura ✅ **GATI (D-037)**:
   `gemma3:27b` në Ollama është instaluar, testuar dhe validuar
   (kundër qwen3:14b për cilësi gjermanishteje; gemma3 fitoi: pa
   "thinking", latencë e parashikueshme, citim korrekt me RAG).
   **⚠️ PËRKOHËSISHT në DeepSeek** (kërkesa e pronarit 2026-08-01, për
   demonstrimin e plotë të funksioneve). PARA lansimit publik kthe
   `PROFILES["DE"].llm_provider = "local"` në `backend/app/jurisdictions.py`
   — vetëm atëherë asnjë kërkesë qytetari DE s'del nga makina.
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
