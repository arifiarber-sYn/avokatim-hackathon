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

A two-sided legal platform:

1. **For lawyers** — practice management that lets **one lawyer work with the
   capacity of a whole firm**: case intake → digital matter files → deadlines →
   documents → AI assistance → billing → client portal.
2. **For citizens** — a free "pocket lawyer" (`/`, `/ava`, `/avokatet`,
   `/posto-rastin`, `/rasti-im`): public Ava (legal information with article
   citations, rate-limited), lawyer directory, case marketplace (citizens post,
   lawyers claim; identity protected until claim; automatic conflict check),
   and SOS for emergencies (duty roster, push/email to on-duty lawyers,
   LiveKit video calls).

**Revenue model (D-016, never violate):** citizens pay nothing, ever. Lawyers
pay a flat per-seat subscription (default €24/user/month, 90-day trial,
`Tenant.plan_price_eur` overridable, 0 = free forever). The platform **never
takes a percentage of legal fees** and never holds client money. Overdue
platform invoices block only new marketplace claims — never data access.

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
- **Compliance is a feature**: data protection per Kosovo Law 06/L-082
  (consent records, erasure/anonymization, retention review, data export,
  external-AI kill switch) and AML per Law 05/L-096 (KYC on contacts, source
  of funds, checklist + suspicion reports). Compliance rules live as data and
  explicit records, never hidden logic (see DECISIONS D-011).

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
| `backend/app/models/` | DB models: tenancy, matters, documents, billing, assistant, audit, jurisdiction, marketplace (citizens/cases), platform_billing (subscription invoices) |
| `backend/app/api/` | REST routers, all mounted under `/api` |
| `backend/app/services/` | Business logic: deadlines engine, conflicts check, RAG, assistant, storage, platform_billing (subscription invoices + dunning loop), livekit (call tokens) |
| `backend/app/llm/` | LLM provider abstraction: `base.py` → `deepseek.py`, `local.py`, `router.py` |
| `backend/app/seeds/` | Jurisdiction data (Kosovo deadline rules, holidays, fee tariff, templates, AML indicators) |
| `backend/alembic/versions/` | DB migrations — append-only, never edit old ones |
| `backend/tests/` | pytest suite |
| `frontend/` | Next.js + TypeScript + Tailwind (see `frontend/AGENTS.md` for Next.js caveats) |
| `frontend/src/app/(app)/` | Lawyer pages: dashboard, intake, matters, calendar, contacts, templates, assistant, billing, marketplace, reports, settings, platform (superadmin) |
| `frontend/src/app/` (public) | Citizen pages: `/` (landing), `ava`, `avokatet`, `posto-rastin`, `rasti-im`, `per-avokatet` (lawyer marketing), `portal` (client portal) — wrapped in `components/public-shell.tsx`; per-page explainers via `components/page-intro.tsx` |
| `frontend/src/lib/` | `api.ts` (API client), `types.ts`, `i18n.tsx`, `dictionaries.ts` (sq/sr/tr/bs/en/zh), `legal.ts` (ToS/Privacy texts) |
| `data/` | Runtime data: encrypted documents, legal corpus, logs — **git-ignored, never delete** |
| `docs/agents/` | Agent management system (state, journal, decisions, roadmap) |
| `docker-compose.yml` | Postgres 17 + pgvector (port 5433), Redis (6380), Caddy (8443 HTTPS), LiveKit (7880/7881/7882, SOS calls) |

Key config: `backend/app/config.py` — every setting is overridable via `backend/.env`.

## 4. Running, testing, deploying

The project lives at `~/AvokatIM` (a compat symlink `~/BoraLaw` points there).
The stack runs on this machine via **systemd user services** (start on boot):

```bash
systemctl --user status avokatim     # status
systemctl --user restart avokatim    # restart everything
./start.sh                          # manual start (same thing)
./stop.sh                           # stop backend, frontend, containers
```

Related units: `avokatim-tunnel.service` (Cloudflare Tunnel for the public
domain; the tunnel's internal name on Cloudflare is still `boralaw` — leave it)
and `avokatim-backup.timer` (daily encrypted backup at 03:00 →
`~/AvokatIMBackups`, key at `~/.config/avokatim/backup.key`).

URLs: public https://avokatiim.ai · local http://127.0.0.1:3000 ·
LAN https://<machine-ip>:8443 · API http://127.0.0.1:8000/api
(the old domain boraarifi.ai serves only a static parking page)

- Health check: `curl http://127.0.0.1:8000/api/health` → `{"status":"ok","app":"AvokatIM"}`
- Logs: `data/backend.log`, `data/frontend.log`
- Backend tests: `cd backend && .venv/bin/python -m pytest tests/ -q`
- End-to-end simulation (lawyer + citizen + billing flows, ~130 checks against
  the live stack): `cd backend && .venv/bin/python scripts/full_simulation.py`
- New migration: `cd backend && .venv/bin/alembic revision --autogenerate -m "..."`
  then `.venv/bin/alembic upgrade head`

**IMPORTANT — frontend builds:** `start.sh` rebuilds the frontend automatically
when anything under `frontend/src`/`public` is newer than `.next/BUILD_ID`, and
kills the stale `next-server` first. So after changing frontend code:

```bash
systemctl --user restart avokatim
```

(or run `cd frontend && npm run build` yourself first if you want to see build
errors directly).

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
