# Open Agent Hackathon 2026 — ku gjendet cka

Track: Wildcard [Tinkerer] · afati: 27.10.2026, 23:45 UTC
Kjo dege (hackathon/open-agent-2026) permban punen e re; master mbetet prodhimi.

| Cka | Ku |
|---|---|
| Pershkrimi i dorezimit | docs/hackathon/submission.md |
| README i dorezimit (setup <10 min) | docs/hackathon/README-dorezimi.md |
| Deck (markdown / PDF) | docs/hackathon/deck-open-agent.md · deck.pdf |
| Video demo | docs/hackathon/video/demo-full.mp4 |
| Storyboard | docs/hackathon/video-storyboard.md |
| Flete verifikimi (pergjigje-arta) | docs/hackathon/arta-per-verifikim.md |
| Adapterat | backend/app/adapters/ (base, zetaris, meterless, meta_model) |
| Harness + demo | backend/hackathon/ (harness_v5.py, demo.py, questions*.json) |
| Dokumentim i punes | docs/agents/HACKATHON-OPEN-AGENT.md |

## Statusi i integrimit te sponsoreve

- Zetaris: adapter live kunder REST SQL editor (SELECT 1 -> 200). Datasource i korpusit
  kerkon regjistrim manual ne UI-ne e platformes; nuk pretendohet i kryer.
- Meterless: adapter + usage.jsonl; Nightshift nuk ka build per Linux x86_64 (vetem
  Mac/Windows/DGX arm64). Kerkese per build/API u dergua me 22.10.

## Si ekzekutohet

Shih docs/hackathon/README-dorezimi.md. Shkurt: Postgres me pgvector + korpusi i
AvokatIM, pastaj python hackathon/demo.py "pyetja" ose python hackathon/harness_v5.py.
