# JOURNAL — chronological work log

> Append one entry per session/task, newest at the top. Keep entries short:
> what was done, what was verified, what's left. Format:
>
> ```
> ## YYYY-MM-DD — <short title> (<agent/model if known>)
> - Done: ...
> - Verified: ...
> - Left open / next: ...
> ```

## 2026-07-09 — Fix: Bora "NetworkError" on long answers (Cursor / Fable 5)

- Bug: asking Bora on `/assistant` sometimes showed "NetworkError when
  attempting to fetch resource". Cause: the Next.js `/api` rewrite proxy has a
  **30s default timeout** (`proxy-request.ts`); DeepSeek with thinking mode can
  exceed it — the backend kept working and logged 200, but the browser
  connection was already dropped.
- Fix: `experimental.proxyTimeout: 300_000` in `frontend/next.config.ts`
  (headroom over the backend's 180s LLM timeout). Rebuilt + restarted.
- Verified: end-to-end ask through the :3000 proxy → answer with 6 citations
  in ~28s; health OK.

## 2026-07-09 — P2 differentiators: trust ledger, OAK tariff, .docx, email-in, SMS, Stripe, legal docs (Cursor / Fable 5)

- Done: **client funds ledger (trust)** — `TrustTransaction` model, API
  (`/trust/transactions` CRUD + `/trust/balances`), withdrawal beyond the
  balance is rejected (400), new "Mjetet e klientit" tab in Billing with
  per-matter balances + transaction table; included in tenant export
  (`mjetet_e_klientit.csv`).
- Done: **Kosovo Bar Association fee tariff as data** — `FeeTariffItem` model,
  17 seeded rows from the OAK tariff in force since 01.01.2015 (criminal
  120/150/200 €, civil submissions/hearings 60/80/160 € by value, enforcement,
  misdemeanor, contracts; surcharges documented in `notes`), `GET /fee-tariff`,
  picker in the invoice form that prefills description + price.
- Done: **.docx rendering** — `app/services/docx_render.py` (python-docx; A4,
  2.5 cm margins, Times New Roman 12pt, 1.5 spacing, bold centered title,
  ALL-CAPS lines as headings), `POST /templates/render-docx`, "Shkarko .docx"
  button on the templates page (`apiDownload` now supports POST bodies).
- Done: **email-to-matter** — `app/services/email_ingest.py` IMAP poller
  (lifespan task, disabled without `imap_host`); each matter gets a lazy
  `email_token` → alias `user+token@domain` (plus addressing), shown with a
  copy button in matter Overview (`GET /matters/{id}/email-address`, 404 when
  unconfigured). Inbound mail becomes a matter note; attachments become
  encrypted matter documents (category "email"); Redis dedup by Message-ID.
- Done: **SMS channel** — `app/services/sms.py` (Twilio-compatible REST via
  httpx, disabled without `sms_account_sid`); hearing reminders now also SMS
  the matter's client (separate Redis dedup key).
- Done: **card payments** — `app/services/payments.py` (Stripe Checkout via
  raw HTTPS, no SDK), `POST /invoices/{id}/payment-link` stores
  `payment_link`/`stripe_session_id`, link included in the invoice email,
  "Krijo link pagese" button + link display in UI; unauthenticated
  `POST /api/stripe/webhook` (HMAC signature verification + replay guard)
  marks the invoice paid on `checkout.session.completed`.
- Done: **legal docs** — `docs/legal/marreveshja-e-perpunimit-te-te-dhenave.md`
  (LMDhP model per Law 06/L-082) and `docs/legal/sla.md` (99.5%, P1–P4
  response times, RPO/RTO, credits) in Albanian.
- Migration `f9dabb704d14`: trust_transactions, fee_tariff_items,
  invoices.payment_link/stripe_session_id, matters.email_token. New settings
  in `config.py`: imap_*, sms_*, stripe_* (all optional; features degrade
  gracefully when unset). requirements: + python-docx.
- Verified: full_simulation extended to steps 16–19 → **66 PASS / 0 FAIL /
  0 GAP**; pytest 13 passed; frontend builds; health OK; demo tenant reseeded
  with 4 trust transactions; demo scenario updated (objection answers now
  "Po" for email/cards/tariff/SMS/.docx/DPA-SLA).
- Left open / next: Stripe/IMAP/Twilio need real credentials in `backend/.env`
  to activate (graceful 400/404/off otherwise); Stripe webhook needs the
  public URL routed to `/api/stripe/webhook`.

## 2026-07-09 — Demo readiness: all P0 blockers + 2026 table-stakes + demo package (Cursor / Fable 5)

- Done (P0): invoice PDF service (`app/services/invoice_pdf.py`, WeasyPrint,
  fiscal identity + new `Tenant.bank_details` field) with `GET /invoices/{id}/pdf`
  and `POST /invoices/{id}/send` (emails the PDF via extended `send_email` with
  attachments, sets status→sent); portal email notifications both ways (lawyer
  message → client, signature request → client, client message/signature →
  responsible lawyer); client documents in portal (`Document.visible_to_client`
  + `POST /documents/{id}/visibility` toggle + portal list/download endpoints +
  portal UI section); templates now render missing variables as `__________`
  placeholders (custom Jinja Undefined, no more 400), prefill `authority`/
  `court_case_number` from the matter, and `POST /templates/render-to-matter`
  saves the (editable) rendered text as a searchable matter PDF document.
- Done (P1): `Task` model + CRUD API + Detyrat tab in matter + "Detyrat e mia"
  dashboard card; `Expense` model + API + billing tab + auto-include in invoice
  (`include_unbilled_expenses`); global search `GET /search?q=` (matters,
  contacts, documents incl. text, invoices; respects restricted visibility) +
  search box above content on all pages; inline document preview endpoint +
  modal (PDF iframe / image); admin audit-log viewer + full tenant export
  (`GET /export/tenant` → ZIP of CSVs + decrypted documents) in Settings;
  manual flat-fee invoice items in the invoice form. All strings in sq/en/zh.
- Done (P3): `backend/scripts/seed_demo.py` — resettable "Zyra Demo" tenant
  (8 matters across stages, rule-based deadlines + hearings, 4 PDF docs, tasks,
  time+expenses, paid+draft invoices, portal client with messages and pending
  signature; logins demo@boralaw.app / klienti.demo@boralaw.app); demo script
  `docs/pitch/skenari-demo.md` (20-min flow + objection answers); extended
  `full_simulation.py` with steps 12–16 covering all new features.
- Migration `17000f590312`: tenants.bank_details, documents.visible_to_client,
  tasks, expenses.
- Verified: full_simulation → **56 PASS / 0 FAIL** (remaining GAPs are the
  post-first-clients backlog: trust ledger, email integration, .docx, SMS,
  card payments); pytest 13 passed; frontend builds; health OK; demo tenant
  seeded and login verified.
- Fixed along the way: `template.variables` is a list of dicts (500 in
  render-to-matter); tenant export lazy-loaded invoice items in async context
  (added selectinload).
- Left open / next: P2 differentiators (email-to-matter, client funds ledger,
  .docx templates, KCA fee tariff, SMS, card payments) — after first clients.

## 2026-07-09 — Critical pre-client audit: full E2E simulation + 12-competitor comparison (Cursor / Fable 5)

- Done: wrote `backend/scripts/full_simulation.py` — a reusable 40-step E2E
  simulation played from both sides (firm admin + portal client): signup →
  firm profile → team invite → public intake → conflict check → intake→matter
  → parties → deadline engine → PDF upload + text extraction + AI deadline
  extraction → doc review workflow → template render → Bora ask (7 citations)
  → time entries → invoice with VAT → payment → portal invite/login/messages →
  e-signature + certificate PDF → reports → ICS feed → gap probes. Result:
  39/40 PASS against the live stack (test tenant cleaned up after).
- Done: competitor research (subagent, web): PracticePanther, Rocket Matter,
  CosmoLex, Actionstep, Filevine, LEAP, Amberlo, Kleos, Lawmatics + regional
  (Legalistik, LEXA, Pametni Advokat, Juristi.al). Key finding: no practice
  management software exists today in Albanian or localized for Kosovo law.
- Done: audit canvas `auditimi-kritik-para-klienteve.canvas.tsx` (simulation
  results, P0 demo blockers, 2026 table-stakes checklist, lawyer vs company
  perspectives, 12-competitor matrix, price anchor chart, action plan).
- Findings (P0 demo blockers): no invoice PDF; portal is silent (no email
  notification to client on message/signature request); client cannot see
  matter documents in portal; rendered template is clipboard-only (not saved
  as a matter document, court/authority not prefilled from matter).
- Findings (2026 table-stakes gaps): no email-to-matter integration, no tasks/
  workflow, no matter expenses/disbursements, no global search, no trust/client
  funds ledger, no document preview, no audit log UI, no tenant data export,
  no flat-fee billing, no SMS channel.
- Left open / next: implement P0 (~1 week) before any client demo; then P1
  (tasks, expenses, search, preview, audit UI, export, flat-fee), then P2
  (email integration, client funds ledger, .docx templates, KCA fee tariff).

## 2026-07-09 — Multi-company SaaS + mobile responsive/PWA (Cursor / Fable 5)

- Done (Mobile, rrjedha B): app shell with hidden-md sidebar + mobile top bar,
  hamburger drawer and bottom nav (`(app)/layout.tsx`); matters + contacts as
  card lists on phones, remaining tables in `overflow-x-auto`; matter tabs
  scroll horizontally; assistant collapses to one panel (conversation dropdown);
  dashboard charts stack; settings grids responsive; portal sign cards stack.
  PWA: maskable 512 icon, manifest scope/orientation, `sw.js` app-shell
  precache + cache-first statics + network-first navigations (API never
  cached), SW registered globally from the app layout.
- Done (SaaS, rrjedha A): migration `92f04aa14500` — Tenant gains
  plan/status/seats_limit/trial_ends_at/billing_notes/require_2fa/logo, User
  gains is_superadmin/email_verified_at (founder made superadmin, founder
  tenant plan=firm/25 seats). Public signup (30-day trial) + email
  verification + password reset + change password, all via stateless signed
  purpose tokens (D-008). Redis login rate limiting (5/15min → 429). JWT
  tenant-claim validation, suspended/trial-expired blocking and per-tenant
  require_2fa policy in `get_current_user`. Team invites by email
  (admin-only, invitee sets password at `/ftesa`; plaintext-password add
  endpoint removed), seat-limit enforcement (402). Superadmin platform panel
  (`/api/platform` + `/platform` page): tenant list with stats,
  suspend/activate, plan/seats/trial/notes. Isolation: corpus writes
  superadmin-only, `document_text` restricted-matter aware, portal login
  tenant-aware, ICS tokens expire (180 d). Tenant branding (logo + name) on
  portal and public intake. New pages: /regjistrohu, /verifiko-email,
  /harrova-fjalekalimin, /rivendos, /ftesa, /platform; trial + verify-email
  banners; onboarding checklist on dashboard. All strings in sq/en/zh.
- Verified: pytest 13 pass (new purpose-token tests); `tsc` + build clean;
  `scripts/isolation_check.py` 12/12 PASS; `scripts/saas_check.py` 27/27 PASS
  (signup→verify→reset→rate-limit→invite→seats→platform→suspend);
  health OK on localhost and https://www.boraarifi.ai.
- Left open: card payments (manual billing for now), per-tenant private
  corpus, multi-firm membership per email, Lighthouse PWA audit on a real
  phone (owner can test install on Android/iOS via boraarifi.ai).

## 2026-07-08 — Real legal corpus + XK template library + signature certificate (Cursor / Fable 5)

- Done (corpus): `backend/scripts/import_gzk.py` — downloads real Kosovo laws
  from Gazeta Zyrtare (ActDocumentDetail HTML; PDF fallback for laws GZK hosts
  only as postback, e.g. 08/L-182 via the MD mirror) and posts them to
  /corpus. Loaded 9 laws ≈ 4,000 article chunks: LPK, KPP, Criminal Code
  (2026 consolidated), LMD, Labor, Administrative Disputes, Business
  Organizations, Family, Data Protection. Removed the old test fragment.
  Fixed /assistant/ask to ground in the tenant's default jurisdiction when no
  matter is selected — citations were empty outside matters before.
- Done (templates): expanded `XK_TEMPLATES` from 3 to 12 — payment-order
  objection, labor lawsuit, administrative lawsuit (08/L-182), demand letter,
  NDA, service contract, employment contract (03/L-212), legal opinion,
  due-diligence checklist. Seeded idempotently at startup.
- Done (e-signature): Certificate of Completion PDF
  (`GET /matters/{id}/signatures/{sig_id}/certificate`, WeasyPrint, 400 until
  signed) + "Certifikata" download link in Documents tab; i18n sq/en/zh.
  Corrected the legal basis: Law 08/L-022 (not 06/L-037). Documented QTSP
  research in DECISIONS D-007 (Evrotrust + rTrust are the licensed providers).
  weasyprint added to requirements.txt.
- Verified: 9 pytest pass; tsc + build clean; Bora answers real questions with
  correct citations (LPK art. 176 appeal deadline; Labor Law art. 32 annual
  leave — 6 law citations each); NDA renders; E2E certificate flow
  (invite → sign in portal → 17 KB PDF, %PDF magic OK, 400 before signing);
  synthetic data cleaned; health + dashboard + boraarifi.ai all 200.
- Left open / next: ICL practice templates + real-file migration (after the
  meeting); QTSP integration for qualified signatures (next phase, D-007);
  LMDhP compliance docs; more laws can be added by extending
  `import_gzk.py` LAWS.

## 2026-07-08 — ICL offer folder + firm-readiness features (Cursor / Fable 5)

- Done (offer): researched ICL Law / Virtus Invesco (Mehmet Berisha), competitor
  pricing (Clio/Smokeball/MyCase July 2026), Kosovo market; produced a full offer
  canvas (3 models: SaaS €24/user/mo w/ 3-month pilot; license+source €18k;
  partnership €25k → 25–30% co-ownership) and exported it to
  `~/Desktop/Oferta-BoraLaw-ICL/` (HTML + WeasyPrint PDF + cover email text).
- Done (code): migration `3a316e59b755`. Per-matter permissions
  (`matters.restricted` + `matter_members`; enforcement centralized in
  `get_owned_matter` + `restricted_visibility_filter`, applied to matter list,
  upcoming deadlines, ICS feed, dashboard agenda; PUT
  /matters/{id}/members admin/responsible-only; audit-logged). Document approval
  workflow (request-review → approve/request_changes + review-inbox; "Rishikimi"
  column in Documents tab). CSV import (Settings → Data import, contacts +
  matters, template downloads). Fiscal invoices (tenant NUI/VAT/address/
  default_vat_rate 18% via GET/PATCH /firm, Settings → Firm profile; invoices
  carry vat_rate/vat_amount/total_with_vat, shown in Billing). i18n sq/en/zh
  for all new strings.
- Verified: 9 pytest pass; tsc clean; E2E script (temp lawyer): restricted matter
  hidden from non-member (list + direct 404) then visible after membership;
  review flow request→inbox→approve; CSV imports create 1+1 rows; VAT 18% math
  on a €100 invoice = €118. Synthetic data fully cleaned. Frontend rebuilt,
  stack restarted, health + dashboard + https://boraarifi.ai all 200.
- Left open / next: their practice templates + data migration with the pilot
  firm's real files; real corpus; qualified e-signature (Law 06/L-037 provider);
  LMDhP compliance docs; demo meeting with Mehmet Berisha.

## 2026-07-07 — Public domain live: boraarifi.ai via Cloudflare Tunnel (Cursor / Fable 5)

- Done: owner bought boraarifi.ai (Namecheap) + moved DNS to Cloudflare (free)
  + authorized `cloudflared tunnel login`. Installed cloudflared 2026.6.1 (rpm),
  created tunnel `boralaw`, CNAMEs for apex + www (--overwrite-dns over old
  parking records), config → 127.0.0.1:3000 (Next rewrites carry /api),
  systemd user service `boralaw-tunnel.service` (enabled, Restart=always).
  PUBLIC_BASE_URL=https://boraarifi.ai in backend/.env; stack restarted.
- Verified through the public internet: /login /dashboard /portal /apliko/{token}
  /manifest.webmanifest /sw.js /api/health /api/public/intake/{token} all 200 on
  https://boraarifi.ai and www; served by Cloudflare (cf-ray SOF); public-form
  and calendar-feed URLs now emit the domain. Owner also confirmed backup key
  copied to USB.
- Left open / next: real corpus (owner uploads laws), pilot firm demo, PWA
  install + push opt-in on owner's phone (now easy: valid TLS on the domain).

## 2026-07-07 — SMTP live via Gmail App Password (Cursor / Fable 5)

- Done: owner supplied a Gmail App Password; SMTP_* set in `backend/.env`
  (smtp.gmail.com:587, STARTTLS, user/from arifi.arber@gmail.com). Stack
  restarted; reminder loop now has both channels (email + push).
- Verified: real test email sent through `send_email` and delivered to the
  owner's inbox; dashboard still 200 after restart.
- Advised owner: no need to buy PositiveSSL from Namecheap — Caddy issues free
  Let's Encrypt certificates automatically once a domain points at the server;
  only the domain itself needs purchasing.
- Left open / next: domain purchase (owner), backup key off-machine (owner),
  real corpus, pilot firm.

## 2026-07-07 — Dashboard outage: stale next-server + full audit (Cursor / Fable 5)

- Root cause: owner saw a broken dashboard because the running `next-server`
  (started 14:50) predated the last `npm run build` (15:11) — old HTML referenced
  chunk files that the new build had replaced, so the browser got 404s on JS and
  pages never hydrated. Fixed by `systemctl --user restart boralaw.service` and
  **hardened `start.sh`**: it now rebuilds when `frontend/src`/`public` is newer
  than `.next/BUILD_ID` and kills the stale server before starting a fresh one.
- Full audit (all green): 9 pytest pass; alembic at head `fdb43a0e95bc`; every
  app page (/, login, dashboard, matters, contacts, calendar, intake, billing,
  reports, assistant, templates, settings, portal) returns 200; all 11 JS/CSS
  chunks referenced by /dashboard load 200; /api reports/dashboard + analytics,
  matters, invoices, time-entries, team, intake, templates all 200 with a real
  token; public intake page (/apliko/{token}) 200 + its public API OK; ICS feed
  200; Caddy HTTPS 200; containers healthy; boralaw.service + backup timer
  enabled (next run 03:00).
- Left open / next: SMTP app password (owner), real corpus, public domain.

## 2026-07-07 — OCR enabled on host (Cursor / Fable 5)

- Done: installed tesseract 5.5.2 + langpacks sqi/eng/chi_sim (owner provided
  sudo password in chat; not stored anywhere).
- Verified: `storage.extract_text` OCRs a synthetic Albanian scanned image
  (PNG) and an image-only PDF correctly, diacritics intact, status "done".
- Left open: SMTP still waiting on a Gmail App Password from the owner (owner
  offered the real Gmail password — declined and explained App Passwords).

## 2026-07-07 — Remaining backlog: backups, push, payments, firm reporting (Cursor / Fable 5)

- Done: migration `fdb43a0e95bc` (`push_subscriptions`, `invoices.paid_on` +
  `payment_reference`). Web Push end-to-end: VAPID keys generated into
  `backend/.env`, `services/push.py` (pywebpush, dead-sub cleanup), `/api/push/*`
  endpoints, `public/sw.js` service worker, opt-in section in Settings; reminder
  loop now runs when SMTP **or** push is configured and sends both channels.
  Invoices: mark-paid records date + bank reference (form in Billing UI).
  /reports/analytics gained `by_lawyer` (open matters, MTD hours vs target,
  utilization) — table shows when tenant has >1 active member. Encrypted daily
  backups: `backup.sh` (pg_dump + documents + .env, AES-256, retention 14) +
  `boralaw-backup.timer` (03:00, enabled); key at `~/.config/boralaw/backup.key`.
- Verified: 9 tests pass; API roundtrip (invoice paid with TRX ref, by_lawyer
  payload with temp member, push subscribe/unsubscribe) then synthetic data
  removed; backup ran and restore-tested (dump + docs + env decrypt OK);
  frontend built; stack restarted; reminder loop active with push channel.
- Host checks: tesseract NOT installed (sudo needs password — owner action in
  STATE); no GPU tooling, Ollama has no models — local LLM documented, not enabled.
- Left open: SMTP credentials, tesseract install (owner), local-LLM
  model decision, qualified e-signature, per-matter permissions, XK template
  library with pilot firm, real corpus from Gazeta Zyrtare, public domain+TLS.

## 2026-07-07 — Competitive-gap features implemented (Cursor / Fable 5)

- Done: implemented all suggestions from the full-app analysis in one batch.
  Migration `fc080e9898a0`: `matter_messages`, `signature_requests`,
  `tenants.intake_token`. New backend: `/api/team` (multi-user + roles,
  admin/lawyer manage), `/api/calendar/feed.ics` (ICS with signed token),
  `extract-deadlines` + `deadlines/bulk` (AI reads court doc → proposals →
  accept), matter/portal messages, signature request/sign/decline (SHA-256 +
  IP + timestamp, audit), `client-update-draft`, public intake
  (`/api/public/intake/{token}`), reminder loop (`services/notifications.py`,
  SMTP config in `config.py`, Redis dedup). `MatterOut/Update` now carry
  `responsible_user_id`.
- UI: Settings → Team/Calendar sync/Public form sections; matter page →
  Messages tab, responsible-lawyer select, per-document "Extract deadlines" +
  "Request signature", AI tab → client-update draft with send-to-portal;
  new `/portal` (client login, matters, chat, signature inbox); new
  `/apliko/[token]` public form; PWA manifest + generated icons.
- Verified: 9 tests pass; full E2E via API with synthetic data (portal login,
  message roundtrip both directions, sign flow, real DeepSeek extraction —
  found appeal deadline art. LPK + hearing date from a synthetic judgment —
  bulk accept created 2 deadlines, client-update draft in Albanian, ICS shows
  2 events, team member create/deactivate); synthetic data cleaned up;
  frontend built; stack restarted; /portal, /apliko/…, /manifest.webmanifest
  all 200.
- Left open: SMTP credentials (reminders auto-enable once set), push
  notifications for PWA, qualified e-signature, per-matter permissions,
  payment tracking, XK template library with pilot firm.

## 2026-07-07 — Full-app competitor analysis (Cursor / Fable 5)

- Done: researched full 2026 feature sets of Clio (Manage AI, Draft, Grow,
  Accounting), Smokeball (Archie AI, AutoTime, 20k forms) and MyCase (IQ,
  built-in e-sign/SMS). Compared 27 capabilities across 5 areas. Canvas:
  `~/.cursor/projects/home-kllosha-BoraLaw/canvases/krahasimi-i-plote-aplikacionit.canvas.tsx`.
- Scores: Clio 24/27, Smokeball 21.5/27, MyCase 20/27, BoraLaw 16.5/27.
  Our structural advantages nobody matches: XK procedural rules as data,
  RAG with article citations, self-hosting, local-LLM option, sq/en/zh UI.
  Biggest gaps: multi-user roles, e-signature, calendar sync, AI deadline
  extraction from court docs, online payments/messaging in portal.
- Added "Competitive gaps" section to ROADMAP with pilot-blocking priorities.

## 2026-07-07 — Financial analytics P2 implemented (Cursor / Fable 5)

- Done: migration `44cef654e97a` adds `users.billable_hours_target_monthly`
  (default 120) and `intake_requests.source` (referral|web|phone|walk_in|other).
  New `GET /api/reports/analytics`: utilization (MTD billable hours vs target),
  realization (billed/worked hours, 90d), collection (paid/issued value, 180d),
  intake funnel with per-source conversion (90d), profitability by practice
  area (180d). New `PATCH /api/auth/me` for profile/target updates.
- UI: new sidebar page "Analitika" (`/reports`) with color-coded rate cards
  (thresholds: utilization 70%, realization 85%, collection 90%), funnel and
  per-area profitability table; source select in intake form; monthly hours
  target editable in Settings → Profile.
- Verified: 9 tests pass; synthetic-data check of all analytics payloads
  (rolled back); frontend built; stack restarted; /reports returns 200.

## 2026-07-07 — Dashboard upgrade P1 implemented (Cursor / Fable 5)

- Done: extended `/api/reports/dashboard` with `today_agenda` (pending deadlines
  due today, joined with matter ref/title), `ar_aging` (sent invoices bucketed
  0-30/31-60/61-90/91+ days by issued_on), `monthly_trend` (last 6 months of
  worked hours + billed revenue; date_trunc via literal_column — bound params
  in GROUP BY break Postgres). UI: agenda card on top of dashboard, aging
  breakdown card, two CSS mini bar charts, `QuickTimer` component in the
  sidebar (localStorage-backed, saves to POST /time-entries on stop).
- Verified: 9 backend tests pass; synthetic-data check of all three new
  payloads (rolled back); frontend rebuilt; stack restarted, health OK.
- Gotcha: dictionary keys must be unique across the file (`selectMatter`
  already existed) — TS build enforces `en`/`zh` match `typeof sq`.

## 2026-07-07 — Dashboard competitor analysis (Cursor / Fable 5)

- Done: web research comparing our dashboard vs Clio, Smokeball, MyCase +
  2026 legal-KPI best practices (curate 5-7 KPIs; categories: financial/
  production/capacity/marketing; trends over static numbers). Result canvas:
  `~/.cursor/projects/home-kllosha-BoraLaw/canvases/dashboard-krahasimi.canvas.tsx`.
- Findings: we already have real-time clickable KPI cards and a unique
  differentiator (deadlines with procedural legal basis — nobody has that);
  main gaps are today-agenda, trend charts, A/R aging, utilization/realization,
  quick timer. Added as Dashboard P1/P2 items in ROADMAP Phase 2.

## 2026-07-07 — Sales pitch for Kosovo law firm (Cursor / Fable 5)

- Done: a law firm in Kosovo contacted the owner after he posted about the
  project. Wrote the presentation text (Albanian) in
  `docs/pitch/prezantimi-firma-avokatesh.md`, framed as a founding-partner
  pilot offer (their expertise shapes the firm module, Phase 3).
- Note for future agents: if the pilot happens, Phase 3 (roles, matter
  assignment, firm reporting) becomes top priority in ROADMAP.

## 2026-07-06 — Agent management system + autostart (Cursor / Fable 5)

- Done: created the agent operating system for this repo: root `AGENTS.md`
  (entry point for any LLM/agent), `CLAUDE.md` pointer, `docs/agents/`
  (STATE, JOURNAL, DECISIONS, ROADMAP). Made the first git commit.
- Done: `boralaw.service` (systemd user unit, enabled) so the stack starts on boot;
  hardened `start.sh` (waits for docker + DB health, skips rebuild when `.next` exists).
- Done: recovered the original project chat that was orphaned in Cursor
  (it had been run from an empty window; relinked it to this workspace).
- Verified: service starts stack from scratch; `/api/health` OK; frontend 200.
- Left open: nothing blocking. See ROADMAP for next steps.

## 2026-07-06 — Project foundation (Cursor agent, first session)

- Done: full MVP scaffold and implementation — FastAPI backend (models, API,
  services, LLM abstraction, Kosovo seeds, Alembic initial schema, tests),
  Next.js frontend (all pages, i18n sq/en/zh), docker-compose (pgvector, Redis,
  Caddy HTTPS), start/stop scripts, README.
- Verified: backend tests passing; stack running; UI functional at :3000.
- Left open: git repo initialized but no commits (fixed in next session).
