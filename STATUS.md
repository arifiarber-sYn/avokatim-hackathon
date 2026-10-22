# STATUS — Open Agent Hackathon 2026

Data: 22.10.2026 · Dega: hackathon/open-agent-2026 · Afati: 27.10.2026 23:45 UTC
Dorëzuar: platforma GenAI.Works — #1 **The Agent That Can Explain Why** (Submitted), #2 **Wildcard [Tinkerer]** (Submitted), 2/3

## Cka punon sot

- Kerkim vektor mbi 353 442 fragmente (350 612 me embeddings 384-dim), i kufizuar ne
  gjuhen e pyetjes.
- Rirenditje hibride: 50 kandidate vektor + bonus per terma juridike + preference per
  burime primare (ligj/kod) ndaj vendimeve.
- Porte domeni: pyetjet jashtë juridik refuzohen me arsye.
- Demo CLI: pyetje -> deshmi -> pergjigje me citime, ose "s'e di".
- Harness: 3 sete (20 + 13 + 13). Blind: 10/10 brenda, 3/3 refuzuar.

## Cka eshte e matur, cka jo

- E matur: prania e termit juridik ne fragmentin e kthyer; refuzimi i pyetjeve jashte
  korpusit.
- E matur tani (10 pyetje, verifikim AI mbi titullin dhe tekstin e nenit):
  10/10 ligj i sakte ne vendin e pare, 2/10 nen i sakte i plote, 7/10 nen i duhur brenda
  top-3, 0/10 burim i gabuar ne krye.
  Detajet: docs/hackathon/arta-verifikuar.md

## Sponsoret

| Sponsori | Statusi | Prova |
|---|---|---|
| Zetaris | Platforma xhiron (4 konteinerë healthy, UI 307→login); **tokeni API PRANOHET përsëri — verifikuar live 22.10 20:2x** (`SELECT 1`→`[['1']]` 2×, `current_catalog()`→spark_catalog/default); dritarja e dështimit 17:10 ka mbaruar | backend/app/adapters/zetaris.py |
| Zetaris datasource | **0 datasources** (`SHOW DATASOURCES`→`[]`); `legal_corpus` MUNGON; `CREATE TABLE` kthen metadata por tabela s'lexohet (Spark s'ka warehouse pa datasource) → hapi i mbetur: regjistrim datasource në UI (127.0.0.1:3011) | provë 22.10 20:2x |
| Meterless | Adapter + usage.jsonl | backend/app/adapters/meterless.py |
| Meterless Nightshift | Pa build per Linux x86_64; kerkesa derguar 22.10 | — |

## Ku te shikohet

- Submission: docs/hackathon/submission.md
- Setup: docs/hackathon/README-dorezimi.md
- Deck: docs/hackathon/deck.pdf
- Video: docs/hackathon/video/demo-full.mp4
- Puna dhe vendimet: docs/agents/HACKATHON-OPEN-AGENT.md
