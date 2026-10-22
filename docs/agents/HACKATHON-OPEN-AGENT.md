# HACKATHON — Open Agent 2026 (Wildcard [Tinkerer])

Statusi: aktiv · Dega: hackathon/open-agent-2026 · Worktree: /home/kllosha/AvokatIM-hack
Afati i dorëzimit: 27.10.2026, 23:45 UTC

## Pse
Open Agent Hackathon ka një track të vetëm që pranon projekt ekzistues: **Wildcard
[Tinkerer]**. Rregullat e tij kërkojnë integrim të **Zetaris** dhe **Meterless** dhe
vlerësojnë vetëm punën e re. AvokatIM është projekti ynë ekzistues; puna e re është
shtresa e adapterave.

## Çfarë u shtua (Faza A, 22.10.2026)
- backend/app/adapters/base.py — kontrata Evidence / QuerySpec / SourceAdapter / dedupe
- backend/app/adapters/zetaris.py — adapter live (HTTP) + FixtureAdapter (mock i deklaruar)
- backend/app/adapters/meterless.py — ekzekutim lokal + usage.jsonl (një rresht për thirrje)
- backend/app/config.py — hackathon_mode (default false), zetaris_*, meterless_*,
  hackathon_usage_log
- backend/tests/test_adapters_contract.py — 5 teste, pa rrjet/DB

## Parimi
Asnjë SDK i sponsorit nuk futet në core. Gjithçka e jashtme vjen si Evidence përmes
adapterit, prandaj kodi ekzistues nuk ndryshon sjellje kur hackathon_mode=False.

## Hapat pasardhës
1. Zetaris: llogari + lidhja e tri burimeve (ligje / praktikë / regjistra).
2. Meterless: Nightshift lokal + matje në UI.
3. Harness 20 pyetje-etalon mbi korpusin real (bazë para ndryshimeve).
4. Video 1–4 min + slide deck + README dorëzimi.

## Lidhje
- Plani i plotë: ~/.openclaw/workspace/memory/plans/2026-10-22-dy-garat-plani-i-plote.md
- Faqja e eventit: https://hackathon.genai.works/event/open-agent-hackathon-2026
