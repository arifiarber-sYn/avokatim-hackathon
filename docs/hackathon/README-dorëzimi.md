# AvokatIM — agjenti që shpjegon pse

Dorëzim për Open Agent Hackathon 2026, track Wildcard [Tinkerer].
AvokatIM është produkt live (avokatiim.ai); puna e re e këtij repo-je është shtresa
që e bën përgjigjen të verifikueshme dhe të matshme.

## Çka është e re

- Zetaris adapter — një sipërfaqe query mbi burime të fragmentuara
- Meterless adapter — ekzekutim lokal + matje e kostos (usage.jsonl)
- Meta Model adapter — modelet e Meta-s, me stub offline
- Harness etalon — 20 + 13 + 13 pyetje, tri sete, matje e përsëritshme
- Demo CLI — pyetje → dëshmi → përgjigje me citime, ose "s'e di" me arsye

## Si ngrihet (më pak se 10 minuta)

1. Kërkohen: Python 3.12+, Postgres me pgvector, korpusi i indeksuar i AvokatIM.
2. Krijo backend/.env me DATABASE_URL (dhe opsionale ZETARIS_*, META_MODEL_*).
3. cd backend; pip install -e .  (ose përdor venv-in ekzistues)
4. Modeli i embeddings: paraphrase-multilingual-MiniLM-L12-v2 (shkarkohet një herë)
5. Ekzekuto:
   - AVOKATIM_DSN=<dsn> python hackathon/demo.py "pyetja"
   - AVOKATIM_DSN=<dsn> python hackathon/harness_v5.py
   - HARNESS_Q=questions-blind.json HARNESS_TAG=blind AVOKATIM_DSN=<dsn> python hackathon/harness_v5.py

## Arkitektura

    Pyetja
      └─ Orchestrator: plan → query → verify
           ├─ ZetarisAdapter   (SQL federativ; REST /sql-editor/sqls/run)
           ├─ MeterlessAdapter (model lokal + usage.jsonl)
           └─ MetaModelAdapter (Muse/SAM, OpenAI-compatible)
                ↓
           Evidence[]  (source_id, uri, fragment, page, confidence)
                ↓
           Përgjigje + citime të klikueshme, ose "s'e di"

Asnjë SDK i sponsorit nuk futet në core: çdo burim kalon nga adapteri, prandaj
HACKATHON_MODE=false e lë sjelljen e prodhimit të paprekur.

## Matjet

| Seti | Brenda korpusit | Jashtë korpusit |
|---|---|---|
| I akorduar (20) | 15/15 | 5/5 |
| Held-out (13) | 9/10 | 3/3 |
| Blind (13) | 10/10 | 3/3 |

KUFIZIM METODOLOGJIK: "brenda" mat praninë e termit juridik në fragmentin e kthyer,
jo korrektësinë e dokumentit të parë. Matja me përgjigje-arta është hapi pasardhës
dhe kërkon verifikim njerëzor.

## Kufizime të njohura

- Zetaris: platforma lokale punon (SELECT 1 → 200), por DDL/CTAS nuk materializohen
  në këtë build; federimi i vërtetë kërkon regjistrimin e datasource.
- Meterless: Nightshift nuk ka build për Linux x86_64 (vetëm Mac/Windows/DGX arm64).
  Kërkesa u dërgua te partnerships@meterless.ai; alternativa është model lokal + matje.
- Meta Model API: adapteri është gati; çelësi vjen nga onboarding-u i garës.

## Të dhënat

Korpusi juridik mbetet në makinë; embeddings llogariten lokalisht. Asnjë dokument
nuk dërgohet në shërbim të jashtëm në këtë dorëzim.
