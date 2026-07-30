# CHANGELOG — dated trail of changes (newest on top)

> One entry per finished piece of work. Never optional (Definition of Done).
> Format: date, what changed, why, files touched.

## 2026-07-30 — Hide "member since" card on public lawyer profile while meaningless

- `/avokatet/[id]` showed "2026 / anëtar që nga" for every lawyer (platform
  launched 2026), which reads like "active only since 2026" — unfair to
  veterans. The card now renders only when the join year differs from the
  current year. Owner-approved after his confusion on Lulzim Aliu's profile.
- Files: `frontend/src/app/avokatet/[id]/page.tsx`; full entry in
  `docs/agents/JOURNAL.md` (2026-07-30).

## 2026-07-30 — docs/agent layer bootstrapped with AgentStandard v1.1

- The project already had a full `AGENTS.md` + Cursor stop-hook; this adds the
  standard `docs/agent/` skeleton (INDEX, STATE, LESSONS, DECISIONS, CHANGELOG,
  UPDATE-PROTOCOL — FILL sections pending) and the blocking pre-commit docs gate
  (`scripts/git-hooks/pre-commit`, installed at `.git/hooks/pre-commit`): commits
  staging code without a `docs/agent/` or `AGENTS.md` update are BLOCKED.
  Origin: OpsHub decision D17 + AgentStandard v1.1 (2026-07-30).
