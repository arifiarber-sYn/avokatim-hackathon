# ROADMAP — vision, phases, backlog

> The owner decides priorities; agents propose. Keep this current: move items to
> "Done" (with date) or into STATE.md when completed.

## Vision

A platform where one lawyer works with the capacity of a whole firm — from case
intake to full processing, eventually assisting in court itself. Built for Bora's
future as a modern lawyer. Target: competitive with the global legal-tech
standard, multi-jurisdictional (XK active; GB, CN, INTL prepared).

## Phase 1 — Solo lawyer MVP  ✅ (2026-07-06)

Everything in STATE.md "What exists and works".

## Phase 2 — Hardening & daily-use polish (current)

- [ ] Backups: automated encrypted backup of Postgres + `data/documents`
      (deadline data and client files must survive disk failure).
- [ ] Real legal corpus: load actual Kosovo laws from Gazeta Zyrtare and verify
      RAG citation quality on real questions.
- [ ] Verify OCR end-to-end on host (tesseract langpacks) with scanned Albanian documents.
- [ ] Local LLM option in production: configure Ollama/vLLM endpoint, quality-test
      "Bora" against DeepSeek on Albanian legal questions.
- [ ] Email/notification channel for approaching deadlines (currently UI-only).
- [ ] Public domain + real TLS certificate (Caddy handles it automatically once a
      domain points here) instead of self-signed on :8443.

## Phase 3 — Multi-lawyer / law firms

- [ ] Roles & permissions inside a tenant (partner, associate, paralegal, admin).
- [ ] Assignment & internal workflow (who works the matter, review steps).
- [ ] Firm-level reporting.

## Phase 4 — More jurisdictions

- [ ] GB seeds (deadline rules, holidays, templates, corpus).
- [ ] CN seeds; INTL (arbitration etc.).
- [ ] Per-jurisdiction template/document language handling.

## Phase 5 — Courtroom assistance (long-term goal)

- [ ] Hearing preparation packs: chronology, arguments, counterargument prediction
      with citations.
- [ ] Live/session assistance mode (fast retrieval over the matter + corpus,
      possibly voice; must work with a local LLM for confidentiality).

## Ideas parking lot

- Client intake form shared as a public link.
- Court calendar/e-filing integrations where Kosovo infrastructure allows.
- Fine-tuned Albanian legal embedding model when corpus is large enough.
