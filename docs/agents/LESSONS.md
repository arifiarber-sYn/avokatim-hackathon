# LESSONS — settled decisions and incidents (check BEFORE proposing changes)

> Append-only, numbered. Each entry: **symptom → cause → rule**. If an idea
> here was tried and failed, do not re-litigate it without new evidence.
> Architectural decisions (with context and reasons) live in `DECISIONS.md`;
> this file is for operational lessons and incidents. A lesson that repeats
> (same class, second incident) MUST become a deterministic check
> (script / hook / lint), not just prose — AgentStandard §6.

## #1 — Old brand names must never come back (2026-07-11)

- **Symptom**: the project was fully rebranded from "BoraLaw" (assistant
  "Bora") to **AvokatIM** (assistant "Ava") to avoid a conflict of interest.
- **Cause**: agents with stale context (old chats, old docs, the `~/BoraLaw`
  compat symlink, the Cloudflare tunnel still internally named `boralaw`)
  can reintroduce the old names.
- **Rule**: never reintroduce "BoraLaw"/"Bora" in code, UI, docs or comms.
  The symlink and the tunnel's internal name are intentional leftovers —
  leave them, but nothing new gets the old name.

## #2 — Test identities must match the suppression patterns (2026-07)

- **Symptom**: E2E simulations create throwaway tenants; if their email
  addresses don't match `_is_test_recipient` in `services/notifications.py`,
  bounces (and thank-you letters) hit real inboxes.
- **Cause**: outbound email is real in the live stack — simulations run
  against it.
- **Rule**: any new test identity must match the suppression patterns; any
  new outbound email must be checked against the simulations (and get a row
  in `COMMS.md` in the same commit).
