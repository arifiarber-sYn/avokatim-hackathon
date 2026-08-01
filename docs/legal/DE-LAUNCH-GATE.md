# Porta e lansimit publik në Gjermani (D-034)

> Ky dokument liston kushtet që DUHEN plotësuar para se `de.avokatiim.ai`
> të promovohet publikisht në Gjermani. Zhvillimi dhe testimi NUK bllokohen
> nga kjo listë — vetëm marketingu/lansimi publik.

## Statusi aktual

Platforma gjermane është funksionale në `de.avokatiim.ai`: juridiksioni DE,
korpusi ligjor federal (gesetze-im-internet.de), Ava në gjermanisht me kufij
RDG dhe deklarim AI Act, afatet ZPO/StPO/KSchG/VwGO/SGG, tarifa RVG, festat
federale, template dokumentesh, AGB + Datenschutzerklärung draft, Impressum
me placeholder.

## Kushtet e portës (para lansimit publik)

1. **Server në BE për të dhënat e qytetarëve gjermanë** — GDPR Art. 3(2);
   "Serverstandort Deutschland/EU" është edhe argument shitjeje. Hostimi
   aktual në makinën e pronarit mjafton vetëm për beta të mbyllur.
2. **Përfaqësues në BE sipas GDPR Art. 27** — i detyrueshëm për ofrues
   jashtë BE-së që përpunojnë të dhëna të banorëve të BE-së.
3. **LLM provider në BE për kërkesat DE** — konfigurohu te
   `JurisdictionProfile.llm_provider` në `backend/app/jurisdictions.py`
   (rekomandim: Mistral). Deri atëherë DE Ava punon me providerin default
   por me deklarim të plotë transparence.
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
