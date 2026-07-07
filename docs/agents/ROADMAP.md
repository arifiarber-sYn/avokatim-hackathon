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
- [x] Email/notification channel for approaching deadlines ✅ (2026-07-07):
      hourly reminder loop mails responsible lawyer per remind_days_before,
      Redis-deduped. Needs SMTP_* in backend/.env to activate.
- [x] Dashboard upgrade P1 ✅ (2026-07-07): "Today" agenda, A/R aging buckets,
      6-month worked-hours + billed-revenue trend, global quick timer in sidebar.
- [x] Dashboard upgrade P2 ✅ (2026-07-07): /reports analytics page with
      utilization, realization, collection, intake funnel by source,
      profitability by practice area; hours target in Settings.
- [ ] Public domain + real TLS certificate (Caddy handles it automatically once a
      domain points here) instead of self-signed on :8443.

## Phase 3 — Multi-lawyer / law firms

- [x] Multi-user + roles (admin/lawyer/staff) inside a tenant ✅ (2026-07-07):
      Settings → Team (add member, change role, deactivate); matter assignment
      via responsible lawyer select on the matter Overview.
- [ ] Finer permissions (per-matter visibility, review steps, internal workflow).
- [ ] Firm-level reporting (per-lawyer utilization on /reports).

## Competitive gaps (from 2026-07-07 full-app analysis vs Clio/Smokeball/MyCase)

Priority before the law-firm pilot:
- [x] AI deadline extraction from court documents ✅ (2026-07-07): button on any
      document with text → Bora proposes deadlines (date, legal basis,
      confidence), lawyer accepts selected ones.
- [x] Calendar sync via ICS subscription feed ✅ (2026-07-07): signed-token URL
      in Settings, works with Google/Outlook/phone.

Base competitiveness:
- [x] E-signature flow in client portal ✅ (2026-07-07): typed-name signature
      bound to document SHA-256 + IP + timestamp, audit-logged. Qualified
      eIDAS/Kosovo e-signature law compliance still future work.
- [x] Client portal v2 ✅ (2026-07-07): full portal UI at /portal — login,
      matters, two-way messages per matter, signature inbox.
- [x] AI-drafted client status updates ✅ (2026-07-07): button on matter AI tab,
      send straight to portal messages or copy.

Long-term differentiation:
- [ ] Kosovo template library built with the pilot firm (our answer to
      Smokeball's 20k form library — nobody has this for XK).
- [ ] Local payment tracking (payment reference + status; local processor later).
- [x] PWA ✅ (2026-07-07): manifest + icons, installable. Push notifications for
      deadlines still open (needs service worker + web-push).
- [x] Public intake form link ✅ (2026-07-07): /apliko/{token} public page,
      feeds intake funnel with source=web; link in Settings.

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
