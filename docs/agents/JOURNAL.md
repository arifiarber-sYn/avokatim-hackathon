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
