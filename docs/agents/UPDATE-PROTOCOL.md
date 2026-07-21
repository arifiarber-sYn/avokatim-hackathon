# UPDATE PROTOCOL — keep this layer alive (read when you change ANYTHING)

This layer is only useful while it stays true. Updating it is part of the
definition of done for EVERY change — code, config, prompts, and ops work
(systemd, git, keys). This formalizes AGENTS.md §2 (session protocol).

## When you finish a change (write side)

1. **JOURNAL.md** — append one entry (newest on top): done / verified /
   left open. **Never optional** — this is the project's changelog.
2. **STATE.md** — if anything live changed (new module, dependency, changed
   behavior, known issues), update it so it describes reality.
3. **DECISIONS.md** — architectural decision made or superseded → new
   D-number (append-only).
4. **LESSONS.md** — a decision was settled, an experiment failed, or an
   incident happened → numbered entry (symptom → cause → rule).
5. **COMMS.md** — if you added/changed any outbound email or operator
   notification → update it in the same commit (AGENTS.md §4b).
6. **AGENTS.md** — only if a hard rule / convention / architecture-map row
   changed.
7. **Commit** (see AGENTS.md §6) — never leave finished work uncommitted;
   never push without an explicit request.

## When you START a task (read side)

1. Root `AGENTS.md` → `docs/agents/INDEX.md` → route to what the task needs.
   Don't ingest everything (STATE.md is long — search it).
2. `git log --oneline -5 && git status` — unrecognized commits? Read the
   diff before touching anything.
3. Check `LESSONS.md` + relevant `DECISIONS.md` entries before proposing to
   remove/replace something — it may be settled.
