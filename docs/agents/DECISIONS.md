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

## D-029: Free trial extended 90 → 365 days (2026-07-28)

- Context: adoption, not revenue, is the bottleneck — 13 offices registered,
  3 verified, first marketplace cycle just completed. The owner decided the
  early market needs a full year to adopt the system before seeing an invoice
  ("le te adaptohen me sistemin tone").
- Decision: `platform_billing.TRIAL_DAYS = 365`. All existing trial tenants
  (12) had `trial_ends_at` recomputed as `created_at + 365 days` in the DB.
  All promises in copy were updated: dictionaries ×6 languages (npSubtitle,
  startTrial, landLawB, lpPlanTrial), i18n trial_ending_body ×6, signup email
  ({trial_days} placeholder picks it up automatically), OAK/ONK outreach
  letters ("Viti i parë është plotësisht falas").
- Consequences: first platform revenue moves to ~mid-2027. The billing
  machinery (invoices, dunning, trial-ending nudges at T-7d) is unchanged and
  already tested — only the constant moved. Historical one-shot scripts in
  `backend/scripts/send_*.py` still say "tre muajt" — they are archives, do
  not reuse their copy verbatim.

## D-030: Industry-gap wave — GEO, trust signals, follow-up, office memory, agentic prepare, client timeline (2026-07-28)

- Context: owner asked what AvokatIM lacks vs the 2026 industry (Clio Duo/
  Work, Harvey Agents, Avvo/Martindale trust patterns, GEO — generative
  engine optimization) and approved the full plan ("implemetoj te lutem siq
  ti sygjeron"). Priority order: acquisition first (GEO + trust), retention
  second (follow-up), AI depth third (memory + agentic), transparency last.
- Decision, six shipped items:
  1. GEO: schema.org JSON-LD server-rendered on public pages (Organization/
     WebSite on landing, ItemList of Attorney on /avokatet, Notary on
     /noteret), per-page metadata via server layouts, robots.ts + sitemap.ts.
     Notary emails are omitted from JSON-LD on purpose (spam protection).
  2. Trust signals: `LawyerProfile.career_start_year` (self-reported, shown
     as "N vjet përvojë") + `cases_completed` (computed from marketplace
     activity — evidence, not claims). Both public in the directory API.
  3. Activation follow-up: single 48h email to verified citizens with no
     posted case (`case_followup_sent_at`, 14-day window). One-shot by
     design — we never nag twice.
  4. Office memory: `Tenant.assistant_style`, free text appended to Ava's
     office system prompt (capped 2000 chars). Deliberately tenant-level and
     transparent (a Settings textarea) instead of hidden learned memory.
  5. Agentic preparation: `prepare_matter_stream` is an orchestrated
     server-side pipeline (read file → derive questions → search corpus →
     synthesize + draft), NOT a free-form tool loop — DeepSeek function
     calling is less reliable and a fixed pipeline is auditable. The draft is
     separated by the literal marker `=== DRAFT-SHKRESA ===`.
  6. Client timeline: reused `updated_at` as the converted/closed timestamp
     instead of adding event tables — good enough for a 3-step stepper.
- Consequences: public pages are now crawlable/citable by AI assistants
  (expect directory citations to build over weeks, not days). New outbound
  email documented in COMMS.md. The agentic pattern (derive → search →
  synthesize with a machine-readable marker) is the template for future
  agent features; extend it rather than inventing new shapes.

## D-031: UI audit wave — profile pages, honest stats, settings map, charts (2026-07-28)

- Context: owner asked for a full interface audit vs the industry and
  approved all 10 suggestions ("pregadite planin e plote per te gjitha edhe
  implemetoj"). Guiding principle: the interface must reach the level of the
  backend — every capability visible, every public page citable.
- Decision, ten shipped items (P1 acquisition, P2 lawyer office, P3 polish):
  1. The lawyer profile is a page, not a card: `/avokatet/[id]` server-routed
     with its own metadata + Attorney JSON-LD; the directory feeds it. New
     public endpoint `GET /public/lawyers/{profile_id}` with the exact same
     trust gate as the list (visible+verified+active+lawyer) plus anonymized
     review comments. Booking extracted into a shared `BookingWidget`.
  2. Landing stats show only numbers that build trust today (554 laws, 141
     ONK notaries, 6 languages, 24/7); the lawyer count self-restores at
     >= 20 in the directory — no manual step, no vanity numbers.
  3. Bio hygiene is enforced in code, not by policy: `_scrub_bio` drops any
     bio line with an email/phone/birth-date at write time (`PUT /profile`).
     One-time DB cleanup rewrote Ilire Aydogan's pasted-CV bio as prose.
  4. Settings got an information architecture: 5 fixed anchored groups
     (`#grp-zyra|publik|ai|njoftimet|siguria`) — deep-link `#grp-ai` for Ava
     preferences. New sections must join a group, not float loose.
  5. Charts stay dependency-free: inline SVG bars (6-month trend dual-series,
     A/R aging) — no chart library.
  6. Feature discovery via a versioned dismissible "E re" card on the
     dashboard (`avokatim:whatsnew:YYYY-MM`); bump the key when contents
     change, never re-nag otherwise.
  7. FAQPage JSON-LD is generated from the same `dictionaries.sq` entries the
     page renders — structured data can never drift from visible answers.
- Consequences: every verified lawyer now has a citable URL (GEO); sitemap
  is dynamic (profiles, revalidate 1h). Screenshot verification of
  JS-rendered pages now uses Playwright chromium (cached in
  `~/.cache/ms-playwright`); headless Firefox fires before client fetches.

## D-032: Last industry gaps — payments abstraction, passive time, office Ava, review requests, flat fees (2026-07-28)

- Context: after the UI wave the owner asked for one more comparison with the
  2026 industry and whether card payments for lawyer→client services are
  complete. Stripe cannot onboard Kosovo businesses, so "complete" needed a
  local answer.
- Decisions:
  1. **Payments are a provider abstraction, not a Stripe integration.**
     `services/payments.py` dispatches on `payments_provider`
     (`stripe`|`raiffeisen`); a provider is "enabled" only when its
     credentials exist. Until a gateway contract exists, the working rails
     are bank transfer + a **manual pay-by-link** the lawyer pastes onto the
     invoice (`PUT /invoices/{id}/payment-link`, https-only) — same
     `payment_link` slot an automated provider would fill, so email/portal
     need no changes. The Raiffeisen adapter is a documented skeleton; only
     `_raiffeisen_payment_link()` needs touching when the bank's API docs
     arrive (owner steps: `docs/integrimet/raiffeisen-pagesat.md`).
  2. **Passive time capture is suggestions, never entries.** A separate
     `time_suggestions` table (no existing billing query touched); derived
     from the append-only audit log with conservative per-action minutes and
     a 120-min/day cap; idempotent per (matter, user, day); only an explicit
     accept creates a `TimeEntry`. Nightly generation rides the existing
     reminder loop (one run per calendar day).
  3. **Office Ava follows D-030: fixed pipeline, no tool loop.** The LLM only
     (a) picks one of 8 hand-written tenant-scoped queries and (b) phrases
     the result; it never writes SQL and never sees cross-tenant data. Every
     call is audited with the tool id.
  4. **Review requests are one-shot and evidence-anchored**:
     `review_request_sent_at` on the case, sent 48h after conclusion, only
     when no review exists — same sent-at pattern as every other reminder
     (COMMS.md rule 4).
  5. **Flat-fee menus are data on the profile** (`flat_services` JSONB,
     max 10, validated server-side), shown on the public profile and as a
     directory chip — transparent pricing without a new table or workflow.
- Consequence / operational note: `systemctl --user restart avokatim` does
  not restart the separate `avokatim-frontend` unit; after any frontend
  build, restart `avokatim-frontend` explicitly or the old process serves a
  stale chunk manifest (CSS 500, unstyled pages).

## D-033: Security hardening wave — Postgres RLS + OpsHub-inspired fixes (2026-07-31)

- Context: a comparative security audit of OpsHub (the owner's CRM project)
  and AvokatIM showed OpsHub enforces tenant isolation *inside* Postgres
  (RLS FORCE + non-superuser app role) while AvokatIM relied only on
  `tenant_id` filters in code. Both projects shared gaps: no CSP, unsigned
  WhatsApp webhook, no dependency scanning, no SECURITY.md.
- Decision:
  1. **RLS with a default-open policy, not default-deny.** Unlike a pure
     per-org SaaS, AvokatIM has legitimate cross-tenant reads (public lawyer
     directory, landing stats, background reminder loops, /platform admin).
     The `tenant_isolation` policy on all 25 tables with `tenant_id`
     therefore admits sessions with **no** tenant GUC, and locks a session
     to one tenant as soon as `deps.get_current_user` pins it (superadmins
     stay unpinned). This protects exactly the risky surface — authenticated
     lawyer endpoints with a forgotten WHERE clause — with zero regression
     risk for public/background paths. Rows with `tenant_id IS NULL` are
     platform-shared (global document templates, platform audit events) and
     stay visible; the full simulation caught this (empty template list)
     before the policy was amended.
  2. **GUC via `set_config(..., local=true)` + a Session `after_begin`
     listener**, never session-level: SQLAlchemy returns pooled connections
     to the pool at every commit, so a connection-level setting would leak
     tenant context across requests. The transaction-local setting dies with
     each transaction and the listener re-arms it for every new one.
     Corollary learned the hard way: after the local setting reverts, the
     GUC reads `''` (not NULL) and Postgres does **not** short-circuit `OR`
     — every cast in the policy goes through `nullif(..., '')`.
  3. **Two DB roles**: the app connects as non-superuser `avokatim_app`
     (NOBYPASSRLS, DML-only) via new setting `database_app_url`; Alembic and
     admin scripts keep the owner role via `database_url`. FORCE RLS keeps
     even owner sessions subject to the policies.
  4. **JWT revocation via `users.token_version`** (claim `ver`, compared in
     deps on every request — the user row is loaded anyway). Password
     reset/change bumps it; change-password returns a fresh token so the
     current device stays logged in. Chosen over a Redis denylist because it
     needs no new infrastructure and covers the real scenario (compromised
     password).
  5. **CSP with 'unsafe-inline' scripts for now** (Next.js hydration without
     nonce infrastructure); the enforced win is origin-locking script/connect
     targets so injected code cannot exfiltrate localStorage tokens to an
     attacker domain. Headers set in `proxy.ts` for public hosts only.
  6. **TOTP secrets Fernet-encrypted at rest** (same key material as document
     storage, different salt, `enc:v1:` prefix, plaintext passthrough for
     legacy rows), WhatsApp webhook now requires `X-Hub-Signature-256` when
     `whatsapp_app_secret` is set, document uploads validate a MIME +
     extension allowlist, `SECURITY.md` + /siguria vulnerability-report
     section published, and `scripts/security_scan.sh` (pip-audit + npm
     audit) runs weekly via `avokatim-secscan.timer` reporting to Halim.
- First scan acted on immediately: Next.js 16.2.10 → 16.2.12 (fixes the
  middleware/proxy-bypass advisory that would have neutered the new CSP
  headers), sharp overridden to >=0.35.0, pip upgraded. Left open: torch
  2.12.1 → 2.13.0 (PYSEC-2025-194) — big dependency, needs its own session;
  `setuptools` stays <82 until then (torch pin).

## D-034: Germany expansion — one codebase, jurisdiction profiles as data (2026-08-01)

- Context: the owner wants everything achieved for Kosovo replicated for
  Germany. Options were a separate fork or a multi-country single codebase.
- Decision: **single codebase, single brand, per-country "jurisdiction
  profile"** (`backend/app/jurisdictions.py`) — the architecture already kept
  jurisdiction *rules* as data (hard rule #4); this adds the code-side
  complement (currency, VAT 18/19, timezone, locales, chamber registry,
  feature switches, cities, public host). A fork would double every future
  improvement. Key sub-decisions:
  1. **Host = country.** `de.avokatiim.ai` (Cloudflare tunnel ingress + DNS)
     resolves to DE in proxy.ts (`x-avokatim-country`) and in
     `country_from_request` for public endpoints; authenticated paths trust
     only `Tenant.country`. `country` columns on tenants / citizen_users /
     case_requests (default XK) scope directory, marketplace, stats, SOS
     alerts and Ava — German lawyers and Kosovar lawyers never mix.
  2. **German corpus from gesetze-im-internet.de** (official BMJ portal,
     public domain, structured XML — one `<norm>` per §):
     `scripts/import_de_laws.py`, 58 core federal acts (GG, BGB, ZPO, StGB,
     StPO, HGB, KSchG, VwGO, SGB, RVG, BRAO…, 14 443 chunks), resumable like
     the GZK importer. RAG fallback language is now per-jurisdiction
     (`corpus_fallback_language`: sq for XK, de for DE) resolved inside
     `search_corpus`.
  3. **DE Ava is a different prompt, not a translation**: strictly
     Rechtsinformation (RDG § 2 boundary), AI-system disclosure (EU AI Act
     Art. 50, in force 2026-08-02), never invent norms; LLM provider is
     per-jurisdiction via `JurisdictionProfile.llm_provider` (EU provider
     before public launch; default until a key exists).
  4. **BRAV has no emails → no auto-verification for DE lawyers.** The OAK
     email-match rule cannot port; German signups notify the operator/Halim
     with a prefilled BRAV search link for one-click manual approval
     (bravsearch.bea-brak.de returned 503 during the session — scraping
     deferred, link-assisted manual flow is v1).
  5. **SOS and the notary pillar are OFF for DE** (feature switches +
     backend guards + hidden UI) until each gets its own legal review.
  6. **Month-based German deadlines approximated as 30 days** in seed data
     with an explicit warning note in every affected rule (§ 222 ZPO month
     arithmetic differs around month ends) — honest approximation over
     false precision until the deadline engine learns calendar months.
  7. **Public launch gate documented, not blocking** development:
     EU server + GDPR Art. 27 representative + EU LLM + German-lawyer review
     of AGB/Datenschutz/Impressum (docs/legal/DE-LAUNCH-GATE.md).
- Consequences: adding country #3 is now data + one profile entry; the de
  locale is the 7th UI/email language; German legal texts (AGB, Datenschutz,
  Impressum at /impressum) are drafts pending professional review.

## D-035: Landesrecht as a `region` dimension, not new tables (2026-08-01)

- Context: German court deadlines legally depend on the Bundesland's
  holidays (§ 222 ZPO → §§ 187 ff. BGB), and the topics citizens ask most
  (police, building, school, neighbours, Kita, shop hours, municipal, press)
  are Landesrecht — absent from the federal corpus (D-034 limitation).
- Decision: one nullable `region` column (Bundesland code NW/BY/…, ISO
  3166-2 without prefix) on `Holiday`, `LegalCorpusDoc` and `Tenant`;
  `region IS NULL` = nation-wide/federal, so the existing 79-act federal
  corpus and federal holidays are untouched. The 16-Länder registry and a
  city→Land prefill map are data in the DE `JurisdictionProfile`.
  1. **Deadline engine**: `_holiday_set(…, region)` returns federal + that
     Land's holidays; the office's Land comes from `tenant.region`
     (settings picker, prefilled from the first profile city). No region →
     federal only (previous behaviour, conservative). Only whole-Land
     holidays are seeded — municipal/partial ones (Mariä Himmelfahrt in BY,
     Augsburger Friedensfest) are excluded because a false holiday would
     compute a LATER due date than the real one.
  2. **Corpus**: `search_corpus(…, region)` = `region IS NULL OR region =
     :r` — federal always, the asker's Land on top, other Länder never.
     Lawyer assistant passes no region yet (federal-only, unchanged).
  3. **Import per portal adapter** (`scripts/import_de_landesrecht.py`):
     every Land publishes differently, so one small adapter per portal and
     a curated ~10-act list per Land. Pilot: NRW (recht.nrw.de, server-
     rendered Drupal) + Bayern (gesetze-bayern.de) = ~30M residents,
     20 acts / ~2,900 chunks. Statutory texts are § 5 UrhG public domain.
  4. **Remaining 14 Länder blocked on juris SPAs**: landesrecht-bw.de,
     gesetze.berlin.de etc. are JavaScript apps over a token-authenticated
     "mylex" API — scraping needs a headless browser or a data agreement;
     deferred (LESSONS #1). Ava's DE prompt says openly which Länder are
     covered and answers federal-only for the rest.
- Consequences: deadline math is now Land-correct for offices that pick
  their Bundesland; public Ava has a "Bundesland (optional)" selector
  (localStorage); every future Land is data + one adapter, no schema work.

## D-036: Exact calendar-month deadline math (`day_type="months"`) (2026-08-01)

- Context: German statutory month deadlines (ZPO § 517/§ 520, VwGO § 70/§ 74,
  SGG § 84, AO § 355) were approximated as 30/60 calendar days with a warning
  note. The 2026 industry comparison flagged this as the highest-risk gap:
  missed deadlines are the #1 malpractice source, and every German
  Kanzleisoftware does exact month math. Kosovo's LPK art. 124 uses the same
  rule, so the fix is generic, not DE-specific.
- Decision: extend `DeadlineRule.day_type` with a third value `"months"`
  (`days` then holds the month count) instead of adding a new column — one
  field describes the counting mode: calendar days | business days |
  calendar months. `add_months()` in `services/deadlines.py` implements
  §§ 187–188 BGB: the period ends on the day of the target month with the
  same number as the trigger day; when that month is shorter, on its last
  day (Jan 31 + 1M → Feb 28/29). The existing `extend_to_business_day` loop
  covers § 222 (2) ZPO (weekend/holiday → next business day, Land holidays
  included via D-035).
- Seeder change: `_seed_country` now syncs `days`, `day_type`, `legal_basis`,
  `notes`, `trigger_event` from seeds for existing rules (rules are platform
  data, never tenant-edited) — existing DBs convert on next startup without
  a migration; only `name` keeps the merge-don't-overwrite behaviour.
- Consequences: DE month rules are exact (6 rules converted, warning note
  replaced with the § 188 explanation); the public calculator and matter
  deadline picker show "X Monate/muaj" (new dcMonths* keys in 7 locales);
  any future jurisdiction can use month periods as data.

## D-037: German market parity in 6 phases; DE runs on a local LLM (2026-08-01)

- Context: the 2026-08-01 industry comparison against RA-MICRO, AnNoText and
  Actaport showed AvokatIM ahead on AI/marketplace/languages but behind on
  five German market standards: full RVG fee math, E-Rechnung, legal-expense
  insurance in the intake flow, DATEV export, and beA. Order chosen by the
  owner: functional parity → test → German launch with a **local LLM**.
- Decisions (one per phase):
  1. **RVG as data, not code**: the § 13 RVG band table (KostBRÄG 2025) and
     rate-based VV items live in `seeds/germany.py`; `services/rvg.py` only
     implements the generic math (band walk, kaufmännisch rounding, § 13
     Abs. 2 minimum, Anrechnung Vorbem. 3 Abs. 4 VV capped at 0.75, VV 7002
     pauschale, VAT). Exposed to lawyers (`/api/fee-calc/rvg` + billing
     widget that inserts invoice lines) and to the public as an SEO tool
     (`/rvg` on the DE host, rate-limited).
  2. **E-Rechnung via drafthorse, hybrid by default**: every DE-office
     invoice PDF is a ZUGFeRD/Factur-X hybrid (WeasyPrint renders PDF/A-3b
     via `pdf_variant`, drafthorse attaches EN 16931 CII XML); raw XML at
     `GET /invoices/{id}/e-invoice.xml` for B2G. New `Tenant.iban`;
     validated once with Mustangproject (valid EN 16931 + PDF/A-3b).
  3. **Rechtsschutz as intake signal**: `CaseRequest.has_legal_insurance` +
     `insurer_name`; asked on /posto-rastin (DE host), extracted by Ava's
     structure-case step, shown as a badge to lawyers (Advocado-style
     conversion signal); Deckungsanfrage lawyer template in DE_TEMPLATES.
  4. **DATEV EXTF, no dependency**: `services/datev.py` writes the publicly
     documented EXTF Buchungsstapel v13 CSV (cp1252, CRLF, decimal comma,
     SKR03 defaults 8400/10000) from issued invoices + payments; per-office
     account config on Tenant; `GET /api/export/datev` (DE only).
  5. **Local LLM for DE**: `PROFILES["DE"].llm_provider = "local"` → Ollama
     `gemma3:27b` (RTX 5090, 17.5 GB VRAM, ~50 tok/s). Chosen over qwen3:14b
     after a RAG-grounded German shootout: qwen3 spent its token budget on
     "thinking" and returned empty answers through the OpenAI-compat
     endpoint; gemma3 is fluent, grounds on provided norms, no thinking
     mode. No German citizen data leaves the machine — closes launch-gate
     item 3.
  6. **beA is an external-dependency project**: BRAK registration as a
     Kanzleisoftware-Hersteller starts now (guide + ready-to-send German
     email in `docs/legal/BEA-KSW-REGISTRATION.md`); the KSW client module
     (`services/bea/`, planned as a Java sidecar wrapping the official
     KSW-Toolkit since the crypto lives in that Java library) starts only
     after BRAK grants test access.
- Verified: `scripts/de_simulation.py` (15-check E2E on the DE host),
  full_simulation XK 187 PASS, pytest 150 green.
- Consequences: feature parity with the German incumbents except beA;
  DE positioning until beA lands: "AI + marketplace layer over the
  existing Kanzleisoftware".

## D-038: Two STT models + per-language Piper voices for multilingual voice (2026-08-01)

- Context: the voice audit showed the Albanian Whisper fine-tune is
  unusable for German ("Kündigung" → "kindikung"; a § 195 BGB sentence came
  out as gibberish), and server TTS existed only for Albanian — German
  users got whatever their browser's speechSynthesis ships. Not
  competitive for the DE launch, where voice Ava is a differentiator
  (incumbents only sell dictation software, no public voice assistant).
- Decision:
  1. **STT routes by language**: `sq` → the Albanian fine-tune
     (`whisper-sq-ct2`); every other language (and auto-detect) → the stock
     multilingual `large-v3-turbo` (the previously dead
     `voice_stt_fallback_model` setting now does what its docstring always
     claimed; cache in `data/models/whisper-cache`). Both are lazy
     singletons (`lru_cache(maxsize=2)`), CUDA float16 with CPU int8
     fallback (`voice_stt_device="auto"`) — ~1.6 GB VRAM each, warm
     transcription ~0.3 s on the RTX 5090.
  2. **Server TTS per language**: Piper voices as data files in
     `data/models/piper-voices/{lang}.onnx` — de (thorsten), en (lessac),
     tr (dfki), sr (serbski_institut), zh (huayan) downloaded from
     rhasspy/piper-voices; sq keeps its dedicated model. `/voice/status`
     returns `tts_langs`; the client uses server TTS when the locale is
     listed, browser speechSynthesis otherwise (bs has no Piper voice).
     A new language = drop in an .onnx file, no code.
- Verified: German TTS→STT roundtrip test in the suite (152 green ×3);
  live: § 195 BGB sentence transcribed correctly in 0.27 s warm, German
  Piper WAV in 1.3 s. Everything still local — no audio leaves the machine.
- Consequences: voice Ava is fully functional in sq/de/en/tr/sr/zh with
  local neural voices; CUDA greedy decode is not bit-stable word-for-word
  (tests assert sentence frames, not single words).

## D-039: Per-host SEO — dynamic root layout via x-avokatim-country (2026-08-01)

- Context: the mobile audit found the DE host serving `<html lang="sq">`,
  Albanian titles/descriptions, Kosovo JSON-LD, a sitemap with Kosovo URLs
  (plus the dead `/apliko` link) and an Attorney ItemList containing XK
  lawyers. For a German market launch this is disqualifying: crawlers and
  AI assistants would classify de.avokatiim.ai as an Albanian site.
- Decision: SEO surfaces are resolved per request from the
  `x-avokatim-country` header the proxy already sets (D-034). New
  `lib/seo.ts` exposes `serverCountry()` + `COUNTRY_BASE_URL`; the root
  layout, the 7 public layouts with page metadata, `sitemap.ts` and
  `robots.ts` switched from static exports to async `generateMetadata`/
  functions reading it. Server-side fetches for JSON-LD/sitemap now pass
  the country header explicitly (they'd otherwise fall back to XK).
- Consequences: those routes render dynamically (headers() is a
  request-time API) — fine, we serve through Next ourselves, no static
  CDN. Adding a jurisdiction means adding its strings to the layouts and
  its base URL to `COUNTRY_BASE_URL`. Legal pages (kushtet/privatesia/
  impressum/kontakti) still have static Albanian metadata — acceptable for
  now, tracked in JOURNAL 2026-08-01i.

## D-040: Prozesskostenrechner — GKG table as data, § 91 ZPO risk model (2026-08-01)

- Context: German citizens' first question before suing is "what does it
  cost me if I lose?". Established market calculators (ERGO, Deubner)
  combine RVG lawyer fees with GKG court fees per instance. We already had
  the RVG side (D-037); court fees and the risk composition were missing.
- Decision: the § 34 GKG / Anlage 2 fee table lives in
  `seeds/germany.py` as `DE_GKG_TABLE` in the exact same band format as
  `DE_RVG_TABLE` (base fee up to 500 €, fixed increment per started step;
  values of the KostBRÄG 2025 version in force since 2025-06-01, verified
  against gesetze-im-internet.de and BGBl. 2025 I Nr. 109). The band
  walker was generalized (`rvg.banded_fee`) so both tables share one
  implementation. Per-instance composition is data too
  (`DE_PROZESSKOSTEN_INSTANCES`): KV 1210/1220/1230 court rates and the
  lawyer VV items per instance (3100/3104, 3200/3202, 3208/3210 — the
  same convention the market calculators use, incl. 2.3 for the mandatory
  BGH counsel in revision). `services/prozesskosten.py` only computes:
  loser pays both lawyers + court fees (§ 91 ZPO), VAT on lawyers only,
  VV 7002 per instance/lawyer, § 12 GKG filing advance.
- Consequences: a future fee amendment is a seed edit, no code. The public
  endpoint is DE-host-only (`_require_de`) like the RVG one; the lawyer
  endpoint gives offices the same numbers for client advice. The § 12a
  ArbGG labor-court exception is a UI note, not modeled — acceptable for
  an informative tool.

## D-041: Online-Verfahren assistant — pilot courts as data, RDG-safe citizen side (2026-08-01)

- Context: Germany's civil online procedure went live 2026-04-15 (payment
  claims ≤ 10,000 € + air passenger rights, 18 pilot local courts,
  service.justiz.de, reduced 2.0 court fee). No practice-management tool
  owns this workflow yet — first-mover window.
- Decision: pilot courts live in `seeds/germany.py` (`DE_OV_COURTS` with
  scope + live_from, set by Land ordinances and expected to grow) — the
  service (`online_verfahren.py`) only evaluates: value cap, court match,
  flight detection, fee comparison. Eligibility `checks` use stable codes
  localized client-side. Klageschrift generation reuses the existing
  DocumentTemplate machinery (two new seeded templates), no new renderer.
  `ov-export` returns format-neutral JSON (`avokatim.ov-export/v1`) until
  the BMJV publishes the lawyer-side XJustiz submission spec — we don't
  guess a schema we'd have to break.
- Citizen side is information-only (RDG § 2: no individual legal advice):
  a static pointer card to the official portal, shown when a deterministic
  matcher (flight keywords or € amount ≤ 10k) fires on the case text —
  no LLM judgment, no recommendation of a course of action.
- Consequences: when courts join/leave the pilot, we edit a seed list.
  The lawyer endpoints 404 for non-DE matters, and the app button hides
  itself by probing. Both OV endpoints write audit-log entries (rule §5.8).

## D-042: Hybrid retrieval — RRF over 3 legs, rare-word FTS instead of plain BM25 (2026-08-01)

- Context: legal research is the #1 AI use in German firms. Pure vector
  search misses exact statutory terms ("§ 573c BGB": 1/6 hit rate on
  citation-style queries) and the federal case-law corpus (16.8k decisions,
  `rechtsprechung-im-internet.de`) floods any naive full-text ranking —
  judgments repeat terms like "BGB" hundreds of times.
- Decision: `search_corpus` fuses three rankings with standard RRF (k=60,
  equal weights — weighted RRF was tested and rejected: with k=60 a
  down-weighted leg can never surface anything into the top-6 on its own):
  1) pgvector cosine, 2) `plainto_tsquery` AND (verbatim phrases),
  3) a rare-word OR leg: up to 4 query words with chunk document frequency
  ≤ 2% (one GIN-backed count per word), prefix-matched (`:*`) so "Berufung"
  finds "Berufungsfrist". The df cap is the IDF substitute — Postgres FTS
  has no BM25, and common words flood the ranking with judgment chunks.
  Judgments are capped at `limit//3` of the final slots so statutes stay
  the primary grounding; case law enriches, never displaces the law.
- Measured (eval_de_recherche.py, same corpus state): natural-language
  §-recall 9/14 = vector baseline; explicit §-citations 5/6 vs 1/6.
  Known limit: German compounds (Kündigungsschutzklage ↛ KSchG § 4 text)
  need better embeddings or compound splitting — future work.
- tsv column is populated in Python on insert (corpus API) + backfilled by
  migration; a generated column was rejected because the ts config depends
  on the parent doc's language (cross-table).

## D-043: Back-office agents — suggest → human accept, never auto-execute (2026-08-01)

- Context: German lawyers report ~49.5% of their time is non-billable
  admin. The biggest wins are automating intake of court mail (deadlines),
  dunning (Mahnwesen) and email filing — but a legal tool must never act
  on its own (BRAK KI-Leitfaden human-oversight principle, and a wrong
  auto-created deadline is worse than none).
- Decision: every back-office automation follows the `TimeSuggestion`
  pattern — a *Suggestion row with `status=pending` that the lawyer
  explicitly accepts or dismisses. First instance: `DeadlineSuggestion` —
  background LLM scan on document upload / email attachment (through the
  `app/llm/` abstraction only), matched against `DeadlineRule` by
  normalized legal basis (§/Art. + law code, e.g. "§ 517 ZPO" ↔
  "ZPO § 517") plus weighted title-token overlap (longer tokens weigh
  more, so German compounds like "Berufungsbegründungsfrist" carry the
  match). Accept path reuses the rule engine (`create_deadline_from_rule`)
  when a rule + trigger date matched, so holiday/notfrist logic stays in
  one place; otherwise a plain deadline from the extracted date.
- Scan is fire-and-forget (`asyncio.create_task`) with its own DB session;
  failures only log — an LLM outage must never break a document upload.
  Suggestions are per-document deduped (skip if any suggestion exists).
- Consequences: Mahnwesen drafts and sender→matter email classification
  (F4 parts 2–3) reuse the same suggest/accept contract; nothing sends or
  files automatically.

## D-044: BRAK compliance is a product feature — register + review gate (2026-08-01)

- Context: DSGVO/confidentiality worry is the #1 adoption blocker for AI
  in German firms (38.9%), and the BRAK KI-Leitfaden asks for documented
  AI use and human oversight. Competitors treat compliance as paperwork;
  we can sell it as a feature.
- Decision: two mechanisms, both on by default. (1) A per-office
  **KI-Nutzung register** derived from the existing append-only audit log
  (no new tracking) with CSV export — documentation duty solved from data
  we already keep. (2) A **human-review gate**: AI-assisted documents get
  `ai_generated=true` at creation; `require_ai_review` blocks the two
  exits from the firm (client-portal visibility, signature request) until
  `confirm-ai-review` sets `ai_reviewed_by/at`. Enforced in the API, not
  the UI, so future exit paths inherit the gate by calling the same
  helper. Complemented by a seeded Art. 30 DSGVO Verarbeitungsverzeichnis
  template covering the platform's AI features.
- Alternatives rejected: a blocking review modal before every AI output
  (friction, would be clicked away); flagging at send-time by content
  heuristics (unreliable — provenance at creation is exact).
- Consequences: new AI-generated document paths must set `ai_generated`
  and new outbound paths must call `require_ai_review`; the review stamp
  is user-visible, so the flag must never be set speculatively.

## D-045: DE go-to-market in-product — 0% positioning, RSV tracking, static Ratgeber (2026-08-01)

- Context: the dominant German marketplace charges lawyers a per-mandate
  "Infrastrukturgebühr" (~34%); legal-expense insurance (RSV) initiates a
  large share of consumer mandates; and consumer-law guides are the main
  organic acquisition channel (SEO/GEO).
- Decision: (1) state our model — fixed subscription, 0% commission per
  mandate — explicitly on /per-avokatet for the DE host, with careful
  wording and **no competitor named in the UI**. (2) Treat the
  Deckungsanfrage as a first-class workflow on the matter: insurer
  directory as seed data (`DE_INSURERS`), one-click letter via the
  existing template into the documents, and a 3-state
  `insurance_status` on `Matter` with a 14-day follow-up nudge — no email
  automation, the lawyer sends the letter (D-043 principle). (3) Ship the
  10 highest-demand consumer guides as **static TS data** rendered
  server-side at /ratgeber/[slug] with Article JSON-LD and RDG-safe
  disclaimers — no CMS, no LLM-generated content without lawyer review;
  articles are German-only and appear only in the DE sitemap.
- Consequences: insurer contact data must be verified before production
  use (noted in seed); new guides are added by editing `ratgeber.ts`
  (reviewed content only); if the guide count grows past ~30, revisit the
  no-CMS decision.

## D-046: BRAV auto-verification by unique name match (2026-08-01)

- Context: Kosovo lawyers auto-verify via a confirmed email that matches
  the OAK registry (strong proof — the chamber publishes member emails).
  BRAV publishes NO emails, so German lawyers always landed in the manual
  queue (D-034). The BRAV portal (bravsearch.bea-brak.de) has no API — it
  is a JSF/PrimeFaces app — but it is searchable programmatically (GET
  session + ViewState, partial-ajax POST of the search form; needs a
  browser User-Agent, non-browser agents get 503).
- Decision: auto-approve a German lawyer only when the confirmed-email
  signup name has EXACTLY ONE active Rechtsanwalt match in the whole
  register (`services/brav.py` client + `_try_auto_verify_brav`). This is
  a weaker proof than the OAK email match (name ≠ mailbox ownership), so
  the safeguards are: unique-match-only (a result list longer than one
  page can never auto-approve — unseen namesakes), name normalization
  (umlauts ü↔ue↔u, academic titles) before comparing, operators always
  get an FYI (same as OAK), the action is audited
  (`platform.verification_auto`, registry=BRAV) and revocable from
  /platform. Namesakes → operator queue with candidates in the note;
  portal down/no match → old behavior (manual one-click search link).
- Also: `POST /platform/verifications/{id}/decide` no longer demands
  `oak_license_no` for DE (BRAV publishes no license numbers); the queue
  shows the jurisdiction's chamber label (`bar_name`) instead of a
  hardcoded "OAK".
- Alternatives rejected: scraping the whole BRAV register into a local
  CSV like OAK (170k+ entries behind a stateful JSF UI, no stable bulk
  access, legally murkier than single lookups); keeping DE fully manual
  (does not scale and loses signups to friction).
- Consequences: the portal is flaky (beA outages 503 everything) — the
  client degrades to None and verification falls back to manual, never
  blocking signup; if BRAV ever changes its JSF markup the fixtures in
  `tests/fixtures/brav_*.xml` and `_CARD_RE` must be re-recorded.

## D-047: Kosovo litigation cost calculator over UA 03/2025 (2026-08-01)

- Context: DE has a Prozesskostenrechner (D-040); Kosovo had nothing
  although its court fees just changed drastically — the KGJK's UA
  Nr. 03/2025 on the unification of court fees is in force since
  2026-01-01 (fees up 200–900%), which makes "sa do të më kushtojë?"
  a high-value public question.
- Decision: same data-not-code pattern as DE. `XK_COURT_FEE_TABLE` in
  `seeds/kosovo.py` (civil + commercial tracks, appeal/extraordinary =
  50%), `services/xk_cost_risk.py` computes per instance (court fee +
  both lawyers per the OAK tariff nr. 6/7 + 30% paushall + VAT 18,
  loser-pays per nenet 449/452 LPK). One shared endpoint pair, resolved
  per jurisdiction: `/fee-calc/process-cost` by tenant country,
  `/public/tools/process-cost` by host. Public page `/kostoja` (XK host
  only, Albanian SEO), billing card for XK offices.
- Sourcing caveat: the KGJK has not published the UA 03/2025 PDF at a
  stable URL (its own online calculator still serves the 2017 values).
  Bands were cross-verified from detailed legal-press coverage
  (Betimi për Drejtësi, KosovaPress, Bar commentary). The >100k€ civil /
  >500k€ commercial rule is encoded as 0.5% capped at 2,500/10,000 €
  (caps are reported verbatim; 0.5% continues the 2017 methodology and
  reproduces both caps exactly). When the official PDF surfaces, verify
  and adjust the seed.
- Consequences: fee updates are seed edits, no code change; the DE
  calculator behavior is unchanged (regression-tested).

## D-048: Per-country public guide articles — Albanian udhëzues (2026-08-01)

- Context: the DE host has 10 curated Ratgeber guides (D-045) that pull
  organic search traffic toward Ava/posto-rastin; the XK host had no
  equivalent although the same questions dominate citizens' searches in
  Kosovo (largimi nga puna, përmbarimi, qiraja, trashëgimia...).
- Decision: guide content becomes per-country data on one shared shape.
  `RatgeberArticle` gains a `country` field; German articles stay in
  `frontend/src/lib/ratgeber.ts` (country "DE"), the 10 new Albanian
  ones live in `frontend/src/lib/udhezues.ts` (country "XK") to keep
  file sizes sane. Separate routes per market — `/ratgeber` (German UI)
  and `/udhezues` (Albanian UI) — rather than one parametrized route:
  the URLs are themselves SEO keywords on each host. Same Article
  JSON-LD (inLanguage "sq"), per-host canonical, sitemap scoping
  (`only: XK` + per-article entries on the XK sitemap only), footer +
  tools-dropdown links per host, and the not-legal-advice disclaimer.
- Content sourcing: written against the cited Kosovo statutes (Ligji i
  Punës 03/L-212, LPP 04/L-139, LMD 04/L-077, Ligji për Trashëgiminë
  2004/26, Ligji për Familjen 2004/32, Ligji 04/L-018, LPPA 05/L-031,
  LKA 03/L-202); where an exact figure is not certain from the statute
  text the article states the rule generally instead of inventing a
  number. Still static data, no CMS — reviewed 2026-08.
- Consequences: adding a guide = one array entry; a future third
  jurisdiction adds its own data file and route pair without touching
  the article components.

## D-049: 0%-commission positioning on both hosts; RSV stays DE-only (2026-08-01)

- Context (parity pass B4): the "fixed subscription, 0 % commission per
  mandate" section on /per-avokatet was DE-only (D-045), yet the claim
  is true of the product everywhere and referral platforms taking fee
  shares exist in Kosovo too. Conversely the Deckungsanfrage/RSV flow
  (insurer directory, coverage-request letters, /posto-rastin insurance
  question) could have been ported to XK for symmetry.
- Decision: (1) the positioning card renders on both hosts with the
  same market-neutral wording (keys renamed lpDe0* → lp0*); the BRAK-KI
  compliance checklist below it stays DE-only since it cites German
  professional rules. (2) The RSV/Deckungsanfrage feature set is
  deliberately NOT ported to Kosovo: a private legal-expenses-insurance
  market does not exist there in any practical form, so the flow would
  be dead UI. This is a documented decision, not an omission — revisit
  only if an XK insurer starts selling RSV-type policies.

## D-050: Kosovo case law in the corpus via the KGJK publication portal (2026-08-01)

- Context (B3): hybrid search + judgment citations shipped with D-042,
  but the XK corpus held 0 judgments. Feasibility spike on the official
  publication portal gjyqesori-rks.org/aktgjykimet/ came back a clear
  GO: 290k+ published decisions (Supreme alone 21k), server-rendered
  listing that accepts STATELESS GET filters
  (?r=M&courtId=<id>&judgeStatus=1&ordBy=v.publicationDtTm&ordDir=DESC
  &offset=<n>, 20 rows/page), rows carry case type/number, decision +
  publication dates, judge, court and a direct PDF link; the PDFs are
  text-native Albanian (no OCR needed for the sampled majority).
- Decision: importer `backend/scripts/import_xk_judgments.py` modeled
  on the DE one — listing page → Albanian (_SQ) PDF → pypdf text →
  corpus API (doc_type="judgment", language "sq", reference = the
  official designation printed in the judgment, e.g. "Rev.nr.46/2026",
  falling back to portal type code + number). Defaults: Supreme Court,
  last 5 years; --courts supreme,apeli,komerciale,<7 basic courts>,
  --years, --limit. Resumable twice over: processed PDF URLs in
  data/xk_judgments_state.txt + reference dedup against the corpus.
- Constraints found: Cloudflare rate-limits bursts (429 after ~15 quick
  requests, then 503) — the importer paces at 2.5s/doc and backs off
  60/120/180/240s on 429/503. Some rows publish only the Serbian PDF —
  skipped to keep the judgment corpus consistently Albanian ("sq" FTS
  config); revisit if SR-language retrieval becomes a priority.
- Ava: the public XK prompt now names published Kosovo case law among
  its sources and requires citing court + case number ONLY when the
  decision is provided as an excerpt (same anti-hallucination rule as
  the DE prompt, D-042). Eval `scripts/eval_xk_recherche.py` guards
  both directions: 12 statute questions must not regress (max_judgments
  cap in _rrf_fuse) and case-law questions should start retrieving
  judgments.

## D-051: Public stats split laws vs judgments; UI copy catches up with case law + new tools (2026-08-02)

- Context: after D-042 (DE, ~15.4k federal decisions) and D-050 (XK,
  ~2.5k Supreme decisions after the full backfill), the public
  `laws_in_corpus` counter silently mixed judgments into a number
  labelled "laws and acts" — inflated and dishonest (XK would have
  shown ~3.1k "laws"). Marketing/Ava copy also still described a
  statutes-only corpus, and the free-tools listings predated
  /kostoja, /udhezues, /rvg cost tab and /ratgeber.
- Decision: `/api/public/stats` excludes `doc_type="judgment"` from
  `laws_in_corpus` and returns a separate `judgments_in_corpus`;
  the landing page and /per-avokatet render it as its own counter
  (hidden while 0, so a fresh jurisdiction shows no empty stat).
  Copy in all 7 locales now says "laws AND published case law" in the
  Ava/marketing/assistant strings, and the tools listings (FAQ,
  citizen page, landing feature list) include the litigation cost
  calculator and the public guides, host-aware (XK: /kostoja +
  /udhezues; DE: /rvg + /ratgeber).
- Kept: `mkAvaDisclaimer` unchanged (legal-information disclaimer does
  not need a source inventory); `umbFnC1` unchanged (languages/voice
  bullet, case law covered by umbWhy2/umbFnL7).
- Files: `backend/app/api/marketplace.py`, `frontend/src/app/page.tsx`,
  `frontend/src/app/per-avokatet/page.tsx`,
  `frontend/src/app/per-qytetaret/page.tsx`,
  `frontend/src/components/public-shell.tsx`,
  `frontend/src/lib/dictionaries.ts`.

## D-052: Ava everywhere — floating public launcher + contextual lawyer panel; AI named in all core claims (2026-08-02)

- Context: the AI is the product's main differentiator but (a) core
  marketing claims (umbWhy1De, lpSubtitle, umbCitizenB, Ava titles)
  did not name it, and (b) the assistant was only reachable as a
  destination page — on mobile that means losing your place. Industry
  research (Aug 2026): consumer products use a bottom-right floating
  launcher (~90% of chat widgets); lawyer-facing suites (Clio Manage AI,
  Smokeball Archie, AnNoText Expert AI) never use a bubble — they use a
  persistent nav entry + a matter-context side panel. Table stakes:
  the assistant knows which matter you are viewing.
- Decision (public): extract the Ava chat core out of /ava into
  `components/ava-chat.tsx` (session, quota, SSE stream, voice,
  examples, structure-case, DE Bundesland, OV pointer) and add
  `components/ava-launcher.tsx` — a labeled FAB (bottom-right,
  bottom-20 on mobile to clear the z-40 bottom nav + center SOS,
  safe-area insets) opening a full-screen sheet on mobile / 420px
  bottom-right panel on desktop. Mounted in PublicShell (~20 pages)
  and directly on /per-avokatet + /per-noteret (no shell). Hidden on
  /ava. Session/quota shared with the page via localStorage.
- Decision (lawyer app): `components/assistant-panel.tsx` mounted in
  (app)/layout — persistent labeled launcher + right slide-over with
  the legal streaming chat (ask-stream/deep-research, voice, citations,
  Law 06/L-082 transparency line). Context awareness: on /matters/[id]
  the panel auto-scopes to that matter and shows a removable chip.
  Panel stays mounted (hidden, not unmounted) so the conversation
  survives navigation. Conversation list + office mode stay on
  /assistant ("open full assistant" link). Hidden on /assistant.
- Copy: AI added to umbWhy1De, lpSubtitle, umbCitizenB, mkAvaTitle,
  landAvaT in all 7 locales; new keys avaFabLabel, apOpenFull,
  apMatterCtx. Root SEO already named KI/AI (D-039) — unchanged.
- Deferred (backlog): action execution with approval from the panel,
  "ask Ava" row in global search (Cmd+K), embedded Ava in /rasti-im.
- Files: `frontend/src/components/{ava-chat,ava-launcher,assistant-panel}.tsx`,
  `frontend/src/app/ava/page.tsx`, `frontend/src/components/public-shell.tsx`,
  `frontend/src/app/(app)/layout.tsx`, `frontend/src/app/per-avokatet/page.tsx`,
  `frontend/src/app/per-noteret/page.tsx`, `frontend/src/lib/dictionaries.ts`.

## D-053: Assistant action execution with approval + Ask-Ava in Cmd+K + Ava card in the citizen portal (2026-08-02)

- Context: the D-052 backlog — the Clio Duo / AnNoText Expert AI
  standard is "the assistant proposes, the lawyer approves": answers
  should turn into deadlines and drafts without leaving the panel.
  Mobile is the priority surface.
- Decision (actions): two new assistant routes, no new create paths.
  `POST /assistant/actions/extract-deadlines` {matter_id, text} reuses
  `extract_deadlines_from_text` and returns proposals only (same
  ExtractedDeadline shape as collab, zero side effects); creation goes
  through the existing `POST /matters/{id}/deadlines/bulk` after the
  lawyer ticks each proposal. `POST /assistant/actions/save-draft`
  {matter_id, title, content} reuses `file_content_as_pdf` with
  `ai_generated=True`, so the D-044 human-review gate blocks
  sharing/signature until confirm-ai-review. Both audit-logged
  (assistant.extract_deadlines / assistant.save_draft).
- Decision (panel UI): action chips ("📅 extract deadlines",
  "📄 save as draft") under every assistant answer when a matter is in
  scope; proposals render as a checkbox list (undated ones disabled —
  bulk skips them), drafts get a title field; success notice links to
  the matter. One in-flight action at a time.
- Decision (global search): Cmd+K/Ctrl+K now focuses the search box;
  the dropdown's first row is "Ask Ava: «query»" which fires the
  `avokatim:ask-ava` CustomEvent — the assistant panel opens with the
  question prefilled (not auto-sent; sending stays a human act).
- Decision (citizen portal): /rasti-im gets a gradient Ava card under
  the intro firing `avokatim:open-ava`, which the public AvaLauncher
  listens for — the citizen opens the full-screen sheet (mobile) or
  side panel without losing the case view. No second embedded chat:
  one shared session/quota via the launcher.
- New dictionary keys ×7: apActExtract, apActDraft, apActCreate,
  apActNoDl, apActDlDone, apActDraftDone, apDraftTitle, gsAskAva, rmAvaB.
- Files: `backend/app/api/assistant.py`,
  `backend/tests/test_assistant_actions.py`,
  `frontend/src/components/{assistant-panel,global-search,ava-launcher}.tsx`,
  `frontend/src/app/rasti-im/page.tsx`, `frontend/src/lib/dictionaries.ts`.

## D-054: Technology-leadership wave — notifications, agentic AI, proactive AI, 24/7 receptionist, UX detail pass, local observability (2026-08-02)

- Context: full comparison with the 2026 industry frontier (Harvey Agent
  Builder, Clio Vincent agentic mode, Legora end-to-end vision, RA-MICRO
  KI Widget, Smith.ai/ElevenLabs AI receptionists, ambient-AI trend).
  We matched the leaders on in-context AI and approval-gated actions but
  lacked in-app notifications/realtime, agentic multi-step execution,
  proactive monitoring, a 24/7 intake channel, and 2026 UX table stakes.
- Decision (F1, foundation): one `Notification` model + `/notifications`
  API + lightweight SSE stream, with a per-user, per-kind "interrupt
  budget" (push vs. center-only) in Settings. All existing sources
  (deadlines, suggestions, email, Mahnung, intake, messages) write here
  alongside email/push — one place to look, user-controlled interruption.
- Decision (F2, agentic): `POST /assistant/agent-run` (SSE) — the LLM
  plans visible steps from a goal and executes read-only tools
  sequentially; anything that writes (deadlines, drafts) emits approval
  events consumed by the D-053 approval UI. Human-on-the-loop is kept as
  our BRAK-conform differentiator; every run lands in the KI-Register
  (D-044).
- Decision (F3, proactive): three background agents in `reminder_loop`
  (morning briefing with local TTS; case-law monitor matching new corpus
  judgments to open matters via local embeddings — active linkage no
  competitor offers; deadline audit). All respect the interrupt budget,
  none acts without approval.
- Decision (F4, receptionist): hands-free voice conversation mode in the
  public Ava chat (local STT→LLM→TTS loop — privacy-safe Albanian voice
  no one else has), and the WhatsApp bot upgraded to full intake: a
  Redis state machine ("RAST" → describe/city/name/email) that posts a
  structured marketplace case, alerts matching lawyers (incl. F1
  center) and offers real consultation slots in-chat. AI is declared in
  the first message (RDG/BRAO).
- Decision (F5, UX): passkeys/WebAuthn (passwordless login skips TOTP —
  a passkey is already MFA) + sliding sessions; opt-in dark mode via a
  `.theme-dark` utility remap (no second design system); Cmd+K becomes a
  command palette (fuzzy actions + pg_trgm typo-tolerant search);
  skeletons + optimistic updates; PWA install banner only after real
  engagement; haptics on key actions.
- Decision (F6, observability): GlitchTip self-hosted in the existing
  compose stack (own DB in avokatim-db, Redis DB 2) instead of SaaS
  Sentry — errors never leave the machine. Frontend errors relayed
  through our own `POST /api/public/client-error` (rate-limited, no PII)
  rather than shipping a Sentry browser SDK: one dependency less, same
  visibility. Product usage as Umami custom events (`lib/analytics.ts`),
  counts only.
- Files: see the six F1–F6 entries in `docs/agent/CHANGELOG.md`
  (2026-08-02); commits a63111a, 0bfcd39, d503020, ea338ac, 600a3be + F6.
