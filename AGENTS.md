# AvokatIM — Agent Operating Manual

> Ky skedar është udhëzuesi kryesor për çdo agjent AI që punon në këtë projekt.
> This file is the entry point for ANY AI agent or LLM working on this project,
> regardless of vendor or tool. Read it fully before making changes.

## 0. Who you are working for

- The owner is a solo developer building this as his own legal-tech product,
  **AvokatIM**. Treat the project with care — it is aimed at real, paying law firms.
- Historical note: the project was called "BoraLaw" and the assistant "Bora"
  until 2026-07-11; it was fully rebranded to AvokatIM (assistant: "Ava") to
  avoid any conflict of interest. Do not reintroduce the old names.
- **Always communicate with the owner in Albanian.** Code, comments, commits and
  these agent docs stay in English so any LLM can work with them.
- The owner values a competitive, industry-standard product over speed or cost.

## 1. What AvokatIM is

A legal practice management platform that lets **one lawyer work with the capacity
of a whole firm**: case intake → digital matter files → deadlines → documents →
AI assistance → billing → client portal.

- **Jurisdictions**: Kosovo (XK) is active. GB, CN, INTL are prepared as data.
  Jurisdiction rules (deadlines, holidays, templates, legal corpus) are **data,
  not code** — never hardcode jurisdiction-specific logic.
- **Tenancy**: multi-tenant from the foundation (solo lawyer now, firms later).
- **Languages**: UI in Albanian (sq), Serbian (sr), Turkish (tr), Bosnian (bs),
 English (en), Chinese (zh) — Kosovo's official languages (Law 02/L-37) plus
 extras. Every new UI string must be added to **all six** in
 `frontend/src/lib/dictionaries.ts`. Server-generated client communications
 (emails, SMS, invoice PDF) are localized via `backend/app/i18n.py` using
 `Contact.locale` → tenant default → sq.
- **Privacy**: client documents are encrypted at rest and indexed with **local**
  embeddings — document text must never leave this machine for indexing.

## 2. Session protocol (MANDATORY)

**At the start of every session:**
1. Read `docs/agents/STATE.md` — current state of the project.
2. Read the last 2–3 entries of `docs/agents/JOURNAL.md` — recent work.
3. If your task touches architecture, skim `docs/agents/DECISIONS.md`.

**At the end of every session (or after completing a significant task):**
1. Append an entry to `docs/agents/JOURNAL.md` (format is described there).
2. Update `docs/agents/STATE.md` if the state changed (new module, new dependency,
   changed behavior, known issues).
3. Record any architectural decision in `docs/agents/DECISIONS.md`.
4. Commit your work to git (see §6). Never leave finished work uncommitted.

## 3. Architecture map

| Path | What it is |
|---|---|
| `backend/` | Python 3 / FastAPI / SQLAlchemy 2 async / Alembic |
| `backend/app/models/` | DB models: tenancy, matters, documents, billing, assistant, audit, jurisdiction |
| `backend/app/api/` | REST routers, all mounted under `/api` |
| `backend/app/services/` | Business logic: deadlines engine, conflicts check, RAG, assistant, storage |
| `backend/app/llm/` | LLM provider abstraction: `base.py` → `deepseek.py`, `local.py`, `router.py` |
| `backend/app/seeds/` | Jurisdiction data (Kosovo deadline rules, holidays, templates) |
| `backend/alembic/versions/` | DB migrations — append-only, never edit old ones |
| `backend/tests/` | pytest suite |
| `frontend/` | Next.js + TypeScript + Tailwind (see `frontend/AGENTS.md` for Next.js caveats) |
| `frontend/src/app/(app)/` | Pages: dashboard, intake, matters, calendar, contacts, templates, assistant, billing, settings |
| `frontend/src/lib/` | `api.ts` (API client), `types.ts`, `i18n.tsx`, `dictionaries.ts` (sq/en/zh) |
| `data/` | Runtime data: encrypted documents, legal corpus, logs — **git-ignored, never delete** |
| `docs/agents/` | Agent management system (state, journal, decisions, roadmap) |
| `docker-compose.yml` | Postgres 17 + pgvector (port 5433), Redis (6380), Caddy (8443 HTTPS) |

Key config: `backend/app/config.py` — every setting is overridable via `backend/.env`.

## 4. Running, testing, deploying

The stack runs on this machine via a **systemd user service** (starts on boot):

```bash
systemctl --user status avokatim     # status
systemctl --user restart avokatim    # restart everything
./start.sh                          # manual start (same thing)
./stop.sh                           # stop backend, frontend, containers
```

URLs: local http://127.0.0.1:3000 · LAN https://<machine-ip>:8443 · API http://127.0.0.1:8000/api

- Health check: `curl http://127.0.0.1:8000/api/health` → `{"status":"ok","app":"AvokatIM"}`
- Logs: `data/backend.log`, `data/frontend.log`
- Backend tests: `cd backend && .venv/bin/python -m pytest tests/ -q`
- New migration: `cd backend && .venv/bin/alembic revision --autogenerate -m "..."`
  then `.venv/bin/alembic upgrade head`

**IMPORTANT — frontend builds:** `start.sh` only builds the frontend if
`frontend/.next` is missing. After changing frontend code you MUST rebuild:

```bash
cd frontend && npm run build && systemctl --user restart avokatim
```

## 5. Hard rules

1. **Never commit secrets.** `backend/.env` holds the DeepSeek API key, DB password,
   document encryption key. It is git-ignored — keep it that way.
2. **Never delete or rewrite `data/`** — it contains encrypted client documents.
3. **Migrations are append-only.** Never edit an applied Alembic revision; create a new one.
4. **Jurisdiction logic is data.** New rules go in `backend/app/seeds/`, not in service code.
5. **Every UI string in 6 languages** (sq/sr/tr/bs/en/zh) in `dictionaries.ts`. Default locale is sq. Backend client-facing strings go in `backend/app/i18n.py`, also in all 6.
6. **LLM calls only through the abstraction** in `backend/app/llm/` — never call a
   provider API directly from services. This keeps the app LLM-agnostic.
7. **Local embeddings only** for document/corpus indexing (sentence-transformers).
8. **Audit log**: user-visible actions on matters/documents must write to the audit service.
9. Verify before finishing: tests pass + health endpoint OK + the feature works in the UI.

## 6. Git discipline

- Work is preserved through git. Commit at every meaningful, working checkpoint.
- Message format: short imperative summary, English, e.g.
  `Add deadline engine rules for appeals (LPK art. 176)`.
- Never use `--force`, never rewrite history, never commit `data/` or `.env`.

## 7. Where to find deeper context

| File | Purpose |
|---|---|
| `docs/agents/STATE.md` | Current snapshot: what exists, what works, environment |
| `docs/agents/JOURNAL.md` | Chronological work log of all agent sessions |
| `docs/agents/DECISIONS.md` | Architectural decisions and their reasons |
| `docs/agents/ROADMAP.md` | Vision, phases, backlog — what to build next |
| `README.md` | User-facing overview (in Albanian) |
| `frontend/AGENTS.md` | Next.js version caveats — read before frontend work |
