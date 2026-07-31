# CHANGELOG — dated trail of changes (newest on top)

> One entry per finished piece of work. Never optional (Definition of Done).
> Format: date, what changed, why, files touched.

## 2026-07-31 — Suppress isolation_check probe addresses (iso.a/iso.b)

- The owner was alarmed by two "unverified lawyer signups" — they were the
  self-deleting IsoTest A/B tenants that `scripts/isolation_check.py` creates
  through the real signup endpoint. Their `iso.[ab].<hex>@gmail.com` addresses
  were missing from `_TEST_RECIPIENT_RE`, so signup pinged Halim/Telegram and
  tried to send verification emails. Added the pattern + regression tests
  (including a real-looking `iso.krasniqi@` that must still pass).
- Files: `backend/app/services/notifications.py`,
  `backend/tests/test_email_suppression.py`.

## 2026-07-31 — Security wave (D-033): Postgres RLS + OpsHub-inspired hardenings

- Tenant isolation enforced in the database itself: non-superuser role
  `avokatim_app`, `tenant_isolation` RLS policies (ENABLE+FORCE) on all 25
  `tenant_id` tables, per-request transaction-local GUC pinned in deps.
  Default-open so public/background/superadmin paths behave as before;
  NULL-tenant rows stay platform-shared. Also: CSP + security headers in
  proxy.ts, WhatsApp webhook HMAC verification, upload MIME allowlist,
  Fernet-encrypted TOTP secrets, `users.token_version` JWT revocation,
  SECURITY.md + /siguria report card (×6), weekly pip-audit/npm-audit timer
  reporting to Halim. First scan: Next.js → 16.2.12, sharp → 0.35.3.
- Verified: pytest 128/128, isolation_check (incl. new SQL probes) all PASS,
  full_simulation 188 PASS / 0 FAIL, live headers + screenshot OK.
- Files: `backend/app/{database,deps,config,security}.py`,
  `backend/app/api/{auth,documents,whatsapp}.py`,
  `backend/app/models/tenancy.py`, 3 Alembic revisions,
  `backend/scripts/{isolation_check,encrypt_totp_secrets}.py`,
  `frontend/src/proxy.ts`, `frontend/src/app/siguria/page.tsx`,
  `frontend/src/app/(app)/settings/page.tsx`, `frontend/src/lib/dictionaries.ts`,
  `scripts/security_scan.sh`, `SECURITY.md`; details in
  `docs/agents/DECISIONS.md` (D-033) + JOURNAL 2026-07-31.

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
