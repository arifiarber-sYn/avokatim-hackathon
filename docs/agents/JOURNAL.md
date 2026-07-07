# JOURNAL — chronological work log

> Append one entry per session/task, newest at the top. Keep entries short:
> what was done, what was verified, what's left. Format:
>
> ```
> ## YYYY-MM-DD — <short title> (<agent/model if known>)
> - Done: ...
> - Verified: ...
> - Left open / next: ...
> ```

## 2026-07-07 — OCR enabled on host (Cursor / Fable 5)

- Done: installed tesseract 5.5.2 + langpacks sqi/eng/chi_sim (owner provided
  sudo password in chat; not stored anywhere).
- Verified: `storage.extract_text` OCRs a synthetic Albanian scanned image
  (PNG) and an image-only PDF correctly, diacritics intact, status "done".
- Left open: SMTP still waiting on a Gmail App Password from the owner (owner
  offered the real Gmail password — declined and explained App Passwords).

## 2026-07-07 — Remaining backlog: backups, push, payments, firm reporting (Cursor / Fable 5)

- Done: migration `fdb43a0e95bc` (`push_subscriptions`, `invoices.paid_on` +
  `payment_reference`). Web Push end-to-end: VAPID keys generated into
  `backend/.env`, `services/push.py` (pywebpush, dead-sub cleanup), `/api/push/*`
  endpoints, `public/sw.js` service worker, opt-in section in Settings; reminder
  loop now runs when SMTP **or** push is configured and sends both channels.
  Invoices: mark-paid records date + bank reference (form in Billing UI).
  /reports/analytics gained `by_lawyer` (open matters, MTD hours vs target,
  utilization) — table shows when tenant has >1 active member. Encrypted daily
  backups: `backup.sh` (pg_dump + documents + .env, AES-256, retention 14) +
  `boralaw-backup.timer` (03:00, enabled); key at `~/.config/boralaw/backup.key`.
- Verified: 9 tests pass; API roundtrip (invoice paid with TRX ref, by_lawyer
  payload with temp member, push subscribe/unsubscribe) then synthetic data
  removed; backup ran and restore-tested (dump + docs + env decrypt OK);
  frontend built; stack restarted; reminder loop active with push channel.
- Host checks: tesseract NOT installed (sudo needs password — owner action in
  STATE); no GPU tooling, Ollama has no models — local LLM documented, not enabled.
- Left open: SMTP credentials, tesseract install (owner), local-LLM
  model decision, qualified e-signature, per-matter permissions, XK template
  library with pilot firm, real corpus from Gazeta Zyrtare, public domain+TLS.

## 2026-07-07 — Competitive-gap features implemented (Cursor / Fable 5)

- Done: implemented all suggestions from the full-app analysis in one batch.
  Migration `fc080e9898a0`: `matter_messages`, `signature_requests`,
  `tenants.intake_token`. New backend: `/api/team` (multi-user + roles,
  admin/lawyer manage), `/api/calendar/feed.ics` (ICS with signed token),
  `extract-deadlines` + `deadlines/bulk` (AI reads court doc → proposals →
  accept), matter/portal messages, signature request/sign/decline (SHA-256 +
  IP + timestamp, audit), `client-update-draft`, public intake
  (`/api/public/intake/{token}`), reminder loop (`services/notifications.py`,
  SMTP config in `config.py`, Redis dedup). `MatterOut/Update` now carry
  `responsible_user_id`.
- UI: Settings → Team/Calendar sync/Public form sections; matter page →
  Messages tab, responsible-lawyer select, per-document "Extract deadlines" +
  "Request signature", AI tab → client-update draft with send-to-portal;
  new `/portal` (client login, matters, chat, signature inbox); new
  `/apliko/[token]` public form; PWA manifest + generated icons.
- Verified: 9 tests pass; full E2E via API with synthetic data (portal login,
  message roundtrip both directions, sign flow, real DeepSeek extraction —
  found appeal deadline art. LPK + hearing date from a synthetic judgment —
  bulk accept created 2 deadlines, client-update draft in Albanian, ICS shows
  2 events, team member create/deactivate); synthetic data cleaned up;
  frontend built; stack restarted; /portal, /apliko/…, /manifest.webmanifest
  all 200.
- Left open: SMTP credentials (reminders auto-enable once set), push
  notifications for PWA, qualified e-signature, per-matter permissions,
  payment tracking, XK template library with pilot firm.

## 2026-07-07 — Full-app competitor analysis (Cursor / Fable 5)

- Done: researched full 2026 feature sets of Clio (Manage AI, Draft, Grow,
  Accounting), Smokeball (Archie AI, AutoTime, 20k forms) and MyCase (IQ,
  built-in e-sign/SMS). Compared 27 capabilities across 5 areas. Canvas:
  `~/.cursor/projects/home-kllosha-BoraLaw/canvases/krahasimi-i-plote-aplikacionit.canvas.tsx`.
- Scores: Clio 24/27, Smokeball 21.5/27, MyCase 20/27, BoraLaw 16.5/27.
  Our structural advantages nobody matches: XK procedural rules as data,
  RAG with article citations, self-hosting, local-LLM option, sq/en/zh UI.
  Biggest gaps: multi-user roles, e-signature, calendar sync, AI deadline
  extraction from court docs, online payments/messaging in portal.
- Added "Competitive gaps" section to ROADMAP with pilot-blocking priorities.

## 2026-07-07 — Financial analytics P2 implemented (Cursor / Fable 5)

- Done: migration `44cef654e97a` adds `users.billable_hours_target_monthly`
  (default 120) and `intake_requests.source` (referral|web|phone|walk_in|other).
  New `GET /api/reports/analytics`: utilization (MTD billable hours vs target),
  realization (billed/worked hours, 90d), collection (paid/issued value, 180d),
  intake funnel with per-source conversion (90d), profitability by practice
  area (180d). New `PATCH /api/auth/me` for profile/target updates.
- UI: new sidebar page "Analitika" (`/reports`) with color-coded rate cards
  (thresholds: utilization 70%, realization 85%, collection 90%), funnel and
  per-area profitability table; source select in intake form; monthly hours
  target editable in Settings → Profile.
- Verified: 9 tests pass; synthetic-data check of all analytics payloads
  (rolled back); frontend built; stack restarted; /reports returns 200.

## 2026-07-07 — Dashboard upgrade P1 implemented (Cursor / Fable 5)

- Done: extended `/api/reports/dashboard` with `today_agenda` (pending deadlines
  due today, joined with matter ref/title), `ar_aging` (sent invoices bucketed
  0-30/31-60/61-90/91+ days by issued_on), `monthly_trend` (last 6 months of
  worked hours + billed revenue; date_trunc via literal_column — bound params
  in GROUP BY break Postgres). UI: agenda card on top of dashboard, aging
  breakdown card, two CSS mini bar charts, `QuickTimer` component in the
  sidebar (localStorage-backed, saves to POST /time-entries on stop).
- Verified: 9 backend tests pass; synthetic-data check of all three new
  payloads (rolled back); frontend rebuilt; stack restarted, health OK.
- Gotcha: dictionary keys must be unique across the file (`selectMatter`
  already existed) — TS build enforces `en`/`zh` match `typeof sq`.

## 2026-07-07 — Dashboard competitor analysis (Cursor / Fable 5)

- Done: web research comparing our dashboard vs Clio, Smokeball, MyCase +
  2026 legal-KPI best practices (curate 5-7 KPIs; categories: financial/
  production/capacity/marketing; trends over static numbers). Result canvas:
  `~/.cursor/projects/home-kllosha-BoraLaw/canvases/dashboard-krahasimi.canvas.tsx`.
- Findings: we already have real-time clickable KPI cards and a unique
  differentiator (deadlines with procedural legal basis — nobody has that);
  main gaps are today-agenda, trend charts, A/R aging, utilization/realization,
  quick timer. Added as Dashboard P1/P2 items in ROADMAP Phase 2.

## 2026-07-07 — Sales pitch for Kosovo law firm (Cursor / Fable 5)

- Done: a law firm in Kosovo contacted the owner after he posted about the
  project. Wrote the presentation text (Albanian) in
  `docs/pitch/prezantimi-firma-avokatesh.md`, framed as a founding-partner
  pilot offer (their expertise shapes the firm module, Phase 3).
- Note for future agents: if the pilot happens, Phase 3 (roles, matter
  assignment, firm reporting) becomes top priority in ROADMAP.

## 2026-07-06 — Agent management system + autostart (Cursor / Fable 5)

- Done: created the agent operating system for this repo: root `AGENTS.md`
  (entry point for any LLM/agent), `CLAUDE.md` pointer, `docs/agents/`
  (STATE, JOURNAL, DECISIONS, ROADMAP). Made the first git commit.
- Done: `boralaw.service` (systemd user unit, enabled) so the stack starts on boot;
  hardened `start.sh` (waits for docker + DB health, skips rebuild when `.next` exists).
- Done: recovered the original project chat that was orphaned in Cursor
  (it had been run from an empty window; relinked it to this workspace).
- Verified: service starts stack from scratch; `/api/health` OK; frontend 200.
- Left open: nothing blocking. See ROADMAP for next steps.

## 2026-07-06 — Project foundation (Cursor agent, first session)

- Done: full MVP scaffold and implementation — FastAPI backend (models, API,
  services, LLM abstraction, Kosovo seeds, Alembic initial schema, tests),
  Next.js frontend (all pages, i18n sq/en/zh), docker-compose (pgvector, Redis,
  Caddy HTTPS), start/stop scripts, README.
- Verified: backend tests passing; stack running; UI functional at :3000.
- Left open: git repo initialized but no commits (fixed in next session).
