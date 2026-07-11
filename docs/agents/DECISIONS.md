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
