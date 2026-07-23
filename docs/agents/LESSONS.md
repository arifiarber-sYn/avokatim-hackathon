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

## #3 — Manual frontend build + service restart left the OLD server running (2026-07-23)

- **Symptom**: new frontend code (Google login button) built cleanly, service
  restarted, `/api` fine — but the live site kept serving the old JS for a
  whole hour. Even a clean headless browser saw the old code, so it was not
  browser cache.
- **Cause**: `start.sh` only killed the running `next-server` inside its
  "code newer than BUILD_ID" branch. Running `npm run build` manually makes
  BUILD_ID newer than src, so the following `systemctl --user restart
  avokatim` skipped the kill, saw port 3000 healthy, and left the morning's
  server (with the old build in memory) running. The frontend also escapes
  the systemd cgroup (`nohup` in start.sh), so the service restart never
  touches it by itself.
- **Rule**: `start.sh` now ALWAYS kills this project's `next-server`
  (matched by `/proc/<pid>/cwd`, never by name alone — EdaS/CRM run
  `next-server` on the same machine) before ensuring one is up. When
  verifying a frontend change, confirm the server process start time is
  newer than BUILD_ID, or just check the new behavior live in a clean
  browser. Related: `public/sw.js` caches `/_next/static` cache-first and
  Turbopack chunk names are NOT content-hashed — bump `CACHE` version on
  UI overhauls.
