# CHANGELOG

## 2026-10-24 — hackathon(open-agent): B3 — gjurmë arsyetimi në UI (klik → burimi)
- Shtuar `frontend/src/components/reasoning-trace.tsx`: `buildReasoningTrace()` + panel i mbyllur «Gjurmë arsyetimi» (pyetje → kërkim → burime → verifikim → përfundim).
- `/assistant`: ruhen nënpyetjet e deep-research për çdo përgjigje; rreshtat e verifikimit me `doc_id` hapin `CitationSourceModal` (i njëjti modal i badge-ve).
- Pa ndryshime backend/DB: burimet vijnë nga `citations` + eventet `step` / `citation_check`.
- Prova: `tsc --noEmit` 0 gabime; eslint — vetëm gabimi i vjetër `set-state-in-effect` (rreshti 63).

## 2026-10-23 — hackathon(open-agent): B2 — kosto Meterless + usage në UI
- meterless.py: `cost_of()` (USD/1M token), `Usage.cost_usd`, `summarize()` mbi usage.jsonl (rreshtat e korruptuar numërohen).
- Shtuar `GET /api/hackathon/usage` (app/api/hackathon.py), vetëm lexim + auth.
- Shtuar `frontend/src/components/meterless-cost.tsx` në /assistant: thirrje, token, kosto, «dokumentet nuk dolën nga makina»; fshihet kur log-u është bosh.
- demo_integrated.py: shtyp ms/token/kosto (më parë `latency_ms` → «?»).
- Prova: `PYTHONPATH=. pytest tests/test_meterless_usage.py tests/test_adapters_contract.py -q` → 11 passed.

## 2026-10-22 — hackathon(open-agent): adapter layer
- Shtuar backend/app/adapters/ (base, zetaris, meterless) — kontratë e re, e fikshme.
- Shtuar backend/tests/test_adapters_contract.py (5 teste, të gjelbra).
- config: hackathon_mode + zetaris_* + meterless_* (default off).
- Dokumentim: docs/agents/HACKATHON-OPEN-AGENT.md

## 2026-10-23 — hackathon(open-agent): testet e korpusit + Makefile
- Shtuar tests/test_corpus_contract.py — 5 teste offline (manifest, hash, lidhja vendim-OCDS, refuzimi).
- Shtuar Makefile — test / corpus-check / corpus-size / demo.
- Prova: 5 passed; korpusi K-a 56 MB, 53 hash OK.

## 2026-10-23 — hackathon(open-agent): demo offline + teste
- Shtuar backend/hackathon/demo_corpus.py — demo pa DB/LLM/rrjet mbi korpusin K-a (vendim -> OCDS -> ligj).
- Shtuar tests/test_demo_corpus.py — 2 teste; gjithsej 7 passed.
- Shtuar target `make demo-offline`.
- Dokumentuar defekti i burimit: Vendimi-1292-25.pdf identik me Vendimi_2025-1289.pdf.

## 2026-10-23 — hackathon(open-agent): video demo offline (50s)
- Shtuar docs/hackathon/video/demo-offline-2026-10-23.mp4 (6 skena, 50.5s, 663 KB).
- Zë espeak sq; ndërtim me ffmpeg/magick; pa DB dhe pa rrjet.

## 2026-10-23 — hackathon(open-agent): demo i integruar (Zetaris + Meterless)
- Shtuar backend/hackathon/demo_integrated.py — rend i deklaruar: Zetaris → korpus → Meterless.
- Shtuar `make demo-integrated`.
- Prova: Zetaris SELECT 1 OK; 0 datasource (metastore.datasource); Meterless i padisponueshem.
