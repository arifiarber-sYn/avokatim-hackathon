# STATE — current project snapshot

> Update this file whenever the state changes (new module, dependency, behavior,
> known issue). Keep it a snapshot, not a history — history lives in JOURNAL.md.

**Last updated:** 2026-07-07

## Status: MVP built and running + competitive-gap features

All core modules exist end-to-end (API + UI) and the stack runs on this machine.

## What exists and works

- **Auth**: registration (first run creates the lawyer account), JWT login, 2FA (TOTP).
- **Team**: multi-user per tenant with roles (admin/lawyer/staff), managed in
  Settings → Team; matter assignment via `responsible_user_id` (editable in
  matter Overview when >1 member). Adding a member flips tenant kind to "firm".
- **Intake**: new case registration, automatic conflict-of-interest check, AI
  classification, source tracking. **Public intake form** at `/apliko/{token}`
  (tenant token from Settings; submissions arrive with source=web).
- **Matters**: digital case file — parties, documents, deadlines, notes, history,
  **two-way client messages** (Messages tab ↔ portal).
- **Deadline engine**: Kosovo procedural rules (LPK, KPPRK, LKA) seeded as data,
  automatic calculation with official holidays. Tests in `test_deadline_engine.py`.
- **AI deadline extraction**: button on any document with text — Bora proposes
  deadlines (title/date/legal basis/confidence), lawyer reviews and accepts →
  `POST .../extract-deadlines` + `POST .../deadlines/bulk`.
- **Calendar sync**: ICS feed (`/api/calendar/feed.ics?token=...`, signed token,
  URL in Settings) for Google Calendar/Outlook/phone subscriptions.
- **Documents**: encrypted storage (Fernet), versioning, text extraction + OCR,
  semantic indexing (pgvector + local embeddings).
- **E-signature**: lawyer requests signature on a document (Documents tab);
  client signs in portal (typed name bound to document SHA-256, IP + timestamp,
  audit-logged). Status pending/signed/declined shown on both sides.
- **Templates**: lawsuit/appeal/authorization documents auto-filled from matter data.
- **Assistant "Bora"**: RAG over legal corpus + matter documents, with citations.
  Providers: DeepSeek (default) or local OpenAI-compatible (Ollama/vLLM), selectable per request.
  Also: **client-update drafting** (AI tab on matter → send to portal or copy).
- **Corpus**: upload laws via Settings → Legal base; auto-chunked by article ("Neni X").
- **Billing**: time entries, invoices generated from unbilled hours.
- **Client portal**: full UI at `/portal` — login, matters with hearings,
  two-way messages, e-signature inbox.
- **Reminders**: background loop (hourly) notifies the responsible lawyer at
  each deadline's `remind_days_before` offsets; deduped via Redis. Two channels:
  **Web Push** (active — VAPID keys in `backend/.env`, per-device opt-in in
  Settings → Device notifications) and email (active — Gmail SMTP via App
  Password in `backend/.env`, test delivery verified 2026-07-07).
- **Payments**: marking an invoice paid records `paid_on` + optional
  `payment_reference` (bank transaction no.), shown on the invoice card.
- **Dashboard**: workload, week's deadlines, finances. **/reports**: analytics
  incl. **per-lawyer table** (open matters, MTD hours vs target, utilization)
  when the tenant has >1 active member.
- **PWA**: manifest + icons; installable on phone; service worker (`public/sw.js`)
  shows push notifications and opens the matter on tap.
- **Backups**: `backup.sh` — encrypted (AES-256, key at
  `~/.config/boralaw/backup.key`) archive of pg_dump + `data/documents` +
  `backend/.env` into `~/BoraLawBackups/`, retention 14. Daily at 03:00 via
  systemd user timer `boralaw-backup.timer` (enabled). Restore steps in the
  script header. **The key file must also be copied somewhere off-machine.**
- **i18n**: sq / en / zh complete for existing UI.
- **Audit log** on matter/document actions.

## Environment

- Host: owner's Fedora Linux machine; everything runs locally.
- **Autostart**: systemd user service `boralaw.service`
  (`~/.config/systemd/user/boralaw.service`) runs `start.sh` on boot; lingering enabled.
- Containers (restart: unless-stopped): `boralaw-db` (pgvector/pg17, host port 5433),
  `boralaw-redis` (6380), `boralaw-caddy` (host network, HTTPS 8443).
- Backend: uvicorn on 127.0.0.1:8000, venv at `backend/.venv`. Frontend: Next.js on :3000.
- Secrets in `backend/.env` (git-ignored): DeepSeek key, doc encryption key, DB password.
- Optional extras installed in venv: `requirements-ai.txt` (local embeddings, OCR).
- System tesseract 5.5.2 installed (2026-07-07) with sqi/eng/chi_sim langpacks;
  OCR verified end-to-end on synthetic Albanian scanned image and image-only PDF.

## Known issues / caveats

- ~~`start.sh` skips `npm run build`~~ fixed 2026-07-07: `start.sh` now rebuilds
  automatically when any file in `frontend/src`/`public` is newer than
  `.next/BUILD_ID`, and kills the stale `next-server` before starting a fresh one
  (a stale server over a new build serves 404 chunks → blank pages).
- ~~SMTP not configured~~ done 2026-07-07: Gmail App Password in `backend/.env`
  (SMTP_* vars, smtp.gmail.com:587 STARTTLS, from arifi.arber@gmail.com).
  Test email sent and delivered — both reminder channels (email + push) active.
- Host has no GPU tooling (`nvidia-smi` absent) and Ollama has no models/service —
  local-LLM option stays unconfigured; DeepSeek remains the provider. To try
  local: `ollama serve` + `ollama pull qwen3:8b` (CPU will be slow), then set
  `LOCAL_LLM_MODEL=qwen3:8b` in `backend/.env`.
- E-signature is the simple flow (typed name + SHA-256 + audit); qualified
  eIDAS/Kosovo e-signature law compliance is future work.
- `PUBLIC_BASE_URL` (backend/.env, default http://127.0.0.1:3000) is used in
  calendar-feed and public-intake links — set it when the app gets a real domain.
- Caddy serves a self-signed cert on :8443 (browser warning is expected on LAN).

## Jurisdictions

- **XK (Kosovo): active** — deadline rules, holidays, templates seeded.
- GB, CN, INTL: schema-ready, no data yet.
