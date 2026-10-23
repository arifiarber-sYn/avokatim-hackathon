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
