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
