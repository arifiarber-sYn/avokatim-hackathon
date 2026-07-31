# Security Policy — AvokatIM

AvokatIM stores privileged attorney–client material. Security reports are
taken seriously and handled with priority.

## Reporting a vulnerability

- **Preferred**: the contact form at <https://avokatiim.ai/kontakti>
  (category "Ankesë") — it lands directly in the platform operator's queue
  and is triaged the same day.
- **Email**: arifi.arber@gmail.com (subject prefix `[SECURITY]`).

Please include: affected URL/endpoint, steps to reproduce, expected vs.
actual behavior, and any proof-of-concept. Do **not** access data that is
not yours, do not degrade the service, and give us reasonable time to fix
before public disclosure. We confirm receipt within 48 hours and keep the
reporter informed until resolution. Good-faith research within these rules
will never be met with legal action.

## Scope

- `avokatiim.ai` and all its subdomains (app, API, LiveKit, stats)
- The AvokatIM codebase in this repository

Out of scope: social engineering, physical attacks, DoS/volume attacks,
and third-party services we do not operate (Cloudflare, Meta, Stripe).

## What protects the platform today

| Layer | Measure |
|---|---|
| Transport | HTTPS everywhere (Cloudflare edge + HSTS), HTTP→HTTPS redirect |
| Headers | CSP, X-Frame-Options/frame-ancestors, nosniff, Referrer-Policy, Permissions-Policy |
| Auth | bcrypt passwords, JWT with `token_version` revocation, TOTP 2FA for lawyers, OAuth (Google/Apple/Meta) for citizens, login brute-force limits |
| Tenancy | `tenant_id` scoping in code **and** Postgres Row-Level Security (FORCE) via a non-superuser DB role |
| Data at rest | Fernet encryption for documents, evidence chunks and TOTP secrets; AES-256 encrypted backups |
| Evidence | SHA-256 hash chain per recording session (tamper-evident) |
| Ingress | Rate limits (Redis) on public endpoints, signature verification on Stripe/Meta webhooks, MIME allowlist on uploads |
| Audit | Append-only audit log for user-visible actions; ops alerts via Telegram |
| AI | Local embeddings only for client documents; external-AI kill switch per tenant |

## Supported versions

AvokatIM is deployed continuously from `main`; only the live deployment is
supported.

## Dependency hygiene

`scripts/security_scan.sh` runs weekly (systemd timer) — `pip-audit` for the
backend and `npm audit` for the frontend — and reports findings to the
platform operator via Telegram.
