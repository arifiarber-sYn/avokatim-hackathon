# AvokatIM — Agent Operating Manual

> Ky skedar është udhëzuesi kryesor për çdo agjent AI që punon në këtë projekt.
> This file is the entry point for ANY AI agent or LLM working on this project,
> regardless of vendor or tool. Read it fully before making changes.

## How the agent layer works (vendor-agnostic by design)

The owner must be able to swap the coding agent (Cursor, Claude Code, Codex,
Gemini CLI, ...) and the underlying LLM at any time without losing anything.
Three rules make that possible:

1. **`AGENTS.md` is the single source of truth** (the cross-vendor standard
   most tools read natively). Tools that expect their own file get a one-line
   pointer instead of a copy: `CLAUDE.md`, `GEMINI.md`,
   `.github/copilot-instructions.md` all say "read AGENTS.md". Never duplicate
   content into a pointer file; if a new tool needs its own filename, add
   another pointer.
2. **All durable knowledge lives in the repo**, in `docs/agents/` — never only
   in a vendor's chat history, memory feature, or settings. If you learned
   something a future agent will need, write it into STATE / JOURNAL /
   DECISIONS before the session ends.
3. **The app itself is LLM-agnostic too** (D-003): every product LLM call goes
   through `backend/app/llm/` and the provider is chosen by config
   (`backend/.env`), so swapping DeepSeek for a local or other hosted model is
   a config change, not a refactor.

**Reading order when your context window is small** (don't ingest everything):
1. This file (always).
2. `docs/agents/STATE.md` — headline + only the sections your task touches
   (it is long; search it, don't read linearly).
3. Last 2–3 entries of `docs/agents/JOURNAL.md`.
4. `docs/agents/DECISIONS.md` only if you touch architecture — scan titles,
   read the relevant D-numbers.

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

One platform, two sides (the bridge between Kosovo's citizens and lawyers):

1. **For lawyers** — a legal practice management platform that lets **one lawyer
   work with the capacity of a whole firm**: case intake → digital matter files →
   deadlines → documents → AI assistance → billing → client portal.
2. **For citizens** — a free "pocket lawyer": the public assistant **Ava** (cites
   Kosovo law articles, works by voice), a **marketplace** (post a case, verified
   lawyers claim it), **SOS — AI protection by phone** (police-stop scenario:
   voice + encrypted hash-chained evidence recording, duty-lawyer alerts), and
   free tools (deadline calculator, letter/complaint generator) plus a feedback
   channel to the platform (/kontakti).

Revenue model (D-016): citizens never pay; lawyers pay a flat per-seat monthly
subscription after a 365-day trial (first year free — extended from 90 days
on 2026-07-28). Never a percentage of lawyer fees.

- **Jurisdictions**: Kosovo (XK) and Germany (DE) are **active** (DE since
  D-034/D-037: host `de.avokatiim.ai`, trades as **"Ava Legal"** per D-056 —
  brand is data, never hardcode it). GB, CN, INTL are prepared as data.
  Jurisdiction rules (deadlines, holidays, templates, legal corpus) are **data,
  not code** — never hardcode jurisdiction-specific logic.
- **Tenancy**: multi-tenant from the foundation (solo lawyer now, firms later).
- **Languages**: UI in Albanian (sq), Serbian (sr), Turkish (tr), Bosnian (bs),
 English (en), Chinese (zh), German (de). Every new UI string must be added to
 **all seven** in `frontend/src/lib/dictionaries.ts`. Server-generated client
 communications (emails, SMS, invoice PDF) are localized via
 `backend/app/i18n.py` using `Contact.locale` → tenant default → sq.
- **Privacy**: client documents are encrypted at rest and indexed with **local**
  embeddings — document text must never leave this machine for indexing.
- **Compliance is a feature**: data protection per Kosovo Law 06/L-082
  (consent records, erasure/anonymization, retention review, data export,
  external-AI kill switch) and AML per Law 05/L-096 (KYC on contacts, source
  of funds, checklist + suspicion reports). Compliance rules live as data and
  explicit records, never hidden logic (see DECISIONS D-011).

## 1b. German market capture (DE) — active campaign

Germany is not just a second jurisdiction; it is an **active market-capture
campaign** running on two parallel tracks. Any agent touching DE pricing,
marketing or pitch material MUST read
`docs/pitch/strategjia-tregu-gjerman.txt` (full strategy, Albanian) first.

- **Product**: full German parity is live — RVG billing, ZPO/ArbGG/VwGO
  deadlines, ZUGFeRD/XRechnung + DATEV export, Mahnwesen with EDA export
  (Beta), German corpus (federal law + 16k+ decisions, nightly imports),
  migration wizard with RA-MICRO/Advoware presets, Outlook add-in,
  telephony-KI. Pricing: 39 €/user/month after 3 months free (D-057).
- **Track A — sell/license the platform** to German legal-tech companies:
  the complete fixed-price offer (4 options: OEM / white-label DACH /
  DACH acquisition / global acquisition) lives in
  `docs/pitch/ava-legal-platform-offer.txt` (EN) and `...-offer-de.txt` (DE).
  Prices in those documents are FINAL floor prices (decision 2026-08-05):
  never lower them further; if traction grows, they go UP on renewal.
  `docs/pitch/qmimet-dyshemete-interne.txt` is internal-only — never share.
- **Track B — direct pilot acquisition** of German lawyers/firms:
  "Gründungspartner" program (first 5 firms: 12 months free + free
  migration + price locked at 39 €), starting with the Albanian-German
  legal diaspora. Cold B2B email in Germany is restricted (UWG §7) —
  prefer referrals, LinkedIn/XING, physical letters, events.
- **Kosovo is never for sale** in any Track A option except the global one
  (and there only with a perpetual royalty-free license-back).

## 2. Session protocol (MANDATORY)

**At the start of every session:**
1. Read `docs/agents/STATE.md` — current state of the project.
2. Read the last 2–3 entries of `docs/agents/JOURNAL.md` — recent work.
3. If your task touches architecture, skim `docs/agents/DECISIONS.md`.
4. Before proposing to remove/replace anything, check `docs/agents/LESSONS.md`.
   Unsure which file covers your task? Route via `docs/agents/INDEX.md`.

**At the end of every session (or after completing a significant task):**
1. Append an entry to `docs/agents/JOURNAL.md` (format is described there).
2. Update `docs/agents/STATE.md` if the state changed (new module, new dependency,
   changed behavior, known issues).
3. Record any architectural decision in `docs/agents/DECISIONS.md`.
4. If you added/changed any outbound email or operator notification, update
   `docs/agents/COMMS.md` (see §4b).
5. Commit your work to git (see §6). Never leave finished work uncommitted.

## 3. Architecture map

| Path | What it is |
|---|---|
| `backend/` | Python 3 / FastAPI / SQLAlchemy 2 async / Alembic |
| `backend/app/models/` | DB models: tenancy, matters, documents, billing, assistant, audit, jurisdiction, marketplace (citizens/cases/bookings), evidence, platform billing, feedback |
| `backend/app/api/` | REST routers, all mounted under `/api` |
| `backend/app/services/` | Business logic: deadlines engine, conflicts check, RAG, assistant, storage |
| `backend/app/llm/` | LLM provider abstraction: `base.py` → `deepseek.py`, `local.py`, `router.py` |
| `backend/app/seeds/` | Jurisdiction data (Kosovo deadline rules, holidays, fee tariff, templates, AML indicators, citizen letter/complaint templates) |
| `backend/alembic/versions/` | DB migrations — append-only, never edit old ones |
| `backend/tests/` | pytest suite |
| `frontend/` | Next.js + TypeScript + Tailwind (see `frontend/AGENTS.md` for Next.js caveats) |
| `frontend/src/app/(app)/` | Lawyer pages: dashboard, intake, matters, calendar, contacts, templates, assistant, billing, reports, settings, marketplace, platform |
| `frontend/src/app/` (top level) | Public citizen pages: `/` (landing), `/ava`, `/avokatet`, `/posto-rastin`, `/rasti-im` (+SOS), `/afatet`, `/dokumentet`, `/kontakti`, `/per-avokatet` — all wrapped in `PublicShell` (shared header/footer/bottom-nav) |
| `frontend/src/lib/` | `api.ts` (API client), `types.ts`, `i18n.tsx`, `dictionaries.ts` (sq/sr/tr/bs/en/zh), `legal.ts` (ToS/Privacy texts) |
| `data/` | Runtime data: encrypted documents, legal corpus, logs — **git-ignored, never delete** |
| `docs/agents/` | Agent management system (state, journal, decisions, roadmap) |
| `docker-compose.yml` | Postgres 17 + pgvector (port 5433), Redis (6380), Caddy (8443 HTTPS), LiveKit (7880/7881/7882, SOS calls) |

Key config: `backend/app/config.py` — every setting is overridable via `backend/.env`.

## 4. Running, testing, deploying

The project lives at `~/AvokatIM` (a compat symlink `~/BoraLaw` points there).
The stack runs on this machine via **systemd user services** (start on boot):

```bash
systemctl --user status avokatim              # backend status
systemctl --user restart avokatim             # backend + containers ONLY
systemctl --user restart avokatim-frontend    # frontend (rebuilds if src changed)
./start.sh                                    # manual full start (fallback)
./stop.sh                                     # stop backend, frontend, containers
```

**The frontend is a separate unit** (`avokatim-frontend.service`): restarting
`avokatim` does NOT deploy UI changes (LESSONS #4).

Related units: `avokatim-tunnel.service` (Cloudflare Tunnel for the public
domain; the tunnel's internal name on Cloudflare is still `boralaw` — leave it),
`avokatim-backup.timer` (daily encrypted backup at 03:00 → `~/AvokatIMBackups`,
key at `~/.config/avokatim/backup.key`) and `avokatim-outreach.timer` (daily
09:30, `Persistent=true`: 30 personalized recruitment emails/day to OAK
lawyers, then ONK notaries — script `backend/scripts/oak_outreach_campaign.py`,
log `data/outreach.log`, dedup `data/oak_outreach_log.csv`).

URLs: public https://avokatiim.ai · local http://127.0.0.1:3000 ·
LAN https://<machine-ip>:8443 · API http://127.0.0.1:8000/api ·
analytics https://stats.avokatiim.ai (self-hosted Umami container)
(the old domain boraarifi.ai serves only a static parking page)

- Health check: `curl http://127.0.0.1:8000/api/health` → `{"status":"ok","app":"AvokatIM"}`
- Logs: `data/backend.log`, `data/frontend.log`
- Backend tests: `cd backend && .venv/bin/python -m pytest tests/ -q`
- New migration: `cd backend && .venv/bin/alembic revision --autogenerate -m "..."`
  then `.venv/bin/alembic upgrade head`

**Verification playbook** (run what matches your change, against the live stack):

| Suite | When | Command (from `backend/`) |
|---|---|---|
| Unit tests | always | `.venv/bin/python -m pytest tests/ -q` |
| Full E2E simulation | marketplace / citizen / billing / Ava changes | `.venv/bin/python scripts/full_simulation.py` |
| Notary E2E | notary/booking changes | `.venv/bin/python scripts/notary_simulation.py` |
| Tenant isolation | auth/tenancy/permissions changes | `.venv/bin/python scripts/isolation_check.py` |
| SaaS lifecycle | signup/trial/billing/invite changes | `.venv/bin/python scripts/saas_check.py` |

Simulations create throwaway tenants and clean up after themselves; their email
addresses are suppressed (`_is_test_recipient` in `services/notifications.py`) —
keep new test identities matching those patterns or bounces hit the owner's inbox.

**IMPORTANT — frontend builds:** after changing frontend code, deploy with:

```bash
cd frontend && npm run build && systemctl --user restart avokatim-frontend
```

Then verify an asset actually loads (stale-server incidents: LESSONS #3, #4):

```bash
curl -s http://127.0.0.1:3000/ | rg -o '/_next/static/[^"]+' | head -1  # → curl it, expect 200
```

Bump `CACHE` in `frontend/public/sw.js` on UI overhauls (PWA caches
`/_next/static` cache-first and Turbopack chunk names are not content-hashed).

## 4b. Communication layer (emails + operator assistant)

All outbound communication is mapped in **`docs/agents/COMMS.md`** — read it
before touching anything that emails users. The short version:

- **Lane A (automatic)**: the system itself welcomes, thanks, reminds and
  invoices — every successful registration (lawyer/notary verified, citizen
  confirmed) gets a warm thank-you letter with no human involvement.
- **Lane B (Halim)**: the OpenClaw operator assistant handles inbound human
  email — drafts a final reply, asks the owner only **PO/JO** on Telegram,
  sends on "PO". The owner never composes routine mail.
- If you add or change an outbound email: all 7 languages in
  `backend/app/i18n.py`, test-recipient suppression, a row in COMMS.md, and a
  `notify_ops` event when operationally relevant — in the same commit.

## 5. Hard rules

1. **Never commit secrets.** `backend/.env` holds the DeepSeek API key, DB password,
   document encryption key. It is git-ignored — keep it that way.
2. **Never delete or rewrite `data/`** — it contains encrypted client documents.
3. **Migrations are append-only.** Never edit an applied Alembic revision; create a new one.
4. **Jurisdiction logic is data.** New rules go in `backend/app/seeds/`, not in service code.
5. **Every UI string in 7 languages** (sq/sr/tr/bs/en/zh/de) in `dictionaries.ts`. Default locale is sq (de on the DE host). Backend client-facing strings go in `backend/app/i18n.py`, also in all 7.
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
| `docs/agents/INDEX.md` | Documentation router — the layer at a glance + task routing |
| `docs/agents/STATE.md` | Current snapshot: what exists, what works, environment |
| `docs/agents/LESSONS.md` | Settled operational lessons + incidents — check before proposing changes |
| `docs/agents/UPDATE-PROTOCOL.md` | Write-side procedure after any change |
| `docs/agents/COMMS.md` | Communication layer: every automated email + Halim's correspondence protocol |
| `docs/agents/JOURNAL.md` | Chronological work log of all agent sessions |
| `docs/agents/DECISIONS.md` | Architectural decisions and their reasons |
| `docs/agents/ROADMAP.md` | Vision, phases, backlog — what to build next |
| `README.md` | User-facing overview (in Albanian) |
| `frontend/AGENTS.md` | Next.js version caveats — read before frontend work |
| `docs/integrimet/` | Integration research: e-Kosova, e-notary, WhatsApp |
| `docs/legal/` | Platform legal docs: ToS, privacy, AML policy, DPA, SLA |
| `docs/pitch/` · `docs/rekrutimi/` | Sales/presentation texts · OAK/ONK outreach drafts |
