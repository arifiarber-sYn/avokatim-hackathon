# UPDATE PROTOCOL — keep this layer alive (read when you change ANYTHING)

This `docs/agents/` layer (plural) is the SINGLE SOURCE OF TRUTH for AvokatIM
agent knowledge (root `AGENTS.md` routes here). It is only useful while it stays
true. Updating it is part of the definition of done for EVERY change — code,
config, prompts, and ops work (systemd, git, keys).

> Note (D-066): the older `docs/agent/` (singular) directory is DEPRECATED and
> kept only as an archive. Never write new entries there — write here.

## When you finish a change (write side)

1. **JOURNAL.md** — append one dated entry, newest on top (this is the
   project's changelog). **Never optional.**
2. **STATE.md** — if anything live changed (services, ports, config, modules,
   dependencies, watch items), update it so it describes reality. Delete what
   became false.
3. **LESSONS.md** — if a decision was settled, an experiment failed, or an
   incident happened → append a numbered entry (symptom → cause → rule).
4. **DECISIONS.md** — if an architectural decision was made or superseded →
   append a D-number.
5. **COMMS.md** — if you changed anything that emails users or notifies the
   operator, update it (mandatory for outbound comms).
6. **AGENTS.md** (root) — only if a hard rule / convention / invariant changed.
7. **Commit** everything together with a clear message — the user should never
   have to ask. Never push without an explicit request.

## When you START a task (read side)

1. Root `AGENTS.md` → `docs/agents/INDEX.md` → route to the file(s) your task
   touches. Don't scan the whole repo.
2. `docs/agents/STATE.md` (search it — long) for what's live now.
3. Last 2–3 entries of `JOURNAL.md` + `git log --oneline -5 && git status` —
   unrecognized commits? Read the diff before touching anything.
4. Check `LESSONS.md` before proposing to remove/replace something — it may be
   a settled decision.
