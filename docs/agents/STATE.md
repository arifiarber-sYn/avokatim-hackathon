# STATE — current project snapshot

> Update this file whenever the state changes (new module, dependency, behavior,
> known issue). Keep it a snapshot, not a history — history lives in JOURNAL.md.

**Last updated:** 2026-08-01

## Status: live in production at https://avokatiim.ai (Kosovo) + https://de.avokatiim.ai (Germany, D-034) — lawyer office + citizen marketplace + notary profession + growth ops (automated outreach, analytics); first real signups arriving (first outreach conversion 2026-07-13)

All core modules exist end-to-end (API + UI) and the stack runs on this machine.

## What exists and works

- **Germany expansion** (2026-08-01, D-034): one codebase, two countries.
  `app/jurisdictions.py` = declarative per-country profiles (XK/DE: currency,
  VAT 18/19, timezone, locales, chamber registry OAK/BRAV, SOS+notary feature
  switches, corpus fallback language, cities, public host). Host → country:
  `de.avokatiim.ai` → DE (proxy.ts header `x-avokatim-country` +
  `country_from_request`); `country` columns on tenants/citizen_users/
  case_requests scope directory, marketplace, stats, SOS alerts, Ava.
  **German locale (de)** is the 7th full language: `dictionaries.ts` (1,130
  keys) + `app/i18n.py` (all email/SMS strings) + `supported_locales`;
  DE host defaults to de, its picker offers de/en/tr (`COUNTRY_LOCALES`).
  **German corpus**: `scripts/import_de_laws.py` — 78 federal acts from
  gesetze-im-internet.de XML (GG, BGB, ZPO, StGB, StPO, HGB, KSchG, VwGO,
  all citizen-relevant SGB books, BEEG, MuSchG, GewSchG, BerHG, GKG, UWG,
  WoGG, BAföG, RVG, BRAO…) + the GDPR in German via `import_dsgvo.py`
  (CELLAR/EUR-Lex, 99 articles) = **79 acts / 16,435 chunks**, § heading per
  norm, resumable; RAG fallback language is per-jurisdiction.
  **Landesrecht** (D-035): nullable `region` column (Bundesland code, NULL =
  federal) on holidays/corpus docs/tenants; 16-Länder registry + city→Land
  map in the DE profile; `import_de_landesrecht.py` (adapter per portal)
  loaded **NRW + Bayern, 20 acts / ~2,900 chunks**; `search_corpus(region=…)`
  = federal + that Land; public Ava has a Bundesland dropdown, citations
  show the Land. Remaining 14 Länder blocked on juris SPAs (LESSONS #1).
  **Federal case law** (2026-08-01, D-042): `import_de_rechtsprechung.py`
  (rii-toc.xml, BMJV portal) imports BGH/BAG/BVerfG decisions of the last
  5 years as `doc_type="judgment"`, `reference`=Aktenzeichen, sections
  Leitsatz/Tenor/Gründe; ~16.8k decisions matched, initial import running
  in background (`data/import_rechtsprechung.log`, resumable — re-run the
  script to continue/refresh). Ava cites judgments with court +
  Aktenzeichen (lawyer + public, DE prompt updated).
  **Hybrid retrieval** (D-042): `legal_corpus_chunks.tsv` (tsvector,
  `german`/`simple` per language) + GIN; `search_corpus` = RRF over
  3 legs (pgvector cosine, plainto AND, rare-word prefix OR with df ≤ 2%);
  judgments capped at limit//3 slots. Eval `scripts/eval_de_recherche.py`:
  §-citation queries 1/6 → 5/6; known limit: German compounds
  (Kündigungsschutzklage) still need better embeddings. **DE seed data**
  (`seeds/germany.py`): federal holidays (incl. Easter calc) + per-Land
  holidays 2026–27 (whole-Land only; deadline engine uses `tenant.region`
  via the settings Bundesland picker), 14 deadline
  rules (ZPO/StPO/KSchG/VwGO/SGG/AO — month rules use exact calendar-month
  math, `day_type="months"` per §§ 187–188 BGB, D-036), full RVG engine
  (D-037: § 13 band table KostBRÄG 2025 + VV items in seeds,
  `services/rvg.py`, lawyer + public fee-calc APIs, `/rvg` page, billing
  widget), 5 lawyer templates (incl. Deckungsanfrage), 4 German citizen
  doc templates (country-picked in `public_tools.py`).
  **DE market parity (D-037)**: DE-office invoice PDFs are ZUGFeRD/Factur-X
  hybrids (PDF/A-3b + EN 16931 CII XML via drafthorse, `Tenant.iban`;
  raw XML endpoint for B2G); `CaseRequest.has_legal_insurance`/`insurer_name`
  flow (form + Ava extraction + lawyer badge); DATEV EXTF export
  (`services/datev.py`, `GET /api/export/datev`, per-office SKR03 config);
  E2E check: `backend/scripts/de_simulation.py`. beA: BRAK registration
  guide + draft email in `docs/legal/BEA-KSW-REGISTRATION.md` (module after
  access). **DE Ava**:
  own prompt (RDG § 2 information-only + EU AI Act Art. 50 disclosure);
  local LLM (Ollama gemma3:27b on the RTX 5090) is installed and validated
  but DE runs **temporarily on DeepSeek** for the demo (see launch gate
  item 3 — must return to `llm_provider="local"` before public launch).
  **DE lawyers**: BRAV has no emails →
  never auto-verified; ops/Halim get a BRAV search link for one-click manual
  approval; onboarding shows German cities/languages, VAT 19 default,
  notary signup blocked (400) and SOS hidden/guarded (403) for DE.
  **Legal**: German AGB + Datenschutzerklärung drafts in `lib/legal.ts`,
  `/impressum` page (§ 5 DDG, address placeholder), launch gate =
  `docs/legal/DE-LAUNCH-GATE.md` (EU server, Art. 27 rep, EU LLM, lawyer
  review — blocks public launch, not development).

- **Security hardening wave** (2026-07-31, D-033): **Postgres RLS** on all 25
  tables with `tenant_id` — app connects as non-superuser `avokatim_app`
  (setting `database_app_url` in `backend/.env`; owner role stays in
  `database_url` for Alembic/scripts); `deps.get_current_user` pins each
  session to the tenant via transaction-local GUC (`app.tenant_id`,
  `after_begin` listener in `database.py`); policies are default-open so
  public/background/superadmin paths are unaffected, NULL-tenant rows are
  platform-shared. Plus: CSP/Permissions-Policy/nosniff headers in
  `frontend/src/proxy.ts`; WhatsApp webhook HMAC verification
  (`whatsapp_app_secret`); document-upload MIME+extension allowlist;
  TOTP secrets Fernet-encrypted (`enc:v1:` prefix); `users.token_version`
  JWT revocation (bumped on password reset/change); root `SECURITY.md` +
  vulnerability-report card on /siguria (×6); weekly dependency scan
  `scripts/security_scan.sh` via `avokatim-secscan.timer` (Mon 07:30,
  reports to Halim, log `data/security-scan.log`).
  `scripts/isolation_check.py` also asserts RLS coverage + SQL-level probes.
- **Auth**: public self-service signup (`POST /auth/signup` → new tenant on a
  **365-day trial** ("viti i parë falas", `platform_billing.TRIAL_DAYS`,
  extended from 90 on 2026-07-28) + admin
  user; page `/regjistrohu`), JWT login, 2FA (TOTP),
  email verification (signed purpose tokens, page `/verifiko-email`, banner +
  resend in app), password reset (`/harrova-fjalekalimin` → `/rivendos?token=`,
  single-use via password-hash fingerprint), change password (Settings →
  Profile). Login rate limiting via Redis (5 fails/15 min per email+IP → 429).
  `get_current_user` validates the JWT tenant claim, blocks suspended tenants,
  expired trials, and enforces the per-tenant `require_2fa` policy (members
  without TOTP can only reach `/api/auth` until they enable it).
- **Multi-company SaaS** (2026-07-09): Tenant carries `plan`
  (trial/solo/firm), `status` (active/suspended), `seats_limit`,
  `trial_ends_at`, `plan_price_eur`, `billing_notes`, `require_2fa`, `logo`.
  Seat limits enforced on team invite/reactivation (402). Trial banner +
  verify-email banner in the app shell. **Platform panel** (`/platform`,
  superadmin only — flag `users.is_superadmin`, never settable via API):
  list tenants with seats/matters/status, suspend/activate, change
  plan/seats/price, extend trial, billing notes, **platform invoices**
  (list/generate/mark-paid/void). The founder user is superadmin; founder
  tenant is plan=firm/25 seats/price 0 (never billed).
- **Platform subscription billing** (2026-07-11, D-016 — replaces manual
  D-008): revenue model = lawyers pay `plan_price_eur` (default **24
  €/user/month**, per-tenant override; 0 = free forever) which includes the
  whole platform + unlimited marketplace leads; citizens never pay; **never a
  % of lawyer fees** (Avvo Legal Services died of fee splitting).
  `PlatformInvoice` model (unique tenant+month, number P-YYYY-NNNN);
  `app/services/platform_billing.py`: `TRIAL_DAYS=365`, due 14 d, grace 14 d,
  idempotent monthly generation + **daily billing loop** (lifespan task,
  every 12 h): issues current-month invoices + emails admins, weekly dunning
  reminders (Redis dedup), trial-ending nudges (≤7 d). Tenant-admin API
  `/billing/subscription` (state+invoices), `/upgrade` (self-service trial →
  solo/firm, first invoice issued instantly), `/invoices/{id}/payment-link`
  (Stripe Checkout, metadata `platform_invoice_id`, same `/api/stripe/webhook`
  marks it paid). **Enforcement**: open invoice > due+grace ⇒ `past_due` —
  marketplace claim returns 402 and Tregu/Settings show a red banner; data
  access is NEVER blocked (operator may suspend chronic non-payers).
  Settings → "Abonimi" section (plan, price×seats, upgrade CTA, invoice list,
  card-pay button, bank-transfer hint from `platform_bank_details` in
  backend/.env — set it before the first real invoice!). Emails in 6 langs
  (`platform_invoice_*`, `platform_overdue_*`, `trial_ending_*`).
  Tests `tests/test_platform_billing.py`; simulation section 28.
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
- **Lawyer onboarding funnel** (2026-07-13): signup redirects to the
  `/onboarding` wizard (3 steps: public profile → OAK license + consult fee →
  optional booking hours; skippable, saves via `PUT /marketplace/profile`).
  Welcome email with next steps at signup (`lawyer_welcome_*` ×6); the
  verification email now uses `tr()` too. One-shot email nudges from
  `reminder_loop`: lawyer with inactive public profile 48h after signup,
  citizen with unverified email after 24h (columns
  `users.profile_nudge_sent_at`, `citizen_users.verify_reminder_sent_at`;
  only accounts ≤14 days old are ever nudged). **Activation follow-up**
  (2026-07-28, D-030): verified citizens with no posted case get one email
  48h after signup (`citizen_users.case_followup_sent_at`, ×6 languages).
- **Last industry gaps** (2026-07-28, D-032): **Payments abstraction** —
  `services/payments.py` dispatches on `payments_provider` (`stripe` |
  `raiffeisen`); Raiffeisen adapter skeleton + `verify_raiffeisen_callback`
  (finalize field names when the bank contract lands — steps in
  `docs/integrimet/raiffeisen-pagesat.md`). Manual pay-by-link:
  `PUT /invoices/{id}/payment-link` (https-only) + paste/edit UI; the auto
  link button gates on `GET /payments-config`. **Passive time capture** —
  `time_suggestions` table; `services/time_capture.py` turns audit-log
  activity into per-(matter, user, day) suggestions (cap 120 min, idempotent),
  generated nightly in the reminder loop + on-demand; accept → real
  `TimeEntry`, UI in billing + dashboard card. **Office Ava** —
  `POST /assistant/office-ask`: LLM picks one of 8 fixed tenant-scoped SQL
  tools, then phrases the answer in the UI language; "Zyra" segment with 6
  chips on the assistant page. **Auto review request** —
  `case_requests.review_request_sent_at`, one-shot email 48h after a claimed
  case concludes (×6, COMMS.md updated). **Flat-fee services** —
  `lawyer_profiles.flat_services` (≤10 × {title, price_eur}), editors in
  Settings + onboarding, section on `/avokatet/[id]`, chip in the directory.
  Operational: after `npm run build`, restart `avokatim-frontend`
  explicitly (it is not covered by `restart avokatim`).
- **UI audit wave** (2026-07-28, D-031): **Lawyer profile pages** —
  `/avokatet/[id]` (server layout: metadata + Attorney JSON-LD; client page:
  big trust numbers, CTA card, anonymized reviews) backed by
  `GET /public/lawyers/{profile_id}`; `BookingWidget` shared component;
  dynamic sitemap includes profiles. **Landing stats** — 554 laws · 141 ONK
  notaries (`notaries_licensed` in `/public/stats`) · 6 languages · 24/7;
  lawyer count self-restores at ≥20 in the directory. **Bio sanitizer** —
  `_scrub_bio` in `PUT /marketplace/profile` drops bio lines with
  email/phone/birth-date (tested). **Settings map** — 5 anchored groups
  with sticky sidebar / mobile chips (`#grp-zyra|publik|ai|njoftimet|siguria`).
  **Analytics charts** — /reports renders 6-month trend (SVG bars) + A/R
  aging from `/reports/dashboard`. **What's-new card** on the dashboard
  (versioned localStorage key). **Directory** — trust chips, profile links,
  booking as a real button. **/afatet** — quick chips for the 5
  most-searched deadlines. **/per-qytetaret** — 6-question FAQ accordion ×6
  + FAQPage JSON-LD sourced from the sq dictionary.
- **Industry-gap wave** (2026-07-28, D-030): **GEO** — schema.org JSON-LD
  server-rendered (Organization/WebSite on `/`, Attorney ItemList on
  `/avokatet`, Notary ItemList on `/noteret`), per-page metadata via server
  `layout.tsx` on 9 public pages, `robots.ts` + `sitemap.ts`. **Trust
  signals** — `lawyer_profiles.career_start_year` (onboarding + Settings)
  and computed `cases_completed` shown on directory cards and in
  `/public/lawyers`. **Office memory** — `tenants.assistant_style`
  (GET/PUT `/assistant/style`, Settings card) appended to Ava's office
  system prompt. **Agentic "Përgatit lëndën"** —
  `POST /assistant/matters/{id}/prepare` (SSE): reads the file, derives
  legal questions, searches corpus per question, streams situation + legal
  basis + next steps + risks + a draft after `=== DRAFT-SHKRESA ===`;
  matter AI tab has the button with live steps, draft copy + `.docx`
  download (`POST /assistant/export-docx`). **Client timeline** — the
  `rasti-im` stepper shows the date each stage was reached.
- **Agentic AI — Phase 3 of the improvement backlog** (2026-07-13, D-022):
  **Deep research**: `POST /assistant/deep-research` (SSE) — LLM decomposes
  the question into 3–5 sub-questions, each searched in the corpus, one
  synthesis with merged deduped citations; assistant UI has a "Hulumtim i
  thelluar" toggle with a live step list. **Clause assist**:
  `POST /templates/ai-assist` (draft + instruction → improved text + risk
  flags + changes) with an accept/discard panel on the templates page.
  **Document summaries**: `POST /documents/{id}/summarize` (summary + key
  points + possible deadlines), cached in `documents.ai_summary`
  (migration `31de290208e7`), button + modal in the matter Documents tab.
  All three go through `get_provider()` and respect `allow_external_ai`.
  **Public /siguria** page (×6) linked in footer + /per-avokatet.
  **e-Kosova readiness** doc: `docs/integrimet/e-kosova.md` + section in
  the government pitch.
- **Growth features — Phase 2 of the improvement backlog** (2026-07-13):
  **Founder badge**: `lawyer_profiles.is_founder` — auto-set for the first
  20 verified offices (`FOUNDER_LIMIT`), amber "Themelues" badge in
  `/avokatet` + program section on `/per-avokatet`. **Referrals**:
  `tenants.referral_code`/`referred_by_code`, `?ref=` on `/regjistrohu`
  (recorded in audit), `GET /marketplace/referral` (lazy code + referred
  count), share section in Settings; outreach drafts in
  `docs/rekrutimi/kontakt-oak-dhe-avokatet.md`. **Ava-intake**:
  `POST /api/public/ava/structure-case` (LLM → JSON
  `{category, description, city, urgency}`, rate-limited); "Më lidh me
  avokat" on `/ava` stores the structured draft and `/posto-rastin`
  prefills form fields from it (legacy plain-text drafts still work).
  **WhatsApp stub** (`app/api/whatsapp.py`, `docs/integrimet/whatsapp.md`):
  `GET/POST /api/public/whatsapp/webhook` — Meta handshake, inbound text →
  Ava answer via Graph API; logs-only until `WHATSAPP_TOKEN/PHONE_ID/
  VERIFY_TOKEN` are set; daily per-number quota. **iOS push guide + SMS
  alerts**: Safari "Add to Home Screen" instructions in Settings → push;
  `lawyer_profiles.phone` + `sms_case_alerts` — matching new-case and SOS
  notifications also via the Twilio-compatible SMS service when configured.
  **Paid consultations**: lawyer with `consult_fee_eur` + Stripe configured
  ⇒ booking created as `pending_payment` (+ `fee_eur`) with a Stripe
  Checkout link (`metadata[booking_id]`, return to `/rasti-im`); the
  existing `/api/stripe/webhook` flips it to `pending` and only then
  notifies the lawyer; `pending_payment` holds the slot; Stripe error or no
  key ⇒ free flow unchanged. Migrations `c3a3e4c5a37f`, `8fc9637a45d9`,
  `e0c562b27017`.
- **Automated professional outreach** (2026-07-14): `avokatim-outreach.timer`
  (systemd user unit, daily 09:30, `Persistent=true` → catches up after a
  reboot) runs `backend/scripts/oak_outreach_campaign.py`: 30 personalized
  emails/day, same-day guard against double batches, dedup via
  `data/oak_outreach_log.csv` (now with `audience` column), registered
  users/citizens auto-suppressed from the DB. Phase 1 lawyers
  (`data/oak_registry.csv`), then automatically phase 2 notaries
  (`data/notaries.json`) with a notary letter. Output → `data/outreach.log`.
- **Feedback lives in-platform only** (2026-07-14): `/kontakti` submissions
  no longer email the operator; `GET /platform/feedback/pending-count`
  powers a red badge on the Platform nav item (app sidebar).
- **OpenClaw operations assistant "Halim"** (2026-07-18, D-027): the local
  OpenClaw gateway relays everything to the owner on Telegram.
  `services/ops_notify.py` pushes operator events (signup, verification,
  SOS, case, feedback, booking) to `/hooks/agent` over loopback
  (`OPENCLAW_HOOK_TOKEN` in backend/.env; empty = disabled; test recipients
  suppressed). Hook runs are isolated sessions with no chat context, so the
  payload also carries the explicit delivery target (`channel=telegram`,
  `to=OPENCLAW_HOOK_TO`) — without it the gateway refuses the assistant's
  message-tool send as ambiguous and nothing reaches the phone. OpenClaw cron jobs run `scripts/ops_inbox_triage.py` (10-min
  read-only Gmail triage, state `data/ops/inbox_state.json`; replies drafted,
  sent only after owner approval via `scripts/ops_send_reply.py`) and
  `scripts/ops_digest.py` (08:30 morning report: 24h growth/marketplace
  numbers, pending verifications, feedback, overdue invoices, outreach tail,
  Umami traffic). Assistant rules: `~/.openclaw/workspace/AVOKATIM-OPS.md`.
  **Correspondence operator role** (2026-07-19, D-028): Halim replaces the
  owner for inbound human email — final ready-to-send draft on Telegram with
  a single "PO (dërgo) / JO (lëre)" question; never duplicates automatic
  letters. Outbound-communication map: `docs/agents/COMMS.md` (three lanes;
  every successful registration is thanked automatically — warm
  `verify_approved` letter with founder paragraph for professionals,
  `citizen_welcome` letter on citizen email confirmation).
- **Citizen social login** (2026-07-23): "Vazhdo me Google / Apple /
  Facebook" on the citizen auth form (`api/oauth_citizen.py`, server-side
  OAuth code flow at `/api/public/oauth/*`; token handed back in the URL
  fragment). Buttons appear per provider only when its `OAUTH_*` credentials
  exist in `backend/.env` (commented placeholders + redirect URIs are there).
  **Google is LIVE** (2026-07-23: GCP project `elemental-shine-503317-u9`,
  app "AvokatIM" published, flow verified end-to-end). **Apple is LIVE**
  (2026-07-24: team `6G9FRA7A53` / reYa Cloud LLC — App ID
  `ai.avokatiim.app`, Services ID `ai.avokatiim.web` = client_id, key
  `6B5M85MHN7`, .p8 at `backend/secrets/` which is git-ignored; flow
  verified to appleid.apple.com). **Meta is LIVE in dev mode** (2026-07-24:
  app "AvokatIM" `1330283695757341` with Facebook Login use case, `email`
  permission, redirect URI + basic settings filled; full flow verified on
  /kycu). Caveat: only app admins/testers can use the Facebook button until
  Meta **Business verification + Publish** are completed by the owner
  (developers.facebook.com → AvokatIM → Publish → Start Verification).
- **Marketplace case quality gate** (2026-07-13):
  `services/case_quality.py` — heuristics (repetition, gibberish, too short)
  + one fast LLM JSON classification (fail-open → `quality_flag="heuristic"`);
  rejects junk with a localized 400 (`case_quality_reject` ×6); accepted
  cases carry `case_requests.quality_flag` ("ok"/"heuristic").
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
- **AI deadline suggestions** (2026-08-01, D-043): automatic background scan
  on document upload / email attachment → `DeadlineSuggestion` rows matched
  against `DeadlineRule`; lawyer accepts (creates deadline via rule engine
  or direct date, audited) or dismisses. Banner in the matter Deadlines tab
  + dashboard card; `GET /deadline-suggestions`, `.../accept`, `.../dismiss`.
  Never auto-creates anything.
- **KI-Nutzung register** (2026-08-01, D-044): admin card in settings →
  security shows the office's AI usage from the audit trail (per action /
  user, effective LLM provider + data locality) with CSV export
  (`GET /firm/ai-usage`, `/firm/ai-usage.csv`) — BRAK KI-Leitfaden / DSGVO
  documentation duty.
- **AI-review gate on documents** (2026-08-01, D-044): documents rendered
  with AI assistance carry `ai_generated`; sharing with the client or
  requesting a signature is blocked until a human confirms review
  (`POST /documents/{id}/confirm-ai-review`, sets `ai_reviewed_by/at`,
  audited). UI: violet "KI-Entwurf" stamp with one-click confirm, turns
  green once reviewed. Plus a seeded DE office template
  `compliance.verarbeitungsverzeichnis` (Art. 30 DSGVO record covering the
  platform's AI features).
- **Rechtsschutz / Deckungsanfrage tracking** (2026-08-01, D-045, DE
  matters): overview tab card — pick an insurer from the seeded
  `DE_INSURERS` directory (12 carriers with service contacts), one click
  renders the `general.deckungsanfrage` letter into the matter as PDF and
  sets `insurance_status=angefragt`; lawyer records bestätigt/abgelehnt;
  after 14 days without answer the card nudges a follow-up
  (`GET/POST /matters/{id}/deckung[/anfrage|/status]`).
- **DE market positioning + Ratgeber** (2026-08-01, D-045): /per-avokatet
  on the DE host gets a "fixed subscription, 0 % commission per mandate"
  section (careful wording, no competitor named) and a BRAK-KI-Leitlinien
  compliance checklist. New public content: 10 curated German consumer-law
  guides at `/ratgeber/[slug]` (static data in `frontend/src/lib/ratgeber.ts`,
  Article JSON-LD, per-host canonical, DE-only sitemap entries, RDG-safe
  disclaimer, CTA → Ava / posto-rastin).
- **Token-less email classification** (2026-08-01, D-043): inbound mail
  without a matter alias whose sender matches a contact is parked as an
  `EmailSuggestion` (raw message encrypted on disk); dashboard card lets the
  lawyer file it into the suggested matter or dismiss (`/email-suggestions`).
- **Mahnwesen / dunning** (2026-08-01, D-043): overdue sent invoices carry
  `mahnung_level` 0–3; the billing page offers a one-click draft (client's
  locale, level-appropriate wording, +14-day deadline) that the lawyer edits
  and explicitly sends with the invoice PDF attached
  (`GET /invoices/{id}/mahnung/draft`, `POST .../mahnung/send`, audited).
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
  Providers: DeepSeek (default) or local OpenAI-compatible (Ollama/vLLM),
  selectable per request. DE ran on local gemma3:27b (D-037) but is
  **temporarily back on DeepSeek** (owner request 2026-08-01, full-feature
  demo); flip `PROFILES["DE"].llm_provider` to `"local"` before public
  launch (gate item 3).
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
  **Multilingual corpus** (2026-07-16): the gazette's official language
  versions (Law 03/L-190: sq/sr/tr/bs/en) imported via
  `import_gzk.py --lang sr|tr|bs|en` (GZK session-language postback, skip per
  (reference, language)); 9 of 11 laws exist in all five languages (08/L-182
  and 08/L-149 are Albanian-only PDFs). `rag.search_corpus(language=...)`
  filters to the question's language + sq fallback; public Ava and the lawyer
  assistant pass the UI locale, so citations quote the official text in the
  user's language ("Član 395" for sr, "Madde" for tr...). Chinese falls back
  to the Albanian corpus.
  **Notary laws added** (2026-07-13): Law on Notary 06/L-010 (80 chunks) +
  amendment 08/L-149 (MoJ PDF mirror). Amendment 08/L-272 (e-signature)
  has no machine-readable text online yet — see the note in `import_gzk.py`.
  **COMPLETE legislation import** (2026-07-19): `scripts/import_gzk_bulk.py`
  crawls the full GZK catalogue (constitution + amendments, 13 codes, 156
  consolidated acts, ~1,100 laws = 1,275 acts in `data/gzk_laws_index.json`)
  and imports every act in all 5 official languages. Resumable (skips
  existing (reference, language)); ~1/4 of acts are gazette-PDF-only and are
  fetched via the ActDetail image-button postback + pypdf. Re-run
  `--index` then `--lang ...` to pick up newly published laws. Log of the
  initial run: `data/gzk_bulk_import.log`. The public stat counts DISTINCT
  references (unique acts), not per-language documents.
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
  `CitizenUser` (own bcrypt password — **nullable** for social-login
  accounts, `oauth_provider`/`oauth_sub` since 2026-07-23, locale, email
  verification, `privacy_accepted_at`), `LawyerProfile` (opt-in public directory entry per
  tenant user: bio/areas/cities/languages/photo, `is_visible`), `CaseRequest`
  (open → claimed → converted / closed; optional `directed_tenant_id` for
  requests aimed at one lawyer from the directory), `CaseRequestMessage`
  (citizen ↔ claiming lawyer pre-intake chat). API `app/api/marketplace.py`:
  public `/public/citizen/*` (signup with mandatory privacy consent, login,
  verify-email via purpose token, cases CRUD, messages — Redis rate limits:
  5 signups/h/IP, 5 cases/day, 60 msgs/day; posting requires verified email;
  citizen JWT has its own `citizen` claim, unusable as lawyer/portal token),
  public `GET /public/lawyers` (visible profiles, filter area/city/language;
  paid-plan profiles sort first + `highlighted` flag — the "profil i
  theksuar" perk, soft indigo ring in `/avokatet`),
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
  `?verifiko=<token>`), **citizen-first landing at `/`** (see below;
  logged-in lawyers still auto-redirect to /dashboard);
  in-app `(app)/marketplace` ("Tregu" in nav) with open/mine tabs, claim +
  conflict warning + report; Settings → "Profili publik" section. Citizen
  token kept in `localStorage.avokatim_citizen_token`
  (`frontend/src/lib/citizen.ts`). ~60 new UI keys ×6 languages.
  Tests: `tests/test_marketplace.py`; `full_simulation.py` section 24.
- **Trust layer — OAK verification + reviews + transparent pricing**
  (2026-07-12, D-017): `LawyerProfile.oak_license_no` +
  `verification_status` (none/pending/verified/rejected) + `consult_fee_eur`;
  entering the license → pending + email to superadmins; operator decides in
  `/platform` (queue at top, `POST /platform/verifications/{id}/decide`,
  decision emailed ×6 locales). Verified is a hard gate for directory
  listing, match/SOS notifications, stats and claiming (403).
  **Auto-verification** (2026-07-18): `app/services/license_verify.py` —
  when the signup email is confirmed AND matches the public chamber
  registry exactly (OAK `data/oak_registry.csv`, ONK `data/notaries.json`),
  the license is approved automatically (audit action
  `platform.verification_auto`, approval email to the professional, FYI
  email to operators). Hooks: license submit (`PUT /marketplace/profile` →
  `_auto_verify_or_notify`) and email confirmation (`POST
  /auth/verify-email`). Name-only matches are never auto-approved
  (namesakes) — they stay in the queue with a hint badge
  (`registry_match` + `email_verified` in `GET /platform/verifications`). `CaseReview`
  (1:1 with concluded claimed case; communication/speed/clarity 1–5 +
  comment; POST/GET `/public/citizen/cases/{id}/review`); directory returns
  `verified`, `rating`, `review_count`, `consult_fee_eur`, ranked by plan
  tier then rating. UI: Settings license field + status pill + fee,
  /platform queue, /avokatet badge + stars + price, /rasti-im star form,
  /marketplace banner. Migration `16241f40c7cc`.
- **AI protection by phone — local voice + evidence vault + SOS screen**
  (2026-07-12, D-018): `app/services/voice.py` + `/api/public/voice/*` —
  **two STT models routed by language** (D-038): sq → Albanian CT2
  fine-tune, all other languages → stock `large-v3-turbo`
  (`data/models/whisper-cache`) because the fine-tune is unusable for
  German; both CUDA float16 (`voice_stt_device="auto"`, warm ~0.3 s on the
  RTX 5090, CPU int8 fallback). **Server TTS in 6 languages**: Piper
  voices in `data/models/piper-voices/{lang}.onnx` (de/en/tr/sr/zh +
  dedicated sq model); `/voice/status` returns `tts_langs`, client falls
  back to browser speechSynthesis for the rest (bs). All local (no audio
  leaves the machine), rate-limited — logged-in **lawyers** get the
  citizen-tier limits (staff JWT recognized, `voice.ts` sends whichever
  token exists). Settings `voice_*` in config.
  Evidence vault: `EvidenceSession`/`EvidenceChunk` — MediaRecorder chunks
  every 5 s, SHA-256 + `prev_hash` chain, strict seq (409), Fernet
  encryption, audit log, chain-of-custody PDF, background transcription;
  citizen CRUD at `/api/public/citizen/evidence/*`, read-only lawyer access
  on claimed cases. SOS screen (`sos-panel.tsx`): consent once → record
  evidence / push-to-talk with Ava (live transcript + spoken reply) /
  alert duty lawyers; dispatch attaches the recording to the case. Call
  recording is client-side (Web Audio mix → same vault, kind `call`) with
  a lawyer consent notice — LiveKit Egress deliberately not deployed.
  Voice controls (`voice-controls.tsx`) also in /ava and the assistant.
  Tests: `test_voice.py`, `test_evidence.py`; simulation sections 29–30.
- **Public tools + consultation booking** (2026-07-12, Phase 4 of D-018
  plan): deadline calculator `/afatet` (`/api/public/tools/deadline-rules`
  + `deadline-calc`, engine + holidays, no account); citizen document
  generator `/dokumentet` (deterministic Jinja→PDF templates in
  `app/seeds/citizen_docs.py`, no LLM) — **11 templates** with categories
  (Institucionet: kerkese/ankese/qasje_dokumente; Puna: verejtje_pune;
  Konsumatori: ankese_konsumatori; Të përgjithshme: autorizim/
  kundershtim_urdherpagese; Noteria: kontrate_veture/prokure/
  marreveshje_bashkeshortore/kerkese_trashegimie — flagged
  `requires_notary`, amber banner + /noteret link); both linked from the
  landing. Booking: `ConsultBooking` +
  `LawyerProfile.booking_enabled/booking_slots` (weekly windows, 30-min
  slots, 14-day horizon; migration `51f3b67b1756`); lawyer sets hours in
  Settings and confirms/declines in Tregu, citizen books from /avokatet
  and manages in /rasti-im; notifications ×6 (`booking_*` i18n keys).
  Tests: `test_bookings.py`; simulation sections 31–32.
- **Notary integration** (2026-07-13): the third bridge citizen → lawyer →
  notary, all informational (Law 06/L-010 requires physical presence — the
  platform never notarizes). Public page **`/noteret`** (×6 locales): act
  picker with type badge (akt noterial / solemnizim / vërtetim), fee
  estimate per AI 02/2012, "bring with you" document checklist, directory
  of 141 licensed notaries with city filter. Data: `app/seeds/notary.py`
  (fee brackets, acts, checklists — data not code) +
  `data/notaries.json` from `scripts/scrape_onk_registry.py` (public ONK
  registry, Cloudflare emails decoded; git-ignored, re-run to refresh).
  API: `GET /public/tools/notaries`, `GET .../notary-acts`,
  `POST .../notary-fee`. Public Ava routes notary matters and links
  /noteret. Strategic docs: `docs/rekrutimi/kontakt-onk.md` (draft ONK
  email), `docs/integrimet/e-noteria.md` (remote-notarization readiness).
  Tests: `tests/test_notary.py`. **Surfaced as third pillar** (same day):
  top-level "Noterët" link in the desktop header (after Avokatët), footer
  citizen column, `umbFnC8` bullet on `/`, fifth story section on
  `/per-qytetaret`, notary example chip on `/ava` (mobile bottom nav
  intentionally unchanged).
- **Notaries as the second paying profession** (2026-07-13, D-024):
  `Tenant.profession` ("lawyer" | "notary", migration `d4761aba9c68`) —
  same digital office + Ava + billing (per-seat, 365-day trial), no case
  marketplace (impartial public officer, fixed AI 02/2012 tariffs). Signup
  has "Jam avokat / Jam noter" cards (`/regjistrohu?profesioni=noter`
  preselects); notary welcome email variant (`notary_welcome_*` ×6);
  `/auth/me` exposes `tenant_profession`. Conditional UI: marketplace nav
  hidden, tagline "Zyra juaj noteriale moderne", settings/onboarding show
  ONK license instead of OAK and hide SOS/practice-areas/consult-fee/
  referral; matter detail says "Përgjegjësi". Marketing page
  **`/per-noteret`** (×6, violet), linked from `/` (umbFnL9) and a banner
  on `/noteret`. Verification: same queue; the registry match (email, then
  normalized name) now lives in `services/license_verify.py`
  (`registry_match`) and covers both professions, with email matches
  auto-approved (see the trust-layer entry above). Directory merge:
  `/public/tools/notaries` lists registered verified notary offices first
  (badge "I verifikuar në AvokatIM", equal listing — no promoted placement)
  and dedupes their scraped registry entry. Bookings: `/noteret` shows a
  slot picker for registered offices; the citizen can attach a prepared
  dossier (PDF ≤2 MB, `consult_bookings.attachment_name/attachment_b64`,
  migration `c24b4c54ac8f`; download via
  `GET /marketplace/bookings/{id}/attachment`); the notary sees requests in
  a shared `BookingsPanel` on the dashboard (no marketplace page). Claim
  guard: notary tenants get 403 on marketplace claims; excluded from
  /public/lawyers and public stats. Tests: `tests/test_profession.py`;
  simulation: `scripts/notary_simulation.py` (16 checks).
- **Two-surface restructure + citizen account** (2026-07-12, D-020):
  landing `/` is now the umbrella presentation — mission hero, two big
  audience cards, side-by-side full function lists (citizen ×7 / lawyer
  ×6), "Pse AvokatIM" advantages, stats, privacy card (`umb*` keys ×6).
  The citizen story moved to the new **`/per-qytetaret`** (Ava box hero,
  quick paths, 4 feature sections, how-it-works); `/per-avokatet` gained
  a 3-step marketplace walkthrough (`lpHiw*`). **Citizen account**:
  `PATCH /api/public/citizen/me`, `POST .../change-password`,
  `POST .../forgot-password` + `reset-password` (scoped `citizen_reset`
  purpose token, 1h, doubles as email verification; `citizen_reset_*`
  emails ×6). Frontend: shared `components/citizen-auth.tsx`
  (signup/login/forgot, reused by /posto-rastin, /rasti-im, /kycu),
  **`/kycu`** (citizen login + ?rivendos= reset form), **`/llogaria`**
  (profile, language, password, quick links, Dil), `PublicShell` header
  recognizes the citizen token (initials chip → Rasti im / Llogaria /
  Dil; otherwise "Kyçu" → /kycu), `/login` ↔ /kycu cross-banners,
  footer links. SW cache `avokatim-shell-v5`. Simulation includes the
  account flows (178 PASS / 0 FAIL).
- **Public redesign + platform feedback channel** (2026-07-12): shared
  public identity — `components/icons.tsx` (SVG set), `public-footer.tsx`
  (4 columns, mounted in `PublicShell`), shell header with backdrop-blur +
  "Vegla" dropdown. Landing `/` rebuilt as the full project story (hero +
  trust strip, "Çfarë është AvokatIM", 4 feature sections, how-it-works,
  privacy card, stats, lawyer CTA; `land*` i18n keys ×6). Page polish:
  /ava avatar + example chips, /avokatet sticky filters + skeletons,
  /posto-rastin step indicator + success screen, /rasti-im case timeline.
  Feedback (D-019): `PlatformFeedback` model (migration `391e7cf5703d`),
  `POST /api/public/feedback` (rate-limited 5/h/IP, anonymous OK, email to
  superadmins), page `/kontakti`, review section in /platform
  (`GET /platform/feedback`, `POST /platform/feedback/{id}/handle`).
  Tests: `test_feedback.py`; simulation section 31b.
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
- **Public stats + government pitch** (2026-07-11, Phase 4 groundwork of
  D-013): anonymous `GET /api/public/stats` (visible lawyers, cases
  posted/taken, avg hours-to-claim, corpus size) rendered as a stat strip on
  the public landing;   pitch document `docs/pitch/qasje-ne-drejtesi.md`
  (Albanian, for the Ministry of Justice / OAK / donors). Lawyer paid plans
  are now real — see "Platform subscription billing" above (D-016).
- **SOS duty flow + lead limits** (2026-07-11, Phase 3 without video +
  Phase 4 revenue scaffold): `LawyerProfile.sos_on_duty` (opt-in toggle in
  `(app)/marketplace` header and settings public-profile section).
  Citizen `POST /api/public/citizen/sos` — needs a citizen account but NOT
  a verified email (emergencies), rate limit 2/24h per citizen; creates a
  `CaseRequest` with `urgency="sos"` and background-notifies every on-duty
  lawyer via push + email (`sos_alert_*` i18n keys, 6 languages). SOS cases
  sort first in lawyer browse and carry a red SOS badge on both sides;
  red SOS button on `/rasti-im` (auto-opens with `?sos=1`, linked from
  landing). First lawyer to claim wins; normal claim → intake → chat flow.
  **Lead limits**: trial plan = 5 claims/calendar-month
  (`TRIAL_MONTHLY_LEAD_LIMIT`, claim returns 402 when exhausted), solo/firm
  unlimited; `GET /api/marketplace/lead-quota` (now also returns `past_due`)
  shown in the Tregu header. Simulation section 26.
- **Demand↔supply matching** (2026-07-11): posting a non-directed case
  background-notifies (push + email, `case_match_*` ×6) every visible lawyer
  whose `practice_areas`/`cities` match (empty profile lists = match all);
  lawyer browse is ranked SOS → directed-to-me → profile match (category+2,
  city+1) → recency, each row carries `matches_profile` (green chip in Tregu).
- **SOS video/audio room** (2026-07-11, Phase 3 complete for LAN):
  self-hosted **LiveKit** (`livekit/livekit-server:v1.9` in docker-compose,
  signaling 127.0.0.1:7880, media 7881/tcp + 7882/udp, config
  `livekit.yaml`; API keys in root `.env` → container env `LIVEKIT_KEYS`
  and in `backend/.env` → `LIVEKIT_API_KEY/SECRET` — must match).
  Backend `app/services/livekit.py` mints HS256 join tokens (no SDK,
  pyjwt; 4h TTL, single-room grant); `POST /api/marketplace/cases/{id}/
  call-token` (lawyer) and `/api/public/citizen/cases/{id}/call-token`
  (citizen) hand both sides tokens for the same `sos-<case_id>` room on
  claimed/converted cases, audit-logged; `enabled:false` graceful when
  keys are missing. Frontend `src/components/video-call.tsx`
  (livekit-client): full-screen overlay with local preview, mic/cam
  toggles, hang-up — "Thirrje video" buttons in Tregu and `/rasti-im`.
  Signaling URL is derived client-side: `ws://127.0.0.1:7880` on
  localhost, `wss://<host>:7443` on LAN (Caddy :7443 proxies to 7880
  with the internal CA cert). Simulation section 27
  (**133 PASS / 0 FAIL** total with section 28).
  **Remaining for public-internet calls** (owner's decision/action):
  WebRTC media cannot cross Cloudflare Tunnel (HTTP-only) — needs router
  port forwarding of 7881/tcp + 7882/udp (then `use_external_ip: true`
  in `livekit.yaml`) or a small TURN relay VPS (coturn), plus a public
  wss route for signaling. Calls work today on localhost and LAN
  (https://<ip>:8443 + :7443).
- **Citizen-first public UX** (2026-07-11, after web research on Avvo/
  JustAnswer/Airbnb + 2026 marketplace UX; analysis canvas
  `nderfaqja-qytetar-vs-avokat`): "two experiences, one platform".
  `src/components/public-shell.tsx` wraps all citizen pages (`/`, `/ava`,
  `/avokatet`, `/posto-rastin`, `/rasti-im`): desktop = slim header with
  text nav + SOS button + discreet "Për avokatët" link; mobile = fixed
  **bottom navigation** in the thumb zone (Ava · Avokatët · Posto ·
  Rasti im) with an **elevated red SOS button dead-center** (48px+
  targets, `safe-area-inset-bottom`). Landing `/` is citizen-first:
  hero = Ava question box (JustAnswer pattern) that stores
  `localStorage.avokatim_ava_prefill` and routes to `/ava` which
  auto-asks it; 3 secondary action cards; stats strip; footer links.
  Lawyers get a dedicated dark marketing page **`/per-avokatet`**
  (6 feature bullets, plan comparison trial-vs-paid, signup/login CTAs)
  — the lawyer app itself is unchanged. PWA manifest: `start_url` is
  now `/` (role-routed) with long-press `shortcuts` SOS / Ava / Rasti im.
  ~20 new UI keys ×6 languages (`lp*`, `pn*`, `mkHeroTitle`,
  `mkForLawyersLink`).
- **Per-page onboarding intros** (2026-07-11):
  `src/components/page-intro.tsx` — dismissible "how this page works"
  card (localStorage `avokatim:intro:<key>`, collapses to a small "?"
  pill that reopens it). Mounted on all 4 citizen pages (`/ava`,
  `/posto-rastin`, `/rasti-im`, `/avokatet`) and 11 lawyer pages
  (dashboard, intake, matters, contacts, calendar, templates, assistant,
  billing, marketplace, reports, settings). Landing `/` gained a
  "Si funksionon AvokatIM" section (hiw* keys): the presentation
  narrative — one platform two worlds, 3 steps, free-forever note.
  All strings ×6 locales (`*IntroT`/`*Intro`, `hiw*`, `introShow`/`introHide`).
  Service-worker cache bumped to `avokatim-shell-v3`.

## Environment

- Host: owner's Fedora Linux machine; everything runs locally.
- **Public domain**: https://avokatiim.ai (+ www) and **https://de.avokatiim.ai**
  (Germany, same app — country from hostname, D-034) via **Cloudflare Tunnel** —
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
  `avokatim-redis` (6380), `avokatim-caddy` (host network, HTTPS 8443 app +
  7443 LiveKit wss), `avokatim-livekit` (7880 localhost signaling,
  7881/tcp + 7882/udp media), `avokatim-umami` (visit analytics, 127.0.0.1:3210,
  own `umami` DB inside avokatim-db, public at https://stats.avokatiim.ai via
  the tunnel; admin credentials noted in the compose `.env`; frontend loads the
  cookie-free script when `NEXT_PUBLIC_UMAMI_SRC/ID` are set in
  `frontend/.env.local` at build time).
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

- **Frontend restart discipline** (incident 2026-08-01): after `npm run
  build` you MUST `systemctl --user restart avokatim-frontend` — restarting
  `avokatim` (backend-only unit) leaves the old `next-server` serving 404
  chunks over the new build. Mobile audit 2026-08-01 (JOURNAL i): SEO is
  per-host now (D-039, `lib/seo.ts`); `/ava` no longer crashes on browsers
  without `crypto.randomUUID`; tap-targets ≥ 24 px on public + app pages.
  Legal pages (kushtet/privatesia/impressum/kontakti) still have static
  Albanian metadata on the DE host.
- ~~`start.sh` skips `npm run build`~~ fixed 2026-07-07: `start.sh` now rebuilds
  automatically when any file in `frontend/src`/`public` is newer than
  `.next/BUILD_ID`, and kills the stale `next-server` before starting a fresh one
  (a stale server over a new build serves 404 chunks → blank pages).
- ~~SMTP not configured~~ done 2026-07-07: Gmail App Password in `backend/.env`
  (SMTP_* vars, smtp.gmail.com:587 STARTTLS, from arifi.arber@gmail.com).
  Test email sent and delivered — both reminder channels (email + push) active.
- ~~Host has no GPU tooling / Ollama unconfigured~~ changed 2026-08-01
  (D-037): the machine has an RTX 5090 (32 GB VRAM), Ollama serves
  `gemma3:27b` (17.5 GB VRAM, ~50 tok/s); `LOCAL_LLM_MODEL=gemma3:27b` in
  `backend/.env` and DE requests use it (`llm_provider="local"`).
  XK still uses DeepSeek.
- E-signature is the simple flow (typed name + SHA-256 + audit); qualified
  eIDAS/Kosovo e-signature law compliance is future work.
- ~~PUBLIC_BASE_URL placeholder~~ set to https://avokatiim.ai (2026-07-10;
  was boraarifi.ai before).
- Caddy serves a self-signed cert on :8443 (browser warning is expected on LAN).

## Jurisdictions

- **XK (Kosovo): active** — deadline rules, holidays, templates seeded.
- **DE (Germany): active** (2026-08-01, D-034) — profile in
  `app/jurisdictions.py`, seed data in `seeds/germany.py`, 99-act corpus
  (78 federal laws + DSGVO + 20 Landesrecht acts NW/BY, D-035) + federal
  case law BGH/BAG/BVerfG (D-042, importing), hybrid retrieval,
  host `de.avokatiim.ai`. Market parity D-037: RVG engine, ZUGFeRD
  e-invoices, Rechtsschutz flow, DATEV export, local LLM (gemma3:27b);
  DE advancement wave (D-040+): Prozesskostenrechner (F1),
  Online-Verfahren assistant (F2), deep research (F3),
  back-office suggest→accept agents (F4: deadline suggestions,
  Mahnwesen, token-less email classification);
  beA pending BRAK registration. SOS + notary off; public launch gated by
  `docs/legal/DE-LAUNCH-GATE.md`.
- GB, CN, INTL: schema-ready, no data yet.
