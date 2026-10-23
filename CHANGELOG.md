# CHANGELOG

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
