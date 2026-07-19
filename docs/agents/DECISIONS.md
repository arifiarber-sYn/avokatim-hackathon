# DECISIONS — architectural decision log

> Append-only. One numbered entry per decision. Never delete entries; if a
> decision is reversed, add a new entry that supersedes the old one.
> Format: context → decision → consequences.

## D-001: Web app, self-hosted on the owner's machine

- Context: owner wants full control, local data, and outside access for himself.
- Decision: web stack (FastAPI + Next.js) hosted on this computer; Caddy provides
  HTTPS on :8443 for LAN/external access.
- Consequences: no cloud costs or dependencies; machine must stay on; autostart
  handled by systemd user service.

## D-002: Multi-tenant and multi-jurisdiction from the foundation

- Context: solo lawyer today, law firms and more jurisdictions later; goal is a
  globally competitive product.
- Decision: tenancy models from day one; jurisdiction rules (deadlines, holidays,
  templates, corpus) are database *data* seeded per jurisdiction, never code.
- Consequences: adding a jurisdiction = writing seeds, not refactoring; Kosovo (XK)
  is the reference implementation.

## D-003: LLM-agnostic provider abstraction

- Context: LLM landscape changes fast; owner wants the option of a local model.
- Decision: all LLM calls go through `backend/app/llm/` (base interface + provider
  implementations + router). DeepSeek is the default; any OpenAI-compatible local
  endpoint (Ollama/vLLM) is a drop-in alternative, selectable per request.
- Consequences: swapping/adding an LLM touches one module only.

## D-004: Local embeddings; client documents never leave the machine

- Context: attorney–client privilege; documents are the most sensitive data.
- Decision: semantic indexing uses local sentence-transformers
  (multilingual MiniLM, 384 dims) + pgvector. Documents encrypted at rest (Fernet).
  Only assistant *prompts* (question + retrieved snippets) go to a remote LLM, and
  a local LLM removes even that.
- Consequences: indexing has no per-token cost; embedding model changes require
  reindexing the corpus.

## D-005: Deadline engine driven by named rules with holiday calendars

- Context: procedural deadlines are the highest-risk part of legal practice.
- Decision: deadline rules are seeded records (code, base event, period, unit,
  holiday handling) per jurisdiction, with official holiday calendars; the engine
  computes dates and is covered by unit tests.
- Consequences: legal changes are data updates; every rule change needs a test.

## D-006: Agent-agnostic project management via AGENTS.md + docs/agents/

- Context: owner switches between agents/LLMs; work continuity must not depend on
  any single tool's chat history.
- Decision: `AGENTS.md` is the universal entry point (with `CLAUDE.md` pointer);
  persistent memory lives in-repo: STATE (snapshot), JOURNAL (log),
  DECISIONS (this file), ROADMAP (direction). Session protocol in AGENTS.md §2.
- Consequences: every agent must follow the session protocol or the system decays.

## D-007: E-signature legal basis and the path to qualified signatures (2026-07-08)

- Context: AvokatIM's portal e-signature (typed name + SHA-256 + IP + timestamp)
  is a *simple* electronic signature. Kosovo's governing law is
  **Law No. 08/L-022 on Electronic Identification and Trust Services in
  Electronic Transactions** (in force 2022; earlier docs wrongly cited
  06/L-037). Art. 32 makes *qualified* e-signatures equivalent to handwritten;
  simple ones remain admissible under the non-discrimination principle.
- Decision: (1) ship a "Certificate of Completion" PDF (WeasyPrint,
  `GET /matters/{id}/signatures/{sig_id}/certificate`) documenting the evidence
  chain of the simple signature; (2) for qualified signatures, integrate later
  with a Ministry of Economy-licensed QTSP — as of 2026 the recognized
  providers are **Evrotrust Technologies JSC & IT Vision** (decisions
  no. 6269/15.12.2023 and 5404/16.08.2024) and **rTrust (PBC)**, both
  eIDAS-recognized in the EU. Integration would follow the same abstraction
  pattern as `app/llm/` (provider interface, swappable).
- Consequences: current signatures are legally usable evidence but not
  handwritten-equivalent; contracts requiring written form still need wet ink
  or a QTSP integration (planned, next phase; likely per-signature cost).

## D-008: SaaS architecture — stateless purpose tokens, manual billing, one responsive web app (2026-07-09)

- Context: converting the single-practice install into multi-company SaaS
  (benchmark: Clio/Smokeball/MyCase 2026) and making the same app usable on
  phones.
- Decisions:
  1. **Email flows use stateless signed JWTs** ("purpose tokens": verify_email
     / reset_password / invite) instead of a DB token table. Single-use for
     reset/invite is enforced by embedding a fragment of the current password
     hash (`fp` claim) — changing the password invalidates the token. Simpler,
     no migration, no cleanup job; trade-off: no server-side revocation list.
  2. **Billing is manual**: the superadmin panel records plan/seats/trial and
     payment notes; no card processor yet. Suspension/trial-expiry enforced in
     `get_current_user` (403), superadmin exempt.
  3. **One responsive web app** for desktop + mobile (Tailwind breakpoints +
     PWA), not a separate mobile design/native app. Bottom-nav + drawer shell
     in `(app)/layout.tsx`. Native apps remain a possible later layer.
  4. **Legal corpus is a shared read-only asset**: only the platform
     superadmin writes to it; tenants consume it. Per-tenant private corpus
     (a `tenant_id` column on corpus docs) is noted as a future extension.
  5. Email uniqueness stays **global** (one email = one account, like Clio);
     multi-firm membership per email is a future extension.
- Consequences: new auth surface (signup/verify/reset/invite/change-password)
  is covered by `scripts/saas_check.py`; isolation by `scripts/isolation_check.py`.
  Run both against the live backend after touching auth/tenancy.

## D-009: Optional integrations via raw APIs, config-gated, graceful degradation (2026-07-09)

- Context: the P2 differentiators (email-to-matter, SMS, card payments) need
  third-party services, but the product must run fully without them.
- Decisions:
  1. **No vendor SDKs**: Stripe (Checkout + webhook HMAC verification) and the
     SMS provider (Twilio-compatible REST) are called through httpx directly.
     Fewer dependencies, and the SMS base URL is configurable so any
     Twilio-compatible gateway works.
  2. **Config-gated features**: every integration is off until its .env keys
     are set (`imap_host`, `sms_account_sid`, `stripe_secret_key`), and each
     endpoint degrades cleanly (404 for the matter email address, 400 for
     payment links). The UI hides or reports accordingly — no broken buttons.
  3. **Email-to-matter uses plus addressing** on a single mailbox
     (`user+<matter token>@domain`) with a random per-matter `email_token`,
     instead of OAuth mailbox integrations per user. Works with any IMAP
     provider, zero OAuth complexity; token (not matter reference) prevents
     guessing. Full Gmail/Outlook OAuth sync remains a future option.
  4. **Trust ledger is append-style and non-negative**: withdrawals beyond the
     matter balance are rejected at the API; deleting a deposit that would
     make the balance negative is rejected too — client funds protection over
     convenience.
  5. **Bar fee tariffs are jurisdiction data** (`fee_tariff_items` table,
     seeded from the OAK tariff), consistent with D-002 (jurisdiction rules
     are data, not code).
- Consequences: activating an integration = adding keys to `backend/.env` and
  restarting; the Stripe webhook additionally needs the public URL routed to
  `/api/stripe/webhook`. Simulation checks assert the "off" behavior so the
  suite passes with or without credentials.

## D-010: Assistant answers stream via SSE (2026-07-09)

- Context: DeepSeek with thinking mode takes 60–180s. A single hanging HTTP
  request was killed by the Next.js proxy default 30s timeout, occasionally by
  the browser, and will always be killed by Cloudflare's ~100s idle limit on
  boraarifi.ai. Raising `proxyTimeout` was not enough.
- Decision: stream the answer end-to-end with Server-Sent Events.
  `chat_stream()` on the LLM abstraction (providers yield
  `("thinking"|"delta", text)`), `POST /api/assistant/ask-stream` streams
  meta/thinking/delta/done/error events and persists the exchange at the end,
  and the UI renders the text progressively. Thinking tokens are forwarded as
  keep-alive traffic (shown as an indicator, never persisted).
- Consequences: no idle timeout can drop a long answer anywhere in the chain
  (uvicorn → Next proxy → browser/Cloudflare); the lawyer sees the answer as
  it is written (better perceived latency). The non-streaming `/ask` endpoint
  remains for scripts/tests. Streaming endpoints must create their own DB
  session — the request-scoped dependency may close before the body finishes.

## D-011: Kosovo compliance is data + explicit records, not hidden logic (2026-07-09)

- Context: full compatibility with Kosovo law requires the Use of Languages
  law (02/L-37), the Data Protection law (06/L-082, GDPR-aligned) and the
  AML law (05/L-096, lawyers are reporting entities for real estate, client
  funds and company formation).
- Decisions:
  - **Languages**: six locales everywhere (sq/sr/tr/bs/en/zh). Client-facing
    output follows `Contact.locale` (fallback tenant default → sq) through
    the single backend catalog `app/i18n.py`; official documents (invoice
    PDF) are **bilingual** sq + client language via `bilabel()` rather than
    replacing Albanian. AI-translated legal templates are seeded but named
    "kërkon rishikim nga avokati" — never released without human review.
  - **Consent is a record, not a boolean**: `ConsentRecord` rows carry kind,
    grant/revoke timestamps, method and IP so consent is demonstrable
    (art. 7). Features that need consent (SMS) query the record at send time.
  - **Erasure = anonymization**: matter files must legally be retained, so
    the right to erasure strips identifiers from the contact and revokes
    consents instead of deleting rows; blocked while matters are open.
  - **Retention flags, never auto-deletes**: expired closed matters are
    listed for the lawyer's decision (`retention_years` per tenant).
  - **International transfers are a tenant switch**: `allow_external_ai`
    forces the local LLM provider server-side (not just hidden in UI), and
    the UI labels what leaves the country. Sub-processors are enumerated in
    the DPA Annex A.
  - **AML follows jurisdiction-as-data**: NjIF-K indicators and scope hints
    are seeds (`XK_AML_INDICATORS`), the per-matter checklist state lives in
    `Matter.extra["aml"]` (no schema churn), and suspicion reports are
    generated as PDFs for manual filing — the platform never notifies anyone
    automatically (tipping-off prohibition, art. 30).
- Consequences: adding a jurisdiction means adding data (indicators, rules,
  translations), not code; compliance features are auditable end-to-end
  (every consent, erasure, export, large deposit and report is in the audit
  log); one extra FK path tenants↔users required explicit `foreign_keys` on
  the membership relationship.

## D-012: Full rebrand BoraLaw → AvokatIM (2026-07-11)

- Context: the owner's daughter (the product's namesake) started working at a
  company with a similar product; keeping her name on the project could be
  seen as a conflict of interest. The public domain had already moved to
  avokatiim.ai.
- Decision: complete rebrand, not just user-facing strings — product name
  AvokatIM, assistant "Ava", new icons, and internal identifiers too: project
  folder ~/AvokatIM (with ~/BoraLaw compat symlink), DB user/db `avokatim`
  (dump/restore into a fresh cluster), containers/volumes `avokatim-*`,
  systemd units `avokatim*`, backups `~/AvokatIMBackups`. Two deliberate
  exceptions: the Cloudflare tunnel keeps its internal name `boralaw`
  (its ID is wired into both DNS zones; invisible to users), and AGENTS.md
  keeps one historical note so agents don't reintroduce the old names.
- Consequences: users must log in again (localStorage token key changed);
  demo credentials changed (demo@avokatim.app / Demo2026!ava); old
  `boralaw_boralaw_*` docker volumes kept temporarily as a safety net; old
  encrypted backups remain readable (same key, copied to the new path).

## D-013: Citizens as platform-level entities, marketplace-first (2026-07-11)

- Context: the owner wants AvokatIM to also serve citizens ("pocket lawyer"):
  find a lawyer, post a case, free legal AI, live SOS help — free for
  citizens, revenue from the lawyer side. The existing system is strictly
  tenant-scoped (lawyers) with per-tenant Contacts (clients).
- Decision: citizens are a **new platform-level identity** (`CitizenUser`,
  no tenant_id), NOT tenants and NOT contacts. A citizen's `CaseRequest`
  crosses into a tenant only at **claim**, which reuses the existing pipeline
  (conflict check → IntakeRequest source="marketplace" → accept → Contact +
  Matter). On conversion the Contact inherits the citizen's password hash so
  one set of credentials works for both the marketplace and the client portal.
  Lawyer visibility in the public directory is opt-in (`LawyerProfile
  .is_visible`), and open cases show a masked citizen name until claimed.
  MVP order fixed as: 1) marketplace, 2) public Ava, 3) SOS video/audio
  (self-hosted LiveKit + coturn per owner's choice), 4) monetization.
- Consequences: no duplication of the intake/portal flows; platform-level
  tables need their own abuse protection (Redis rate limits, email
  verification, report-abuse) since they sit outside tenant isolation;
  audit rows for citizen actions have tenant_id=NULL; Phase 3 cannot ship
  over the current Cloudflare Tunnel (HTTP-only) — needs open UDP ports or
  a TURN relay, decided before Phase 3 starts.

## D-014: SOS ships without video first; trial lead cap (2026-07-11)

- Context: Phase 3's video/audio room is blocked on network infrastructure
  (WebRTC media cannot cross Cloudflare Tunnel; the owner hasn't yet chosen
  port forwarding vs a TURN relay VPS). Phase 4 needs a concrete lever that
  makes the free plan convert without adding payment processing (D-008
  keeps billing manual).
- Decision: split Phase 3 — ship the **SOS duty flow now** (opt-in
  `sos_on_duty` roster, citizen SOS button, instant push+email alerts,
  first-to-claim, existing chat) and add the LiveKit video room later as a
  drop-in on top of the claim step once media transport exists. SOS needs a
  citizen account but not a verified email (emergencies), compensated by a
  hard 2/24h rate limit and audit logging. For monetization: **trial plan =
  5 marketplace leads/calendar-month** (`TRIAL_MONTHLY_LEAD_LIMIT`), solo
  and firm plans unlimited; enforcement at claim time (HTTP 402), quota
  visible in the Tregu header. The operator still switches plans manually
  in the platform panel.
- Consequences: citizens get real emergency value today and the video room
  becomes an incremental upgrade, not a blocker; the lead cap gives the
  free→paid upgrade a reason to exist without a payment provider; the
  402 signal is already handled distinctly in the frontend so a future
  self-serve upgrade flow can hook into it.

## D-015: Self-hosted LiveKit, LAN-first, tokens via plain JWT (2026-07-11)

- Context: the SOS video room (D-013 phase 3) needs a WebRTC SFU. The owner
  chose self-hosted (privacy, no per-minute vendor cost) over Twilio/Daily.
  Public-internet media transport is still undecided (router port
  forwarding vs TURN relay VPS), but LAN/localhost calls need nothing.
- Decision: run `livekit-server` in docker-compose next to db/redis/caddy;
  ship it **LAN-first** (`use_external_ip: false`, media 7881/tcp +
  7882/udp, signaling proxied by Caddy :7443 for wss). Join tokens are
  minted in `app/services/livekit.py` with **pyjwt directly** (LiveKit
  tokens are standard HS256 JWTs) — no Python SDK dependency for a single
  token shape. Grants are restricted to one `sos-<case_id>` room, 4h TTL,
  and only for claimed/converted cases where the caller is a party.
  API keys live only in the git-ignored `.env` files and must match
  between the container (`LIVEKIT_KEYS`) and the backend.
- Consequences: video works end-to-end today on localhost and LAN and the
  whole app-layer (tokens, buttons, overlay) is final; going public is a
  pure infra change (port forward + `use_external_ip: true`, or coturn) —
  no code changes expected. If we later need server-side room control
  (kick, recording), we add the `livekit-api` package then.

## D-016: Revenue model — per-seat lawyer subscription, never fee splitting (2026-07-11)

- Context: the owner asked how the platform earns ("sistemi mas tre muaj
  falas duhet te arktoj te hyrat") and how global leaders do it. Research:
  LegalMatch = flat lawyer subscription (~$455/mo) with unlimited leads and
  free citizens; Avvo = free profile + paid highlighting; Thumbtack-style
  pay-per-lead creates quality disputes; **Avvo Legal Services was shut
  down (2018) after 8 US state ethics opinions** because the platform held
  client money and took a % "marketing fee" from lawyer earnings —
  impermissible fee splitting with a non-lawyer. The Kosovo Law on
  Advocacy / OAK code protects lawyer independence the same way. The €24
  price point was already validated by the ICL offer.
- Decision: **citizens never pay the platform. Lawyers pay
  `Tenant.plan_price_eur` (default 24 €) per active user per month** after
  a 90-day free trial (the "3 free months" pilot promise); the subscription
  includes the whole practice platform + unlimited marketplace leads +
  highlighted directory profile + SOS duty. Per-tenant price override
  (0 = free forever, for the founder tenant and strategic partners).
  Client fees always flow directly citizen→lawyer (portal invoices); the
  platform never holds client money and never takes a percentage.
  Billing is in-house: `PlatformInvoice` per tenant per month, generated by
  a daily loop, paid by bank transfer (operator marks paid in /platform) or
  Stripe Checkout when a gateway usable from Kosovo is contracted.
  Dunning is deliberately soft: overdue past due+grace (14+14 days) only
  pauses NEW marketplace claims (402) — never access to the lawyer's own
  matters/data ("your data, always yours" commitment); persistent
  non-payment is a manual suspend decision.
- Consequences: D-008 (fully manual billing) is superseded; the platform
  panel stays as the manual fallback and payment-recording surface.
  Self-serve card payment of subscriptions activates automatically once
  STRIPE keys are configured; until then the invoice email carries
  `platform_bank_details` (backend/.env — must be set before the first
  real invoice). Trial length moved 30→90 days to match the market promise.
## D-017: Trust layer — manual OAK verification gate + service-only reviews (2026-07-12)

- Context: before promoting publicly, citizens must be able to trust that
  every listed "lawyer" is a real licensed advocate, and lawyers need social
  proof. OAK (Kosovo Bar Association) publishes its member registry on the
  web but offers no lookup API.
- Decision: verification is **manual by design**: the lawyer enters their
  OAK license number (profile → status `pending`), the platform operator
  checks the public registry and approves/rejects in `/platform` (decision
  emailed in the lawyer's locale). The status is never client-writable and
  editing the license resubmits. Being verified is a hard gate for: public
  directory listing, case-match + SOS-duty notifications, public stats and
  claiming marketplace cases (403). Reviews (`CaseReview`, 1:1 with a
  concluded claimed case) rate only the service — communication, speed,
  clarity (1–5) — **never the legal outcome**, mirroring how Avvo/lawyer
  directories avoid regulatory trouble; the average and count rank the
  directory within each plan tier. Transparent pricing (`consult_fee_eur`)
  is optional and shown in the directory.
- Consequences: a fake or unlicensed signup can browse the app but never
  touches a citizen; the operator has a small recurring duty (verification
  queue is surfaced at the top of /platform and by email). When OAK offers
  an API or a data-sharing agreement, only the manual step is replaced.
## D-018: "AI protection by phone" — local voice pipeline + evidence standard + client-side call recording (2026-07-12)

- Context: the owner's core scenario — a citizen stopped by police opens the
  app and from that second everything should work by voice (Albanian) and be
  preserved as evidence in the citizen's favor. Research (plan
  `mbrojtja_ai_+_backlog_i_plotë`): Albanian STT exists as a fine-tuned
  Whisper large-v3-turbo (WER 6.98%) with a CTranslate2 int8 build that runs
  on our CPU-only host; Piper gained an official `sq_AL` voice (April 2026);
  the ACLU "Mobile Justice" apps validated the evidence pattern (upload
  chunks *while* recording so the proof survives phone seizure).
- Decision, three parts:
  1. **Voice stays local** (`app/services/voice.py`): faster-whisper with the
     Albanian CT2 model (fallback to base turbo for sr/tr/bs/en/zh) + Piper
     `sq_AL` executed as a **subprocess** (GPL-3 isolated from our process;
     no Docker container needed); browser `speechSynthesis` is the TTS
     fallback for non-Albanian locales. Push-to-talk (2–4 s round trip), not
     realtime duplex — duplex needs a GPU and moves to LiveKit Agents later.
  2. **Evidence standard** (`EvidenceSession`/`EvidenceChunk`): MediaRecorder
     chunks every ~5 s → serialized ordered upload → SHA-256 per chunk +
     `prev_hash` chain + server timestamps + IP + audit log; encrypted at
     rest with the existing document Fernet key; downloadable "evidence
     package" PDF (chain of custody + transcript). Strict seq ordering
     (409 on gaps) keeps the chain meaningful.
  3. **Call recording without Egress**: recording a LiveKit call server-side
     (Egress) needs a Chrome-compositing container — fragile on this host.
     Instead the **citizen records client-side**: Web Audio mixes local +
     remote audio into one MediaRecorder feeding the same evidence pipeline
     (kind `call`); the lawyer must acknowledge a recording-consent notice
     before joining. Egress can still be added later purely as infra.
- Consequences: recording works even with zero LiveKit involvement (plain
  SOS), evidence has one uniform format, and no audio ever leaves the
  machine for transcription (D-002 privacy stance extends to voice). The
  privacy policy gained an "SOS recordings and voice" section ×6; consent is
  collected once in the SOS screen and per-session server-side
  (`consent_at`). UI guidance stays "information, not advice".

## D-019: Platform feedback is anonymous-friendly and operator-reviewed (2026-07-12)

- Context: the redesign plan required "vende për shkresa e ankesa". Two
  distinct needs: official letters/complaints citizens send to third parties
  (solved by the template generator, now 7 templates with categories) and
  complaints/suggestions aimed at the platform itself, which had no channel.
- Decision: a single `platform_feedback` table (kind ankesë/sugjerim/problem,
  optional name+email, status new/handled) fed by a rate-limited public
  endpoint (`POST /api/public/feedback`, 5/h/IP, no account required — a
  complaints channel must not demand signup). Superadmins get an email per
  entry and review it in /platform; "handled" is a status + optional note,
  never deletion, so the trail stays auditable.
- Consequences: /kontakti is linked from the shared public footer on every
  public page; the generator and the contact channel stay clearly separated
  in the UI (documents = drejtuar të tretëve, kontakti = drejt platformës).

## D-020: Two public surfaces + first-class citizen identity (2026-07-12)

- Context: the landing mixed both audiences and citizens had no visible
  account: their login was buried in /rasti-im and every "Kyçu" button led
  to the lawyer login (`/login` → /dashboard), which confused non-lawyers.
- Decision: follow the two-sided-marketplace pattern (Avvo-style): `/` is an
  umbrella presentation of the whole project that segments immediately with
  two audience cards; each audience gets its own story page
  (`/per-qytetaret`, `/per-avokatet`) and its own login (`/kycu` vs
  `/login`, each cross-linking the other). Citizens get a real account
  surface: `/llogaria` (profile, language, password, sign-out) backed by
  PATCH /citizen/me + change/forgot/reset-password endpoints, and the
  public header recognizes the citizen token with an initials-chip menu.
  Tabs were rejected: they hide half the content and half the visitors
  never find themselves.
- Consequences: citizen credentials can never land on the lawyer login;
  password reset uses a scoped `citizen_reset` purpose token (1h) and
  doubles as email verification; the shared `citizen-auth.tsx` form keeps
  signup/login/forgot identical across /kycu, /posto-rastin and /rasti-im.

## D-021: Consultation payments run through the platform's Stripe (2026-07-13)

- Context: point 10 of the improvement plan — citizens should be able to
  pay a lawyer's published consultation fee online at booking time.
  Per-lawyer Stripe accounts (Connect) would require every office to
  onboard with Stripe before the feature works at all.
- Decision: the checkout session is created on the platform's existing
  Stripe account (same key/webhook as invoices and subscriptions), with
  `metadata[booking_id]`. Booking status: `pending_payment` →(webhook)→
  `pending` → confirm/decline by the lawyer. `pending_payment` holds the
  slot; if Stripe errors at booking time, we fail open to the free flow so
  a gateway hiccup never loses a client. The collected fee (stored in
  `consult_bookings.fee_eur`) is passed on to the lawyer by the operator —
  a transfer of the exact amount, NOT a percentage cut, so D-016
  ("never fee splitting") stands. Stripe Connect per-office is the
  designated follow-up once volume justifies it.
- Consequences: without `STRIPE_SECRET_KEY` nothing changes (bookings go
  straight to `pending`); the operator needs a simple monthly payout
  routine to lawyers with online-paid consults (audit log records
  `booking.paid_online` per booking).

## D-022: Agentic AI features reuse the single LLM abstraction (2026-07-13)

- Context: points 11–13 (deep research, clause assist, document
  summaries) could each have pulled in agent frameworks or new providers.
- Decision: all three are plain functions in `services/assistant.py` over
  the existing `get_provider()` abstraction and the existing RAG search —
  deep research is an async generator (decompose → search per sub-question
  → synthesize) streamed as SSE `step`/`delta` events; ai-assist and
  summaries are single JSON-returning calls. Summaries are cached in
  `documents.ai_summary` (JSON text) so a document is summarized once per
  version. All three respect the tenant's `allow_external_ai` switch via
  `_effective_provider`.
- Consequences: no new dependencies; local-only tenants get the same
  features on the local provider; deep research cost is bounded (≤5
  sub-questions, ≤4 corpus hits each, deduped citations).

## D-023: Notary integration is information-only, backed by data files (2026-07-13)

- Context: extending the platform to Kosovo's second legal profession
  (144 notaries). Law 06/L-010 requires the party's physical presence
  before the notary and bans combining the lawyer/notary roles, so online
  notarization or notary marketplace accounts are legally impossible today.
- Decision: the notary bridge is purely preparatory — the corpus knows the
  notary law, Ava routes notary matters, `/noteret` gives directory + act
  type + document checklist + fee estimate, and `/dokumentet` produces
  party-drafted documents for solemnization (art. 41 lets the party draft;
  the notary solemnizes). All notary knowledge lives as data:
  `app/seeds/notary.py` (acts, checklists, AI 02/2012 fee brackets) and
  `data/notaries.json` (scraped ONK registry, git-ignored like the OAK
  CSV). No new DB tables, no notary accounts.
- Consequences: zero legal risk (information, not legal service); refresh
  is one script re-run; if remote notarization becomes law (see
  `docs/integrimet/e-noteria.md`) the LiveKit + evidence-vault stack is the
  upgrade path; notary-office accounts (law art. 50 registers) start only
  on explicit ONK interest.

## D-024: Profession is a tenant field, not a fork — notaries pay like lawyers (2026-07-13)

- Context: the owner wants notaries as the second paying profession ("Jam
  noter" next to "Jam avokat"): the same AI office and direct demand, paid
  like lawyers. Worldwide, civil-law notary software (TriNotar/DE,
  Septeo/FR, NoRA/AT) is subscription office software; nobody runs a case
  marketplace for notaries because they are impartial public officers with
  fixed tariffs (AI 02/2012) and territorial competence — competing for
  cases conflicts with the office.
- Decision: one codebase, one `Tenant.profession` column ("lawyer" |
  "notary", default "lawyer"). Notary tenants get the identical stack
  (matters, documents, Ava, calendar, billing, per-seat subscription with
  the same 90-day trial — `platform_billing` needed zero changes) with the
  marketplace surgically removed: no marketplace nav, 403 on case claims,
  excluded from /public/lawyers and public stats. Their "market" is the
  adapted demand channel: equal listing in /noteret (never promoted),
  online appointment slots (reusing `ConsultBooking`), and the prepared
  dossier (citizen attaches the /dokumentet draft to the booking).
  Verification reuses the OAK queue; `LawyerProfile.oak_license_no` holds
  the ONK number for notaries, and the platform panel auto-matches
  signups against the scraped `data/notaries.json` (email → name).
  This narrows D-023: notary *accounts* now exist, but notarization
  remains strictly offline/in-person.
- Consequences: adding a third profession later (përmbarues, ndërmjetësues)
  is a column value + conditional UI, not a fork. The `LawyerProfile` model
  name is now slightly misleading (it backs any professional's public
  profile) — renaming was skipped deliberately to avoid a risky migration;
  revisit only if a third profession lands. Art. 50 notary registers stay
  out of scope until ONK shows interest.

## D-025: AGENTS.md is the single agent entry point; vendor files are pointers (2026-07-16)

- Context: the owner must be able to swap the coding agent (Cursor, Claude
  Code, Codex, Gemini CLI, ...) and the underlying LLM at any time. Vendor
  tools look for different instruction files (CLAUDE.md, GEMINI.md,
  .github/copilot-instructions.md, .cursor/rules) and offer proprietary
  "memory" features that would trap project knowledge in one tool.
- Decision: `AGENTS.md` (the emerging cross-vendor standard) is the only
  full instruction file; every vendor-specific file is a one-line pointer to
  it. All durable knowledge is committed to the repo under `docs/agents/`
  (STATE / JOURNAL / DECISIONS / ROADMAP) — never stored in a vendor's chat
  memory. AGENTS.md carries a "reading order" for small-context models so
  weaker/cheaper LLMs can also operate the repo. Product-side LLM
  independence stays as per D-003 (`backend/app/llm/` abstraction + config).
- Consequences: switching agent vendors costs one pointer file at most; a
  new agent is productive after reading AGENTS.md + STATE headline + last
  journal entries. The discipline cost: agents MUST write session results
  into the docs (session protocol §2) or the knowledge is lost to the next
  tool.

## D-026: License auto-verification only on confirmed-email registry match (2026-07-18)

- Context: OAK/ONK have no lookup APIs, so verification was manual (D-017).
  Both chambers publish member registries WITH email addresses, and we keep
  local copies (data/oak_registry.csv, data/notaries.json). The operator
  wants the procedure automated.
- Decision: `services/license_verify.py` auto-approves a pending license
  only when BOTH hold: (1) the account has confirmed its email
  (email_verified_at) and (2) that exact email appears in the chamber's
  public registry. Owning the mailbox the chamber itself publishes for a
  member is the strongest identity proof available without an official API.
  A name-only match is never auto-approved (namesakes exist) — it is shown
  as a hint badge in the manual queue. Every auto-approval is audit-logged
  (`platform.verification_auto`) and the operator gets an FYI email.
- Consequences: most legitimate signups verify themselves within minutes of
  confirming email; the manual queue shrinks to edge cases (different email
  than the registry, stale registry, no license). The registry files must be
  refreshed periodically or auto-verify silently degrades to manual.

## D-027: OpenClaw (Halim) as the operations assistant — push over loopback, read-only by default (2026-07-18)

- Context: the platform is live and the owner cannot watch the inbox and the
  operator queue all day. An OpenClaw gateway ("Halim") already runs on this
  machine with a Telegram channel to the owner.
- Decision: three integration lanes, all local-only:
  (1) backend pushes operator events (signup, license verification, SOS, new
  case, feedback, booking) to the gateway's `/hooks/agent` endpoint over
  loopback with a dedicated bearer token (`OPENCLAW_HOOK_TOKEN` in
  backend/.env; `services/ops_notify.py`, fire-and-forget, disabled when the
  token is empty, suppressed for test recipients);
  (2) an OpenClaw cron job every 10 min runs `scripts/ops_inbox_triage.py` —
  read-only IMAP PEEK triage of the owner's Gmail (state in
  data/ops/inbox_state.json), human mail → Telegram summary + draft reply;
  (3) a daily 08:30 cron runs `scripts/ops_digest.py` (read-only DB +
  Umami traffic) → morning report on Telegram.
- Guardrails (written into the assistant's AVOKATIM-OPS.md): the assistant
  never sends email without explicit owner approval (then via
  `scripts/ops_send_reply.py`), never writes to Gmail/DB/data/, never
  restarts services. Events → assistant is one-way; actions stay human-gated.
- Consequences: the owner gets everything on Telegram in real time and a
  daily digest; the assistant drafts but humans decide. If OpenClaw is down,
  nothing breaks — ops_notify fails silently and the operator emails still
  arrive; the digest/triage simply pause.

## D-028: Halim is the correspondence operator; the system thanks every registration itself (2026-07-19)

- Context: the owner wants zero routine email work. The first founder letter
  was written by hand; that does not scale, and Halim's old protocol asked
  open-ended questions ("dërgo / ndrysho / lëre").
- Decision: three communication lanes, documented in `docs/agents/COMMS.md`
  (the single source of truth for outbound mail):
  (A) the SYSTEM automatically thanks every successful registration — the
  license-verification email is now a warm thank-you letter signed by the
  owner (with a 'Founder' paragraph for the first 20 offices, both the
  auto-verify and the manual approval path), and citizens get a
  `citizen_welcome` letter the moment they confirm their email (plus a
  `notify_ops` heads-up so Halim knows no action is needed);
  (B) HALIM handles all inbound human correspondence with a single-question
  protocol: final ready-to-send draft on Telegram + "PO (dërgo) / JO (lëre)";
  any other reply is treated as an edit instruction. He never duplicates
  lane A;
  (C) only sensitive/press/legal matters remain owner-written.
- Consequences: the owner's only routine involvement in email is answering
  PO/JO on Telegram. Agents adding outbound email must update COMMS.md in the
  same commit (AGENTS.md §4b + session protocol enforce this). Milestone
  moments are celebrated automatically instead of depending on the owner's
  availability.
