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

## #4 — Frontend now has its OWN systemd unit; restarting `avokatim` does not deploy UI changes (2026-07-26)

- **Symptom**: same class as #3, second incident. After a frontend rebuild
  and `systemctl --user restart avokatim`, the live site served the
  morning's HTML whose chunk files the new build had deleted from
  `.next/static/chunks/` → every `/_next` asset returned 500, pages
  rendered unstyled and never hydrated (buttons dead).
- **Cause**: the stack was split into `avokatim.service` (backend uvicorn
  only) and `avokatim-frontend.service` (ExecStartPre rebuild-if-changed +
  `npm start`). Restarting `avokatim` no longer touches the frontend at
  all, but AGENTS.md and muscle memory still said "restart avokatim =
  everything".
- **Rule** (deterministic, per AgentStandard §6): after ANY frontend
  change, deploy with
  `cd frontend && npm run build && systemctl --user restart avokatim-frontend`.
  Verify with `curl -s http://127.0.0.1:3000/<page> | rg -o '/_next/[^"]+' | head -1`
  and confirm that asset returns 200. If `systemctl` warns "unit file
  changed on disk", run `systemctl --user daemon-reload` first.

## #5 — Test/simulation identities must be gated on the marketplace fan-out (2026-09-18)

- **Symptom**: ~14 real lawyers received "AvokatIM — Rast i ri që përputhet
  me profilin tënd" (email + push, some SMS) for cases that never appeared in
  Treg; one lawyer got 5 mails in 2 hours (69 notifications on 2026-09-18; the
  same pattern on 2026-09-01). `case_requests` held 2 rows — the marketplace
  looked empty because the cases were deleted seconds after creation.
- **Cause**: `full_simulation.py` runs against the LIVE API
  (`127.0.0.1:8000`) and posts synthetic cases as
  `qytetari.sim.<hex>@gmail.com`. `citizen_create_case` / `citizen_sos` fanned
  out to real lawyers with no test check — `_is_test_recipient` was applied
  only to the citizen's own `notify_ops`. The harness then deleted the cases
  (`ON DELETE CASCADE`), so the mails pointed at nothing.
- **Rule**: gate the test identity at three levels — (1) request level
  (`_is_test_recipient(citizen.email)` before BOTH fan-outs), (2) inside
  `_notify_matching_lawyers` / `_notify_on_duty_lawyers`, so a future caller
  cannot forget it, (3) the harness itself: `scripts/sim_guard.py` refuses the
  production base URL unless `--allow-prod` is passed (use
  `AVOKATIM_SIM_BASE_URL` for a test instance). All three harnesses
  (full/de/notary) go through the guard; regression tests in
  `tests/test_sim_guard.py`.
