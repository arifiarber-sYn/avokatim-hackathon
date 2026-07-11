# STATE — current project snapshot

> Update this file whenever the state changes (new module, dependency, behavior,
> known issue). Keep it a snapshot, not a history — history lives in JOURNAL.md.

**Last updated:** 2026-07-11

## Status: demo-ready — P0/P1/P2 closed + full Kosovo-law compliance layer (6 languages, data protection 06/L-082, AML 05/L-096) + public citizen marketplace (Phase 1 of the citizen-bridge vision); zero known feature gaps

All core modules exist end-to-end (API + UI) and the stack runs on this machine.

## What exists and works

- **Auth**: public self-service signup (`POST /auth/signup` → new tenant on a
  30-day trial + admin user; page `/regjistrohu`), JWT login, 2FA (TOTP),
  email verification (signed purpose tokens, page `/verifiko-email`, banner +
  resend in app), password reset (`/harrova-fjalekalimin` → `/rivendos?token=`,
  single-use via password-hash fingerprint), change password (Settings →
  Profile). Login rate limiting via Redis (5 fails/15 min per email+IP → 429).
  `get_current_user` validates the JWT tenant claim, blocks suspended tenants,
  expired trials, and enforces the per-tenant `require_2fa` policy (members
  without TOTP can only reach `/api/auth` until they enable it).
- **Multi-company SaaS** (2026-07-09): Tenant carries `plan`
  (trial/solo/firm), `status` (active/suspended), `seats_limit`,
  `trial_ends_at`, `billing_notes`, `require_2fa`, `logo`. Seat limits enforced
  on team invite/reactivation (402). Trial banner + verify-email banner in the
  app shell. **Platform panel** (`/platform`, superadmin only — flag
  `users.is_superadmin`, never settable via API): list tenants with
  seats/matters/status, suspend/activate, change plan/seats, extend trial,
  billing notes. Billing itself is manual (D-008). The founder user is
  superadmin; founder tenant is plan=firm/25 seats.
- **Tenant isolation** (2026-07-09): corpus writes superadmin-only (shared
  read-only knowledge base), `document_text` goes through restricted-matter
  checks, portal login is tenant-aware (same client email may exist at several
  firms; password picks the account), ICS feed tokens now expire (180 d).
  E2E suites: `backend/scripts/isolation_check.py` (2 throwaway tenants,
  cross-tenant 404s incl. ICS + corpus) and `backend/scripts/saas_check.py`
  (signup/verify/reset/rate-limit/invites/seats/platform/suspend) — run both
  against the live backend after auth/tenancy changes.
- **Mobile responsive + PWA** (2026-07-09): app shell with `hidden md:flex`
  sidebar, mobile top bar + hamburger drawer + bottom nav (Paneli, Lëndët,
  Kalendari, Ava, Më shumë); matters/contacts render as card lists on phones,
  other tables scroll horizontally; matter tabs scroll; assistant collapses to
  one panel with a conversation dropdown; dashboard charts stack. Manifest has
  maskable icon (`icon-512-maskable.png`), scope/orientation; `sw.js` precaches
  the shell, cache-first for static assets, network-first for navigations —
  API responses intentionally never cached. SW registered from the app layout.
- **Team**: multi-user per tenant with roles (admin/lawyer/staff), managed in
  Settings → Team; matter assignment via `responsible_user_id` (editable in
  matter Overview when >1 member). Adding a member flips tenant kind to "firm".
  **Invites by email** (2026-07-09): admin-only `POST /team/invite`
  (name/email/role) — the invitee sets their own password at `/ftesa?token=`
  (7-day signed token; the old add-with-password endpoint is gone). Pending
  invites show a badge + resend. New-tenant onboarding checklist appears on
  the dashboard after signup (`?welcome=1`).
- **Intake**: new case registration, automatic conflict-of-interest check, AI
  classification, source tracking. **Public intake form** at `/apliko/{token}`
  (tenant token from Settings; submissions arrive with source=web).
- **Matters**: digital case file — parties, documents, deadlines, notes, history,
  **two-way client messages** (Messages tab ↔ portal).
- **Per-matter permissions** (2026-07-08): `matters.restricted` + `matter_members`
  table. A restricted matter is visible only to admins, the responsible lawyer and
  explicit members — enforced centrally in `get_owned_matter` +
  `restricted_visibility_filter` (matter list, upcoming deadlines, ICS feed,
  dashboard agenda). UI: checkbox + member picker on matter Overview (shows when
  team > 1).
- **Document approval workflow** (2026-07-08): draft → in_review → approved /
  changes_requested. `POST /documents/{id}/request-review` (pick reviewer),
  `POST /documents/{id}/review` (reviewer or admin decides, optional note),
  `GET /documents/review-inbox`. UI: "Rishikimi" column in the matter Documents tab.
- **CSV data import** (2026-07-08): Settings → Data import; `POST /import/contacts`
  and `/import/matters` (utf-8/latin-1, header row, dedupe by name, client
  auto-link/create, dates YYYY-MM-DD or dd.mm.yyyy). Template CSVs downloadable
  in the UI. Max 2000 rows per file.
- **Fiscal invoices** (2026-07-08): tenant carries `fiscal_number` (NUI),
  `vat_number`, `address`, `default_vat_rate` (18) — editable in Settings → Firm
  profile (admin only, `GET/PATCH /firm`). New invoices get `vat_rate` from tenant
  default (overridable per invoice); `vat_amount`/`total_with_vat` computed and
  shown on the invoice card. Numbering remains sequential per year (F-YYYY-NNNN).
- **Deadline engine**: Kosovo procedural rules (LPK, KPPRK, LKA) seeded as data,
  automatic calculation with official holidays. Tests in `test_deadline_engine.py`.
- **AI deadline extraction**: button on any document with text — Ava proposes
  deadlines (title/date/legal basis/confidence), lawyer reviews and accepts →
  `POST .../extract-deadlines` + `POST .../deadlines/bulk`.
- **Calendar sync**: ICS feed (`/api/calendar/feed.ics?token=...`, signed token,
  URL in Settings) for Google Calendar/Outlook/phone subscriptions.
- **Documents**: encrypted storage (Fernet), versioning, text extraction + OCR,
  semantic indexing (pgvector + local embeddings).
- **E-signature**: lawyer requests signature on a document (Documents tab);
  client signs in portal (typed name bound to document SHA-256, IP + timestamp,
  audit-logged). Status pending/signed/declined shown on both sides.
  **Certificate of Completion PDF** (2026-07-08): "Certifikata" link next to a
  signed status downloads a WeasyPrint PDF proof sheet
  (`GET /matters/{id}/signatures/{sig_id}/certificate`) citing Law 08/L-022.
  Qualified signatures = future QTSP integration (Evrotrust / rTrust — see D-007).
- **Templates**: 12 seeded XK templates auto-filled from matter data: civil
  lawsuit, appeal, power of attorney, payment-order objection, labor lawsuit,
  administrative lawsuit, demand letter, NDA, service contract, employment
  contract, legal opinion, due-diligence checklist (all in `seeds/kosovo.py`).
- **Assistant "Ava"**: RAG over legal corpus + matter documents, with citations.
  Providers: DeepSeek (default) or local OpenAI-compatible (Ollama/vLLM), selectable per request.
  **Answers stream (SSE)** via `/api/assistant/ask-stream` — the UI renders text
  progressively and no proxy/browser/Cloudflare idle timeout can drop long
  thinking-mode answers (see D-010). Non-streaming `/ask` kept for scripts.
  Also: **client-update drafting** (AI tab on matter → send to portal or copy).
  Questions without a matter now ground in the tenant's default jurisdiction
  corpus (so citations always work, not only inside a matter).
- **Corpus**: upload laws via Settings → Legal base; auto-chunked by article ("Neni X").
  **Real Kosovo corpus loaded** (2026-07-08): 9 laws / ~4,000 article chunks from
  Gazeta Zyrtare — LPK 03/L-006, KPP 08/L-032, Criminal Code 06/L-074
  (consolidated 2026), LMD 04/L-077, Labor Law 03/L-212, Administrative
  Disputes 08/L-182, Business Organizations 06/L-016, Family Law 2004/32,
  Data Protection 06/L-082. Re-runnable importer: `backend/scripts/import_gzk.py`
  (skips laws already present; add new laws to its `LAWS` list).
- **Billing**: time entries, **matter expenses/disbursements** (categories:
  court fee, bailiff, expert, travel, notary, translation; billing tab), invoices
  generated from unbilled hours **and unbilled expenses** plus **manual flat-fee
  items** in the invoice form. **Invoice PDF** (2026-07-09):
  `GET /invoices/{id}/pdf` — WeasyPrint fiscal invoice with firm logo, NUI/VAT,
  VAT breakdown and bank details (`Tenant.bank_details`, Settings → Firm
  profile); `POST /invoices/{id}/send` emails the PDF to the client
  (attachment support added to `send_email`) and sets status→sent.
- **Tasks** (2026-07-09): `Task` model (matter optional, assignee, due date,
  priority, status) + CRUD `/tasks`; Detyrat tab in matter, "Detyrat e mia"
  card on dashboard.
- **Global search** (2026-07-09): `GET /search?q=` over matters, contacts,
  documents (filename + extracted text) and invoices, respecting restricted
  visibility; grouped-results search box above the content on every page.
- **Document preview** (2026-07-09): `GET /documents/{id}/preview` (inline
  disposition) + modal in the matter Documents tab (PDF iframe / image).
- **Portal documents** (2026-07-09): `Document.visible_to_client` +
  per-document toggle in the Documents tab ("Në portal" column);
  portal endpoints `GET /portal/matters/{id}/documents` + download
  (audit-logged); documents section in the portal matter view.
- **Portal email notifications** (2026-07-09): client gets an email when the
  lawyer sends a message or requests a signature; the responsible lawyer gets
  an email when the client writes or signs.
- **Templates → matter** (2026-07-09): missing variables render as `__________`
  placeholders (no more 400); `authority`/`court_case_number` prefilled from
  the matter; output is editable in the UI; `POST /templates/render-to-matter`
  saves it as a searchable matter PDF document (category=draft).
- **Audit log UI + export** (2026-07-09, admin only): Settings → Regjistri i
  veprimeve (filterable viewer over `GET /audit-log`) and Settings → Eksporti
  (`GET /export/tenant` → ZIP of Albanian-named CSVs + decrypted documents).
- **Trust ledger — client funds** (2026-07-09): `TrustTransaction` model;
  `/trust/transactions` (deposit/withdrawal, delete) + `/trust/balances`;
  withdrawals beyond the balance rejected (400) — the ledger can never go
  negative; "Mjetet e klientit" tab in Billing (balance cards + table);
  included in the tenant export ZIP.
- **OAK fee tariff as data** (2026-07-09): `FeeTariffItem` model, 17 rows
  seeded from the Kosovo Bar tariff (in force 01.01.2015) in
  `seeds/kosovo.py::XK_FEE_TARIFF`; `GET /fee-tariff?jurisdiction_code=XK`;
  invoice-form picker prefills description + price. Amounts are editable data.
- **.docx export** (2026-07-09): `POST /templates/render-docx` via
  `app/services/docx_render.py` (python-docx; court-filing layout); "Shkarko
  .docx" button next to the PDF/save actions on the templates page.
- **Email-to-matter** (2026-07-09): IMAP poller (`app/services/email_ingest.py`,
  lifespan task; off without `imap_host` in .env). Matter alias =
  `imapuser+<email_token>@domain` (`GET /matters/{id}/email-address`, lazy
  token, shown with copy button in matter Overview; hidden when unconfigured).
  Inbound mail → matter note + attachments as encrypted documents
  (category "email"); Message-ID dedup in Redis.
- **SMS reminders** (2026-07-09): `app/services/sms.py` (Twilio-compatible
  REST; off without `sms_account_sid`). Hearing reminders additionally SMS
  the matter's client at the same day-offsets.
- **Card payments** (2026-07-09): `app/services/payments.py` — Stripe Checkout
  session via raw API (no SDK; off without `stripe_secret_key`).
  `POST /invoices/{id}/payment-link` → stores `payment_link` on the invoice,
  UI button + link, included in the invoice email. Public
  `POST /api/stripe/webhook` (HMAC verify + 5-min replay window) marks the
  invoice paid automatically. Webhook URL must be routed publicly to activate.
- **Legal paperwork for buyers** (2026-07-09): `docs/legal/` — LMDhP/DPA
  model per Law 06/L-082 and SLA (99.5%, P1–P4, RPO/RTO, credits), Albanian.
- **Demo package** (2026-07-09): `backend/scripts/seed_demo.py` creates/resets
  tenant "Zyra Demo" (8 matters, deadlines, docs, tasks, expenses, trust
  transactions, invoices, portal client with pending signature; logins in the
  script header); demo runbook `docs/pitch/skenari-demo.md`.
  `full_simulation.py` covers everything incl. languages/privacy/AML
  (sections 20–23): **89 PASS / 0 FAIL / 0 GAP**.
- **Client portal**: full UI at `/portal` — login, matters with hearings,
  two-way messages, e-signature inbox. Shows the **firm's own name + logo**
  (from portal login response) instead of "AvokatIM"; the public intake form
  does the same (logo uploaded in Settings → Firm profile, data-URL ≤200 KB).
- **Reminders**: background loop (hourly) notifies the responsible lawyer at
  each deadline's `remind_days_before` offsets; deduped via Redis. Two channels:
  **Web Push** (active — VAPID keys in `backend/.env`, per-device opt-in in
  Settings → Device notifications) and email (active — Gmail SMTP via App
  Password in `backend/.env`, test delivery verified 2026-07-07).
- **Payments**: marking an invoice paid records `paid_on` + optional
  `payment_reference` (bank transaction no.), shown on the invoice card.
- **Dashboard**: workload, week's deadlines, finances. **/reports**: analytics
  incl. **per-lawyer table** (open matters, MTD hours vs target, utilization)
  when the tenant has >1 active member.
- **PWA**: manifest + icons; installable on phone; service worker (`public/sw.js`)
  shows push notifications and opens the matter on tap.
- **Backups**: `backup.sh` — encrypted (AES-256, key at
  `~/.config/avokatim/backup.key`) archive of pg_dump + `data/documents` +
  `backend/.env` into `~/AvokatIMBackups/`, retention 30. Daily at 03:00 via
  systemd user timer `avokatim-backup.timer` (enabled). Restore steps in the
  script header. **The key file must also be copied somewhere off-machine.**
- **i18n — 6 languages** (2026-07-09, Law 02/L-37): UI in sq/sr/tr/bs/en/zh
  (`dictionaries.ts`, ~490 keys each; every new UI string goes in ALL SIX).
  Backend catalog `app/i18n.py` (`tr`/`pick_locale`/`bilabel`) localizes
  server-generated output: reminder emails, SMS, invoice email + PDF
  (bilingual sq + client language), signature-request email, certificate.
  `Contact.locale` = client communication language (contact form/detail +
  returned by portal login, portal auto-switches); fallback chain contact →
  tenant default → sq. Seeds carry sr/tr/bs names for deadline rules,
  holidays, OAK tariff (merged into existing rows via `_merge_name`);
  3 Serbian client-facing templates marked "kërkon rishikim nga avokati".
- **Data protection — Law 06/L-082** (2026-07-09): public multilingual ToS +
  Privacy pages (`/kushtet`, `/privatesia`; texts in `frontend/src/lib/legal.ts`,
  long-form Albanian originals in `docs/legal/kushtet-e-perdorimit.md` +
  `politika-e-privatesise.md`). Mandatory checkboxes: signup
  (`accept_tos` → `Tenant.tos_accepted_at`), public intake (`accept_privacy` →
  `IntakeRequest.tos_accepted_at`), portal first login (gate screen →
  `POST /portal/accept-terms` → ConsentRecord). **ConsentRecord** model
  (kinds: portal_tos/email/sms/ai_processing; granted/revoked, method, IP) +
  `/contacts/{id}/consents` API + consent card in contact detail; SMS
  reminders send only with recorded consent. **Erasure**
  (`POST /contacts/{id}/erasure`, admin, blocked on open matters — anonymizes
  identifiers, revokes consents), **data-subject export ZIP**
  (`GET /contacts/{id}/export`), **retention review**
  (`Tenant.retention_years`, `GET /privacy/retention-review` flags expired
  closed matters — never auto-deletes; Settings → compliance card).
  **External-AI gate**: `Tenant.allow_external_ai` — when off the assistant
  is forced to the local provider (`_effective_provider`), UI shows a lock
  note; when on, an art.-49 transfer warning shows for the external provider.
  Ops docs in `docs/legal/`: breach-notification procedure (72h → AIP), RoPA,
  DPA Annex A (sub-processors + transfers). `backup.sh` retention 14→30
  (matches SLA).
- **AML — Law 05/L-096** (2026-07-09): KYC fields on Contact (id_doc_type/
  number, id_verified_on, risk_level, is_pep, beneficial_owner; contact-detail
  form + risk column). `TrustTransaction.source_of_funds` + audit flag
  `aml_large_amount` and UI warning for deposits ≥ 10,000 €. NjIF-K suspicion
  indicators as seed data (`XK_AML_INDICATORS`, 10 items × 6 languages) +
  per-matter AML checklist (state in `Matter.extra["aml"]`, scope
  auto-suggested when the matter has trust transactions; AML tab on matter).
  **SuspicionReport** model + `/aml/reports` API + WeasyPrint PDF for filing
  with NjIF-K + mark-submitted; `Tenant.compliance_officer_id` picker in
  Settings. Internal AML policy model at `docs/legal/politika-aml.md`.
- **Audit log** on matter/document actions.
- **Public marketplace — citizens ↔ lawyers** (2026-07-11, Phase 1 of D-013):
  platform-level models in `app/models/marketplace.py` (no tenant_id):
  `CitizenUser` (own bcrypt password, locale, email verification,
  `privacy_accepted_at`), `LawyerProfile` (opt-in public directory entry per
  tenant user: bio/areas/cities/languages/photo, `is_visible`), `CaseRequest`
  (open → claimed → converted / closed; optional `directed_tenant_id` for
  requests aimed at one lawyer from the directory), `CaseRequestMessage`
  (citizen ↔ claiming lawyer pre-intake chat). API `app/api/marketplace.py`:
  public `/public/citizen/*` (signup with mandatory privacy consent, login,
  verify-email via purpose token, cases CRUD, messages — Redis rate limits:
  5 signups/h/IP, 5 cases/day, 60 msgs/day; posting requires verified email;
  citizen JWT has its own `citizen` claim, unusable as lawyer/portal token),
  public `GET /public/lawyers` (visible profiles, filter area/city/language),
  lawyer `/marketplace/*` (profile upsert, browse open cases with masked
  citizen name, **claim** → existing conflict check → `IntakeRequest
  source="marketplace"`, mine, messages, report-abuse → closes + audit).
  On intake **accept**, the linked CaseRequest becomes `converted`, the new
  Contact gets the citizen's email/locale/**same password hash** with portal
  auto-enabled, signup consent carried into ConsentRecord
  (method="marketplace"), and the citizen is emailed that the portal is ready.
  Emails localized in all 6 langs (`citizen_verify_*`, `case_claimed_*`,
  `case_directed_*`, `case_message_*`, `case_portal_ready_*` in `app/i18n.py`).
  Frontend: public `/avokatet` (directory + filters), `/posto-rastin`
  (citizen signup/login + case form, supports `?avokati=<tenant_id>`),
  `/rasti-im` (citizen dashboard: statuses, chat, close; handles
  `?verifiko=<token>`), **new two-audience landing at `/`** (citizens vs
  lawyers; logged-in lawyers still auto-redirect to /dashboard);
  in-app `(app)/marketplace` ("Tregu" in nav) with open/mine tabs, claim +
  conflict warning + report; Settings → "Profili publik" section. Citizen
  token kept in `localStorage.avokatim_citizen_token`
  (`frontend/src/lib/citizen.ts`). ~60 new UI keys ×6 languages.
  Tests: `tests/test_marketplace.py`; `full_simulation.py` section 24.
- **Public Ava — free legal-information chat** (2026-07-11, Phase 2 of
  D-013): `/api/public/ava/*` in `app/api/marketplace.py` — `ask` +
  `ask-stream` (SSE), grounded in the XK legal corpus via the existing RAG
  (`search_corpus`), own system prompt (`PUBLIC_AVA_SYSTEM_PROMPT`:
  information NOT advice, answer in the question's language, cite laws,
  suggest "Më lidh me avokat" when professional help is needed). Stateless —
  the browser holds the history; nothing persisted. Daily quotas in Redis:
  **5 questions/day anonymous** (IP + localStorage session id),
  **20/day with citizen account** (optional citizen bearer token);
  `GET /public/ava/quota` for the counter. Frontend `/ava`: streaming chat
  with citation chips, 6-language disclaimer, quota bar, and
  **"Më lidh me avokat"** which stores the user's questions in
  `localStorage.avokatim_case_draft` — `/posto-rastin` prefills the case
  description from it. Landing citizen block links to `/ava`.
  Simulation section 25 (**110 PASS / 0 FAIL** total).
  Phase 3 (SOS video/audio) stays blocked on WebRTC media ports —
  Cloudflare Tunnel is HTTP-only; needs router port forwarding or a TURN
  relay VPS before it can start. Phase 4 (lawyer plans/lead fees) not built.

## Environment

- Host: owner's Fedora Linux machine; everything runs locally.
- **Public domain**: https://avokatiim.ai (+ www) via **Cloudflare Tunnel** —
  live since 2026-07-10 (old domain boraarifi.ai now serves only a static
  parking page via Caddy :8099; both zones on Cloudflare) —
  tunnel named `boralaw` on Cloudflare (legacy internal name, kept because the
  tunnel ID is wired into both DNS zones; id d22368e7-b5a0-44fb-80f5-12aa1aa5fa7f), config at
  `~/.cloudflared/config.yml` (ingress → 127.0.0.1:3000; Next.js rewrites proxy
  /api → backend). Runs as systemd user service `avokatim-tunnel.service`
  (enabled). TLS terminates at Cloudflare edge — no cert management needed.
  DNS on Cloudflare (free plan), domain registered at Namecheap (.ai).
- **Autostart**: systemd user service `avokatim.service`
  (`~/.config/systemd/user/avokatim.service`) runs `start.sh` on boot; lingering enabled.
- Containers (restart: unless-stopped): `avokatim-db` (pgvector/pg17, host port 5433),
  `avokatim-redis` (6380), `avokatim-caddy` (host network, HTTPS 8443).
- Backend: uvicorn on 127.0.0.1:8000, venv at `backend/.venv`. Frontend: Next.js on :3000.
- Secrets in `backend/.env` (git-ignored): DeepSeek key, doc encryption key, DB password.
- **Optional integrations, off until configured in `backend/.env`** (all degrade
  gracefully): email-in `IMAP_HOST/USER/PASSWORD` (+folder/poll), SMS
  `SMS_ACCOUNT_SID/AUTH_TOKEN/FROM` (Twilio-compatible), card payments
  `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` (route the public URL to
  `/api/stripe/webhook`).
- Optional extras installed in venv: `requirements-ai.txt` (local embeddings, OCR).
- System tesseract 5.5.2 installed (2026-07-07) with sqi/eng/chi_sim langpacks;
  OCR verified end-to-end on synthetic Albanian scanned image and image-only PDF.

## Known issues / caveats

- ~~`start.sh` skips `npm run build`~~ fixed 2026-07-07: `start.sh` now rebuilds
  automatically when any file in `frontend/src`/`public` is newer than
  `.next/BUILD_ID`, and kills the stale `next-server` before starting a fresh one
  (a stale server over a new build serves 404 chunks → blank pages).
- ~~SMTP not configured~~ done 2026-07-07: Gmail App Password in `backend/.env`
  (SMTP_* vars, smtp.gmail.com:587 STARTTLS, from arifi.arber@gmail.com).
  Test email sent and delivered — both reminder channels (email + push) active.
- Host has no GPU tooling (`nvidia-smi` absent) and Ollama has no models/service —
  local-LLM option stays unconfigured; DeepSeek remains the provider. To try
  local: `ollama serve` + `ollama pull qwen3:8b` (CPU will be slow), then set
  `LOCAL_LLM_MODEL=qwen3:8b` in `backend/.env`.
- E-signature is the simple flow (typed name + SHA-256 + audit); qualified
  eIDAS/Kosovo e-signature law compliance is future work.
- ~~PUBLIC_BASE_URL placeholder~~ set to https://avokatiim.ai (2026-07-10;
  was boraarifi.ai before).
- Caddy serves a self-signed cert on :8443 (browser warning is expected on LAN).

## Jurisdictions

- **XK (Kosovo): active** — deadline rules, holidays, templates seeded.
- GB, CN, INTL: schema-ready, no data yet.
