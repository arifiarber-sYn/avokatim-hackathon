# STATUS — Open Agent Hackathon 2026 (Wildcard [Tinkerer])

Data: 22.10.2026 · Dega: hackathon/open-agent-2026 · Afati: 27.10.2026 23:45 UTC

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
- E pa-matur: saktesia e dokumentit te pare ndaj nje pergjigjeje-arte. Fleta e
  verifikimit (docs/hackathon/arta-per-verifikim.md) eshte pergatitur, pret verifikim
  njerezor.

## Sponsoret

| Sponsori | Statusi | Prova |
|---|---|---|
| Zetaris | Adapter live; SELECT 1 -> 200 | backend/app/adapters/zetaris.py |
| Zetaris datasource | I papërfunduar (hap manual ne UI) | — |
| Meterless | Adapter + usage.jsonl | backend/app/adapters/meterless.py |
| Meterless Nightshift | Pa build per Linux x86_64; kerkesa derguar 22.10 | — |

## Ku te shikohet

- Submission: docs/hackathon/submission.md
- Setup: docs/hackathon/README-dorezimi.md
- Deck: docs/hackathon/deck.pdf
- Video: docs/hackathon/video/demo-full.mp4
- Puna dhe vendimet: docs/agents/HACKATHON-OPEN-AGENT.md
