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
- **Email reminders**: background loop (hourly) mails the responsible lawyer at
  each deadline's `remind_days_before` offsets; deduped via Redis. Disabled until
  SMTP_* is set in `backend/.env`.
- **Dashboard**: workload, week's deadlines, finances. **/reports**: analytics.
- **PWA**: manifest + icons; installable on phone (add-to-home-screen).
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
  System tesseract may still need: `sudo dnf install tesseract tesseract-langpack-sqi
  tesseract-langpack-eng tesseract-langpack-chi_sim` (verify before relying on OCR).

## Known issues / caveats

- `start.sh` skips `npm run build` when `frontend/.next` exists — rebuild manually
  after frontend changes (see AGENTS.md §4).
- SMTP not configured yet — deadline email reminders stay disabled (loop logs
  "SMTP not configured" and exits). Set SMTP_HOST/PORT/USER/PASSWORD/FROM in
  `backend/.env` to enable.
- E-signature is the simple flow (typed name + SHA-256 + audit); qualified
  eIDAS/Kosovo e-signature law compliance is future work.
- `PUBLIC_BASE_URL` (backend/.env, default http://127.0.0.1:3000) is used in
  calendar-feed and public-intake links — set it when the app gets a real domain.
- Caddy serves a self-signed cert on :8443 (browser warning is expected on LAN).
- OCR system binary (tesseract) not confirmed installed on host.

## Jurisdictions

- **XK (Kosovo): active** — deadline rules, holidays, templates seeded.
- GB, CN, INTL: schema-ready, no data yet.
