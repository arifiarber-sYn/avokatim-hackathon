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

- [x] Backups ✅ (2026-07-07): `backup.sh` + daily systemd timer, AES-256
      encrypted, retention 14, restore-tested. Key must be copied off-machine.
- [x] Real legal corpus ✅ (2026-07-08): 9 laws (~4,000 article chunks) loaded
      from Gazeta Zyrtare via `backend/scripts/import_gzk.py`; RAG citation
      quality verified on real questions (LPK appeals, Labor Law leave).
      More laws: extend the script's LAWS list and re-run.
- [x] Verify OCR end-to-end on host ✅ (2026-07-07): tesseract 5.5.2 +
      sqi/eng/chi_sim installed; synthetic Albanian scanned image and image-only
      PDF both OCR correctly (diacritics ë/ç intact).
- [ ] Local LLM option in production: configure Ollama/vLLM endpoint, quality-test
      "Bora" against DeepSeek on Albanian legal questions. (Checked 2026-07-07:
      ollama binary present but no models/service and no GPU tooling on host —
      CPU inference would be slow; needs owner decision on model/hardware.)
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
- [x] Finer permissions ✅ (2026-07-08): per-matter visibility (`restricted` +
      matter members, enforced across list/deadlines/ICS/agenda) and document
      approval workflow (draft → review by partner → approved/changes requested).
- [x] Data migration importer ✅ (2026-07-08): CSV import for contacts and
      matters in Settings, with downloadable templates.
- [x] Fiscal invoices ✅ (2026-07-08): firm NUI/VAT/address in Settings,
      default VAT 18% applied to invoices (vat_amount/total_with_vat shown).
- [x] Firm-level reporting ✅ (2026-07-07): per-lawyer table on /reports (open
      matters, MTD billable hours vs target, utilization); shows when >1 member.

## Competitive gaps (from 2026-07-07 full-app analysis vs Clio/Smokeball/MyCase)

Priority before the law-firm pilot:
- [x] AI deadline extraction from court documents ✅ (2026-07-07): button on any
      document with text → Bora proposes deadlines (date, legal basis,
      confidence), lawyer accepts selected ones.
- [x] Calendar sync via ICS subscription feed ✅ (2026-07-07): signed-token URL
      in Settings, works with Google/Outlook/phone.

Base competitiveness:
- [x] E-signature flow in client portal ✅ (2026-07-07): typed-name signature
      bound to document SHA-256 + IP + timestamp, audit-logged.
      ✅ (2026-07-08) Certificate of Completion PDF per signed document.
      Qualified signatures (Law 08/L-022 art. 32): integrate a licensed QTSP
      (Evrotrust or rTrust) — researched, see DECISIONS D-007; next phase.
- [x] Client portal v2 ✅ (2026-07-07): full portal UI at /portal — login,
      matters, two-way messages per matter, signature inbox.
- [x] AI-drafted client status updates ✅ (2026-07-07): button on matter AI tab,
      send straight to portal messages or copy.

Long-term differentiation:
- [~] Kosovo template library: 12 practice templates seeded (2026-07-08) —
      lawsuits (civil/labor/administrative), objection, appeal, PoA, demand
      letter, NDA, service + employment contracts, legal opinion, DD checklist.
      Still to grow with the pilot firm's own precedents (our answer to
      Smokeball's 20k form library — nobody has this for XK).
- [x] Local payment tracking ✅ (2026-07-07): paid_on + payment_reference on
      invoices, entered when marking paid. (Local processor integration later.)
- [x] PWA ✅ (2026-07-07): manifest + icons, installable. Push notifications ✅
      same day: service worker + VAPID web-push, per-device opt-in in Settings,
      wired into the deadline reminder loop.
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
