# STATE — current project snapshot

> Update this file whenever the state changes (new module, dependency, behavior,
> known issue). Keep it a snapshot, not a history — history lives in JOURNAL.md.

**Last updated:** 2026-07-06

## Status: MVP built and running

All core modules exist end-to-end (API + UI) and the stack runs on this machine.

## What exists and works

- **Auth**: registration (first run creates the lawyer account), JWT login, 2FA (TOTP).
- **Intake**: new case registration, automatic conflict-of-interest check, AI classification.
- **Matters**: digital case file — parties, documents, deadlines, notes, history.
- **Deadline engine**: Kosovo procedural rules (LPK, KPPRK, LKA) seeded as data,
  automatic calculation with official holidays. Tests in `test_deadline_engine.py`.
- **Documents**: encrypted storage (Fernet), versioning, text extraction + OCR,
  semantic indexing (pgvector + local embeddings).
- **Templates**: lawsuit/appeal/authorization documents auto-filled from matter data.
- **Assistant "Bora"**: RAG over legal corpus + matter documents, with citations.
  Providers: DeepSeek (default) or local OpenAI-compatible (Ollama/vLLM), selectable per request.
- **Corpus**: upload laws via Settings → Legal base; auto-chunked by article ("Neni X").
- **Billing**: time entries, invoices generated from unbilled hours.
- **Client portal**: client sees case status and upcoming hearings.
- **Dashboard**: workload, week's deadlines, finances.
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
- Single Alembic migration so far (`20260706_..._initial_schema`); DB can be
  recreated from scratch if ever needed (data loss only affects local dev data).
- Caddy serves a self-signed cert on :8443 (browser warning is expected on LAN).
- OCR system binary (tesseract) not confirmed installed on host.

## Jurisdictions

- **XK (Kosovo): active** — deadline rules, holidays, templates seeded.
- GB, CN, INTL: schema-ready, no data yet.
