> ⛔ **DEPRECATED (D-066, 2026-08-05).** The canonical write procedure lives in
> **`../agents/UPDATE-PROTOCOL.md`** (plural). Write to `docs/agents/`
> (JOURNAL/STATE/LESSONS/DECISIONS/COMMS), not here. This file is archived.

---

# UPDATE PROTOCOL — keep this layer alive (read when you change ANYTHING)

This layer is only useful while it stays true. Updating it is part of the
definition of done for EVERY change — code, config, prompts, and ops work
(systemd, git, keys).

## When you finish a change (write side)

1. **STATE.md** — if anything live changed (services, ports, config, watch
   items), update it so it describes reality. Delete what became false.
2. **LESSONS.md** — if a decision was settled, an experiment failed, or an
   incident happened → append a numbered entry (symptom → cause → rule).
3. **DECISIONS.md** — if an architectural decision was made or superseded →
   append a D-number.
4. **CHANGELOG.md** — one dated entry, newest on top. **Never optional.**
5. **AGENTS.md** — only if a hard rule / convention / invariant changed.
6. **Commit** everything together with a clear message — the user should
   never have to ask. Never push without an explicit request.

## When you START a task (read side)

1. Root `AGENTS.md` → `docs/agent/INDEX.md` → route to ONE topic. Don't scan
   the whole repo.
2. `git log --oneline -5 && git status` — unrecognized commits? Read the diff
   before touching anything.
3. Check `LESSONS.md` before proposing to remove/replace something — it may
   be a settled decision.
