# CHANGELOG — dated trail of changes (newest on top)

> One entry per finished piece of work. Never optional (Definition of Done).
> Format: date, what changed, why, files touched.

## 2026-08-02 — Per-country pricing: DE 39 €/user + 3-month trial (D-057)

- German market analysis (competitors 50–109 €/user/month net, 12–36
  month minimum terms) → DE terms: 39 €/user/month, 90-day free trial,
  no minimum term. XK untouched (24 €, 365-day trial).
- `JurisdictionProfile.trial_days` + `.plan_price_eur`; signup sets both
  on the tenant; trial-ending emails made duration-neutral (×7 locales);
  7 pre-launch DE trial tenants updated to 39 €.
- Frontend: `COUNTRY_PRICING` + `fmtPricing()` in `lib/country.ts`;
  pricing keys now carry `{price}`/`{months}` placeholders (startTrial,
  trialTerms, lpPlanTrial, lpPlanPaid, landLawB, subUpgradeHint ×7);
  new `lpPlanNoTerm` bullet; DE SEO description states the offer.
- Files: `backend/app/jurisdictions.py`, `backend/app/api/auth.py`,
  `backend/app/i18n.py`, `backend/app/services/platform_billing.py`,
  `frontend/src/lib/{country.ts,dictionaries.ts}`,
  `frontend/src/app/{per-avokatet,per-noteret,regjistrohu,login}/page.tsx`,
  `frontend/src/app/per-avokatet/layout.tsx`.

## 2026-08-02 — DE rebrand: "Ava Legal" as country data (D-056)

- The German host now trades as **Ava Legal** (owner's pick); Kosovo keeps
  AvokatIM. Brand is data, not a fork: `JurisdictionProfile.brand_name`
  backend-side, a single `rebrand()` interceptor in `I18nProvider` (all
  dictionary strings) + `<Brand/>` wordmark + `COUNTRY_BRAND` (SEO,
  JSON-LD, manifest) frontend-side.
- Country-aware brand applied to: `_DE` i18n catalog (41 strings), reset
  email (German body for DE tenants), team invites, passkey rp_name,
  ICS calendar name, subscription payment description, invoice PDF
  footer, DATEV export header, public Ava DE prompt, public-tools PDF
  footer, impressum, AGB/Datenschutz, ratgeber JSON-LD.
- Files: `backend/app/jurisdictions.py`, `backend/app/i18n.py`,
  `backend/app/api/{auth,team,passkeys,calendar_feed,subscription,bookings,marketplace,public_tools}.py`,
  `backend/app/services/{invoice_pdf,datev,assistant}.py`,
  `frontend/src/lib/{i18n.tsx,seo.ts,legal.ts}`,
  `frontend/src/components/{brand,public-shell,public-footer}.tsx`,
  `frontend/src/app/{layout,manifest,page,...}`.

## 2026-08-02 — Accountant CSV export (DE→XK parity)

- DE→XK parity audit found two candidate gaps; one was already closed
  (the OAK fee-tariff picker in the invoice form inserts Tarifa e OAK
  items as invoice lines — the RVG-calculator analog). The real gap:
  Kosovo offices had no accounting export (DE has DATEV EXTF).
- New `GET /export/accounting?date_from&date_to`: semicolon CSV with
  UTF-8 BOM, one row per sent/paid invoice issued or paid in the
  period (number, dates, client, net/VAT/gross, status, payment
  reference); audit-logged. Available to every office regardless of
  country — DE offices whose accountant doesn't use DATEV benefit too.
- Billing UI: `AccountingExportCard` (same period picker as DATEV)
  shown when the office is not German; new keys `accTitle`/`accExport`
  ×7 locales.
- Files: `backend/app/api/exports.py`,
  `frontend/src/app/(app)/billing/page.tsx`,
  `frontend/src/lib/dictionaries.ts`.

## 2026-08-02 — UX-wave bullet on the homepage (D-055 follow-up)

- Owner asked for the UX details on the front page too: new lawyer
  bullet `umbFnL11` ×7 (passkeys, dark mode, Cmd+K palette) on `/`,
  placed before the SOS bullet. Verified on the running site.
- Files: `frontend/src/lib/dictionaries.ts`, `frontend/src/app/page.tsx`.

## 2026-08-02 — What's-new card refreshed for the D-054 wave (D-055 F4)

- Dashboard `WhatsNewCard` bumped to `avokatim:whatsnew:2026-08` — it
  reappears once for every lawyer with four items: Ava Agent (link to
  /assistant), morning briefing + notification center (link to
  Settings → notifications), passkeys (link to Settings → security),
  and dark mode/Cmd+K. Old `wnPrepare/wnStyle` keys replaced by
  `wnAgent/wnBriefing/wnPasskey/wnUx` (+CTAs) ×7 locales.
- Verified: pytest 245 PASS, frontend build OK, restart + health OK,
  both hosts (sq/de) serve the new marketing copy.
- Files: `frontend/src/app/(app)/dashboard/page.tsx`,
  `frontend/src/lib/dictionaries.ts`, docs.

## 2026-08-02 — D-054 features surfaced in public marketing (D-055 F3)

- The public pages caught up with the product (audit showed none of the
  D-054 wave was marketed). New/updated keys ×7 locales:
  - `/per-avokatet`: AI section now six cards — new `lpAi5T/B` (Ava
    Agent: give the goal, visible steps, every write approved) and
    `lpAi6T/B` (proactive AI: spoken morning briefing, case-law monitor
    on active matters, deadline audit) lead the grid; `lpAiSub` says
    six. `lpFeat9` now sells the real-time notification center with
    interrupt control; new `lpFeat10` (passkeys, dark mode, Cmd+K
    palette, typo-tolerant search).
  - `/` umbrella: new lawyer bullet `umbFnL10` (agent + proactive AI);
    `umbFnC1` mentions hands-free voice conversation.
  - `/per-qytetaret`: `landAvaB` describes the voice conversation
    (you talk, she listens and answers out loud).
  - SEO: `/per-avokatet` meta description (sq + de) leads with the
    agent and proactive AI.
- WhatsApp/RAST stays unadvertised (existing decision until the channel
  has production credentials).
- Files: `frontend/src/lib/dictionaries.ts`, `frontend/src/app/page.tsx`,
  `frontend/src/app/per-avokatet/{page,layout}.tsx`.

## 2026-08-02 — GlitchTip owner credentials + real SECRET_KEY (D-055 F2)

- Set a proper `GLITCHTIP_SECRET_KEY` and a known password for
  `owner@avokatiim.ai`; both noted in the compose `.env` (git-ignored,
  same pattern as the Umami admin note). Containers recreated; error
  pipeline re-verified end-to-end (event count grew).
- Files: `docs/agents/STATE.md` (compose `.env` is untracked).

## 2026-08-02 — WhatsApp intake localized + country-scoped (D-055 F1)

- New `country_for_phone()` in `jurisdictions.py`: sender's phone prefix
  → country (49 → DE, 383 → XK, unknown → XK); longest-prefix match over
  the jurisdiction profiles.
- All WhatsApp-facing strings moved to the backend i18n catalog as
  `wa_*` keys ×7 locales (intake steps, done/slots/error, daily quota,
  Ava-unavailable, once-a-day hint). Start words now also SLUCAJ/DAVA,
  cancel words also OTKAZI/IPTAL; each locale's hint names its own
  keyword (RAST/FALL/CASE/SLUCAJ/DAVA).
- Country scoping fixed: `CitizenUser`/`CaseRequest` from WhatsApp get
  the detected country+locale (was hardcoded XK/sq — German senders'
  cases were invisible to DE lawyers per the D-034 filter); slot offers
  and `_notify_matching_lawyers` filter by that country; links use
  `public_base_url_for(country)` (de.avokatiim.ai for +49).
- WhatsApp Ava Q&A now passes country+locale to `_ava_prepare` — German
  senders get the DE corpus and German framing.
- Classifier prompt switched to English (descriptions arrive in any
  language).
- Files: `backend/app/{jurisdictions,i18n}.py`,
  `backend/app/services/wa_intake.py`, `backend/app/api/whatsapp.py`,
  `backend/tests/test_wa_intake.py`.

## 2026-08-02 — Observability: local GlitchTip + product events (D-054 F6)

- GlitchTip v5.1 self-hosted in docker-compose (web 127.0.0.1:8010 +
  celery worker + one-shot migrate; own `glitchtip` DB in avokatim-db,
  Redis DB 2 as broker; registration disabled). Errors never leave the
  machine.
- Backend: `sentry-sdk[fastapi]`, init in `main.py` when `SENTRY_DSN` is
  set (no PII, no traces). DSN in `backend/.env`.
- Frontend: `components/error-reporter.tsx` in the root layout relays
  window.onerror + unhandledrejection (deduped, ≤5/session, sendBeacon)
  to new `POST /api/public/client-error` (rate-limited 10/h/IP), which
  forwards to GlitchTip tagged `source=frontend`.
- Product events in Umami via `lib/analytics.ts` `track()`: ava_ask,
  ava_voice_convo, agent_run, case_posted, pwa_install, passkey_added.
- Files: `docker-compose.yml`, `backend/app/{main,config}.py`,
  `backend/app/api/feedback.py`, `backend/requirements.txt`,
  `frontend/src/components/{error-reporter,install-banner,ava-chat,assistant-panel}.tsx`,
  `frontend/src/lib/analytics.ts`, `frontend/src/app/layout.tsx`,
  settings + posto-rastin pages.

## 2026-08-02 — 24/7 receptionist: voice conversation + WhatsApp intake (D-054 F4)

- Voice conversation mode in the public Ava chat (page + launcher panel):
  "🎙 Bisedo me zë" toggle — mic → auto-send → answer spoken aloud via the
  local Piper/browser TTS → mic again, hands-free; speech is interrupted
  when the user starts talking again. New i18n keys `vcMode`/`vcOn` (7 langs).
- WhatsApp bot upgraded from Q&A to full intake (`services/wa_intake.py`):
  "RAST"/"FALL"/"CASE" starts a Redis-backed state machine (describe → city
  → name → email, 1h TTL, ANULO cancels), LLM classifies category/city/
  urgency, then posts a structured `CaseRequest` on the marketplace
  (citizen account auto-created/reused), alerts matching lawyers (push +
  email + F1 notification center) and offers the next free consultation
  slots from bookable lawyers right in the chat. AI self-declaration in the
  first message (RDG/BRAO-safe). Q&A replies append a once-a-day RAST hint.
- Files: `backend/app/services/wa_intake.py`, `backend/app/api/whatsapp.py`,
  `backend/tests/test_wa_intake.py`, `frontend/src/components/ava-chat.tsx`,
  `frontend/src/lib/dictionaries.ts`.

## 2026-08-02 — Proactive AI: briefing, case-law monitor, deadline audit (D-054 F3)

- New: `services/proactive.py` — three background agents wired into
  `reminder_loop` (which now runs even without SMTP/push/SMS since the
  in-app center is always a channel):
  1. Morning briefing: per-tenant LLM day summary (deadlines ≤3d, pending
     suggestions/emails, overdue invoices, due tasks) after
     `briefing_hour` (default 7), redis-deduped; plain-text fallback when
     no LLM. Notification kind `briefing` + dashboard `BriefingCard` with
     local TTS ("listen to your day").
  2. Case-law monitor: judgments added to the corpus in the last 7 days
     matched against open matters via local embeddings (cosine ≤ 0.45) —
     "new Supreme Court decision touches matter X" with citation, 90-day
     dedup per matter+doc.
  3. Deadline audit: open matters with no upcoming deadline → one quiet
     (bell-only) notification per tenant per day.
- `/api/notifications` gained a `kind` filter for the briefing card.
- Files: `backend/app/services/{proactive,notifications}.py`,
  `backend/app/{config.py,api/notifications.py}`, `backend/tests/test_proactive.py`,
  `frontend/src/components/briefing-card.tsx`, dashboard page.

## 2026-08-02 — UX wave: passkeys, dark mode, palette, skeletons, PWA (D-054 F5)

- Passkeys/WebAuthn: `PasskeyCredential` model + migration, `/api/auth/passkeys/*`
  (register/list/delete + passwordless login that skips TOTP — a passkey is
  already MFA); Settings section + "Sign in with passkey" on /login
  (@simplewebauthn/browser, py_webauthn). `/auth/refresh` gives sliding
  sessions (called on app load).
- Dark mode: opt-in `.theme-dark` utility remap in globals.css (pre-paint
  script, no flash), 3-state toggle (light/dark/system) in the sidebar;
  `prefers-reduced-motion` honored globally.
- Command palette: Cmd+K now shows fuzzy-matched actions (new matter/
  deadline/invoice/contact + navigation); `/matters?new=1` deep link.
  Backend search is typo-tolerant (pg_trgm word_similarity + GIN trigram
  indexes, migration b1c2d3e4f5a6) and returns deadlines + tasks.
- Perceived performance: `Skeleton`/`SkeletonCards` on dashboard, matters,
  calendar, citizen portal; optimistic deadline mark-done; button
  micro-interaction (active scale); `haptic()` on FABs and approvals.
- PWA: install banner after 2nd visit (30-day snooze), SW registered on
  public pages too.
- Files: `backend/app/{models/passkeys.py,api/{passkeys,search,auth}.py,config.py}`,
  migrations `722e96516f77` + `b1c2d3e4f5a6`, `backend/tests/test_passkeys.py`,
  `frontend/src/components/{theme-toggle,install-banner,notification-bell,global-search,ui,assistant-panel,ava-launcher,public-shell}.tsx`,
  `frontend/src/lib/haptics.ts`, `frontend/src/app/{layout,globals.css,login,(app)/*}`.

## 2026-08-02 — Ava Agent: goal-based multi-step runs with approval (D-054 F2)

- New: `services/agent_run.py` — Ava plans steps from a goal (tool catalog:
  summarize_matter, research, extract_deadlines, draft_document,
  conflict_check, hearing_prep) and executes them sequentially. No writes:
  deadline/draft steps emit approval events consumed by the D-053 approval
  UI and endpoints. `POST /assistant/agent-run` (SSE) with plan/step/result/
  approval events; every run audit-logged (KI-Register).
- New: panel UI — "Ava Agjente" chip (matter scope only), live work-plan
  checklist (pending/running/done/failed), results land as normal messages
  so voice + action chips keep working.
- i18n: agMode, agModeHint, agPlanT, agPlanning ×7 locales.
- Files: `backend/app/services/agent_run.py`, `backend/app/api/assistant.py`,
  `backend/tests/test_agent_run.py`,
  `frontend/src/components/assistant-panel.tsx`, `lib/dictionaries.ts`.

## 2026-08-02 — Notification center + interrupt budget (D-054 F1)

- New: `Notification` model + migration; `services/notification_center.py`
  (`notify()` writes the bell row and fans out Web Push honoring the
  per-user interrupt budget in `User.notification_prefs`).
- New: `/api/notifications` (list, unread-count, read, read-all, SSE
  `stream`, prefs GET/PUT). Wired sources: deadline reminders, deadline
  suggestions, inbound email suggestions, new bookings, marketplace case
  matches + SOS, citizen case messages.
- New: `components/notification-bell.tsx` — bell with live unread badge
  (SSE + focus fallback), desktop dropdown / mobile bottom sheet; mounted
  in the app header (mobile) and next to global search (desktop).
  Settings gets `NotificationPrefsSection` (push vs bell-only per kind).
- i18n: 17 frontend keys ×7 locales; backend `ntf_suggestions_title` ×7.
- Files: `backend/app/models/notifications.py`, `backend/app/api/notifications.py`,
  `backend/app/services/{notification_center,notifications,email_ingest,deadline_suggest}.py`,
  `backend/app/api/{marketplace,bookings,main}.py`, migration `ac56305907ab`,
  `backend/tests/test_notification_center.py`,
  `frontend/src/components/notification-bell.tsx`,
  `frontend/src/app/(app)/{layout,settings/page}.tsx`, `lib/dictionaries.ts`.

## 2026-08-02 — Assistant actions with approval + Ask-Ava in Cmd+K + Ava in the citizen portal (D-053)

- New: `POST /api/assistant/actions/extract-deadlines` — Ava re-reads an
  answer and returns deadline proposals only (reuses
  `extract_deadlines_from_text`, no side effects); creation goes through
  the existing `POST /matters/{id}/deadlines/bulk` after per-item
  approval in the panel.
- New: `POST /api/assistant/actions/save-draft` — files an answer into
  the matter as a draft PDF with `ai_generated=True`, so the D-044
  human-review gate applies before sharing/signature. Both routes
  audit-logged. Tests: `backend/tests/test_assistant_actions.py`.
- Changed: `assistant-panel.tsx` — action chips under each answer when a
  matter is in scope; checkbox proposal list (undated disabled), draft
  title form, success notice linking to the matter.
- Changed: `global-search.tsx` — Cmd+K/Ctrl+K focuses the box; first
  dropdown row "Ask Ava: «query»" fires `avokatim:ask-ava` → the panel
  opens with the question prefilled.
- Changed: `rasti-im/page.tsx` — gradient Ava card fires
  `avokatim:open-ava` → the public launcher sheet opens (mobile-first,
  case view stays); `ava-launcher.tsx` listens for the event.
- Changed: 9 new dictionary keys × 7 locales (apAct*, apDraftTitle,
  gsAskAva, rmAvaB).
- Files: `backend/app/api/assistant.py`,
  `backend/tests/test_assistant_actions.py`,
  `frontend/src/components/{assistant-panel,global-search,ava-launcher}.tsx`,
  `frontend/src/app/rasti-im/page.tsx`, `frontend/src/lib/dictionaries.ts`, docs.

## 2026-08-02 — Ava everywhere: public launcher + contextual lawyer panel (D-052)

- New: `frontend/src/components/ava-chat.tsx` — public Ava chat core
  extracted from /ava (SSE streaming, quota, voice, structure-case,
  DE Bundesland, OV pointer); /ava is now chrome around it.
- New: `frontend/src/components/ava-launcher.tsx` — bottom-right FAB on
  every public page (PublicShell + /per-avokatet + /per-noteret),
  full-screen sheet on mobile (safe-area), 420px panel on desktop.
- New: `frontend/src/components/assistant-panel.tsx` — lawyer-app
  slide-over (Clio/Archie pattern): streaming legal chat, deep research,
  voice, citations; auto-scopes to the matter on /matters/[id] with a
  removable chip; conversation survives navigation.
- Changed: AI named in core marketing claims ×7 locales (umbWhy1De,
  lpSubtitle, umbCitizenB, mkAvaTitle, landAvaT); new keys avaFabLabel,
  apOpenFull, apMatterCtx.
- Files: components above, `app/ava/page.tsx`, `components/public-shell.tsx`,
  `app/(app)/layout.tsx`, `app/per-avokatet/page.tsx`,
  `app/per-noteret/page.tsx`, `lib/dictionaries.ts`, docs.

## 2026-08-02 — Honest public stats + UI copy for case law and new tools (D-051)

- Changed: `/api/public/stats` — `laws_in_corpus` now excludes
  judgments; new `judgments_in_corpus` field. Landing and /per-avokatet
  show a separate court-decisions counter (`mkStatsJudgments`).
- Changed: 13 dictionary keys × 7 locales mention published case law
  next to statutes (mkAvaIntro, avaIntro, faqA1/2, umbWhy2, umbFnL7,
  landAvaB, landToolsB, lpFeat2, lpAiSub, lpAi1B, assistantIntro,
  deepResearchHint); new `umbFnC9` free-tools bullet.
- Changed: /per-qytetaret tools card links /kostoja + /udhezues (XK) and
  /rvg + /ratgeber (DE); nav `toolsActive` covers /udhezues + /ratgeber.
- Note: overnight Supreme Court backfill finished (2,371 new, 0 failed;
  ~2.5k XK judgments total — the portal only has ~2.6k Supreme decisions
  published in the last 5 years).
- Changed (follow-up): landing "why" claim is host-aware — new
  `umbWhy1De` (7 locales, "citizen portal + complete law-office software
  in one") replaces the false "first of its kind / only digital bridge"
  claim on the DE host (UWG risk; en/tr even said "first in Kosovo");
  de-locale `umbWhy1` now says "im Kosovo" for the XK host.
- Files: `backend/app/api/marketplace.py`, `frontend/src/app/page.tsx`,
  `frontend/src/app/per-avokatet/page.tsx`,
  `frontend/src/app/per-qytetaret/page.tsx`,
  `frontend/src/components/public-shell.tsx`,
  `frontend/src/lib/dictionaries.ts`, docs.

## 2026-08-01 — Kosovo case law import + Albanian retrieval eval (D-050, B3)

- New: `backend/scripts/import_xk_judgments.py` — imports published
  judgments from the KGJK portal (gjyqesori-rks.org/aktgjykimet/,
  stateless GET filters) as `doc_type="judgment"`; Albanian PDFs only,
  official case designation as reference, 2.5s pacing + 429/503
  backoff, resumable via `data/xk_judgments_state.txt` + reference
  dedup. First batch: 150 Supreme Court decisions.
- New: `backend/scripts/eval_xk_recherche.py` — 12 statute + 4 case-law
  Albanian questions; before/after: statutes unchanged (7/9, 2/3),
  case-law presence 0/4 → 4/4.
- Changed: public XK Ava prompt (`backend/app/api/marketplace.py`) now
  includes published Kosovo case law among sources; citations with
  court + case number only when the decision is provided as an excerpt.
- Tests: `backend/tests/test_import_xk_judgments.py` (7) with fixture
  `tests/fixtures/xk_judgments_listing.html`; suite 219 passed.
- Files: `backend/scripts/{import_xk_judgments,eval_xk_recherche}.py`,
  `backend/app/api/marketplace.py`, `backend/tests/**`.

## 2026-08-01 — 0% positioning on both hosts, RSV documented DE-only (D-049, B4)

- Changed: /per-avokatet "fixed subscription, 0 % commission" card now
  renders for XK too (dictionary keys renamed `lpDe0*` → `lp0*`, same
  market-neutral wording); the BRAK-KI checklist stays DE-only.
- Decision: RSV/Deckungsanfrage deliberately not ported to Kosovo (no
  RSV market) — recorded as D-049 in `docs/agents/DECISIONS.md`.
- Files: `frontend/src/app/per-avokatet/page.tsx`,
  `frontend/src/lib/dictionaries.ts`.

## 2026-08-01 — Albanian public legal guides /udhezues (D-048, B2)

- Changed: `frontend/src/lib/ratgeber.ts` — `RatgeberArticle` gains a
  `country` field ("DE"|"XK"); German articles unchanged, tagged "DE".
- New: `frontend/src/lib/udhezues.ts` — 10 curated Albanian guides for
  Kosovo (dismissal, enforcement order, rent disputes, deposit return,
  inheritance, divorce/alimony, traffic accidents, administrative
  appeals, statute of limitations, undeclared work) with cited Kosovo
  statutes and a not-legal-advice disclaimer.
- New: routes `/udhezues` + `/udhezues/[slug]` (Albanian mirror of
  /ratgeber, Article JSON-LD inLanguage "sq", per-host canonical,
  CTA → Ava / posto-rastin).
- Changed: sitemap (`/udhezues` + per-article entries, XK host only),
  public footer + tools dropdown (XK-only link, `udhLink` key ×7
  locales).
- Verified: build OK, pages 200 with JSON-LD, XK sitemap lists 11
  udhezues URLs and no ratgeber, DE sitemap the inverse.
- Files: `frontend/src/lib/{ratgeber,udhezues,dictionaries}.ts`,
  `frontend/src/app/udhezues/**`, `frontend/src/app/sitemap.ts`,
  `frontend/src/components/{public-footer,public-shell}.tsx`.

## 2026-08-01 — Kosovo litigation cost calculator (D-047, B1)

- New: `XK_COURT_FEE_TABLE` + `XK_COST_RISK_INSTANCES` in
  `backend/app/seeds/kosovo.py` — court fees per UA Nr. 03/2025 of the
  KGJK (in force 2026-01-01), civil + commercial tracks, appeal and
  revision at 50%; sourcing caveat documented in D-047.
- New: `backend/app/services/xk_cost_risk.py` — per-instance cost risk
  (court fee + both lawyers per OAK tariff nr. 6/7 + 30% paushall +
  VAT 18), loser-pays per nenet 449/452 LPK; mirrors the DE cost_risk
  response shape.
- Changed: `POST /fee-calc/process-cost` resolves per tenant country
  (XK → xk_cost_risk, DE unchanged); `GET/POST /public/tools/process-cost`
  resolves per host and accepts `track` (civil|commercial) with
  localized track names in the meta response.
- New (frontend): public page `/kostoja` (XK host only, Albanian SEO
  metadata via layout, uses shared pkr* labels + new `kst*` keys ×7
  locales); cost-risk card on billing → invoices for XK offices; links
  in the public footer and tools dropdown (XK only); sitemap entry
  `only: XK`.
- Tests: `tests/test_xk_cost_risk.py` (11). Live: public XK POST/meta,
  DE POST unchanged, /kostoja 200.
- Files: `backend/app/seeds/kosovo.py`, `backend/app/services/xk_cost_risk.py`,
  `backend/app/api/{billing,public_tools}.py`, `frontend/src/app/kostoja/*`,
  `frontend/src/app/(app)/billing/page.tsx`, `frontend/src/components/
  {public-footer,public-shell}.tsx`, `frontend/src/app/sitemap.ts`,
  `frontend/src/lib/dictionaries.ts`, `backend/tests/test_xk_cost_risk.py`.

## 2026-08-01 — BRAV auto-verification for German lawyers (D-046, phase A)

- New: `backend/app/services/brav.py` — client for the official BRAV
  search (bravsearch.bea-brak.de, JSF/PrimeFaces, no API): browser-UA
  session + ViewState, partial-ajax POST, result-card/total parsing,
  every network failure degrades to None. German name normalization
  (umlauts, academic titles) + `de_names_match`.
- Changed: `services/license_verify.py` — DE branch now queries BRAV live
  and auto-approves ONLY a unique active Rechtsanwalt name match
  (truncated result lists never auto-approve); namesakes land in the
  operator queue with candidates in the note; portal down / no match
  keeps the old manual-search-link behavior. Shared approval tail
  extracted to `_approve_profile` (used by OAK/ONK email proof too).
- Changed: `POST /platform/verifications/{id}/decide` no longer requires
  `oak_license_no` when the jurisdiction registry is BRAV (it publishes
  no license numbers); `GET /platform/verifications` returns `chamber`
  (jurisdiction `bar_name`) and the /platform queue displays it instead
  of hardcoded "OAK".
- Tests: `tests/test_brav.py` (13, recorded fixtures in
  `tests/fixtures/brav_*.xml`) + `tests/test_brav_autoverify.py` (7).
- Files: `backend/app/services/{brav,license_verify}.py`,
  `backend/app/api/platform.py`, `frontend/src/app/(app)/platform/page.tsx`,
  `backend/tests/{test_brav,test_brav_autoverify}.py`, fixtures.

## 2026-08-01 — DE market pack: 0% positioning, RSV Deckung tracking, Ratgeber (D-045 F6)

- New (positioning): DE-host-only sections on /per-avokatet — "Festes Abo.
  0 % Provision pro Mandat." (careful wording, competitor not named) and a
  "Konform mit den BRAK-KI-Leitlinien" checklist (register, review gate,
  local indexing, Art. 30 template). 7 new `lpDe*` keys in all locales.
- New (RSV): `DE_INSURERS` seed (12 legal-expense insurers with service
  contacts, verify before production) + `INSURANCE_FOLLOWUP_DAYS=14`;
  `insurer_code`/`insurance_status`/`insurance_requested_at` on `Matter`
  (migration `3f644bf7eddb`); endpoints `GET /matters/{id}/deckung`,
  `POST .../deckung/anfrage` (renders `general.deckungsanfrage` into the
  matter as PDF via new shared helper `file_content_as_pdf`, sets status
  `angefragt`, audited), `POST .../deckung/status`. "Rechtsschutz-
  versicherung" card on the DE matter overview with a follow-up nudge
  after 14 unanswered days. 14 new `dkg*` keys (renamed from `rsv*` —
  collision with existing marketplace keys).
- New (content): 10 curated German consumer-law guides as static data
  (`frontend/src/lib/ratgeber.ts`) served at `/ratgeber` +
  `/ratgeber/[slug]` (server components, per-host canonical, Article
  JSON-LD, RDG-safe disclaimer, CTA → Ava/posto-rastin); DE-only sitemap
  entries; links in the public footer and tools dropdown.
- Tests: `tests/test_deckung.py` (3). Live smoke: anfrage → PDF filed +
  status angefragt → bestätigt; /ratgeber 200 / unknown slug 404.
- Files: `backend/app/{models,schemas}/matters.py`, `api/matters.py`,
  `api/templates.py`, `seeds/germany.py`, migration `3f644bf7eddb` (new),
  `tests/test_deckung.py` (new); `frontend/src/lib/{ratgeber.ts (new),
  dictionaries.ts,types.ts}`, `app/per-avokatet/page.tsx`,
  `app/ratgeber/**` (new), `app/sitemap.ts`, `(app)/matters/[id]/page.tsx`,
  `components/{public-footer,public-shell}.tsx`.

## 2026-08-01 — AI-generated documents: human-review gate + Art. 30 template (D-044 F5, part 2)

- New: `ai_generated`, `ai_reviewed_by_id`, `ai_reviewed_at` on
  `documents` (migration `01ed9e4e7fe8`). `render-to-matter` sets the flag
  when the draft went through AI-assist (the templates page tracks
  acceptance of the improved text and resets on a fresh render).
- New: `require_ai_review` gate — client-portal visibility
  (`POST /documents/{id}/visibility`) and signature requests
  (`POST /collab/matters/{id}/signatures`) return 400 for unreviewed
  AI-generated documents; `POST /documents/{id}/confirm-ai-review`
  records the reviewer + timestamp (audited `document.ai_review_confirm`).
- UI: "KI-Entwurf" stamp next to the filename in the matter Documents tab
  — violet with an inline confirm button while unreviewed, green check
  with review date after. 4 new `aig*` keys in all 7 locales.
- New: seeded DE office template `compliance.verarbeitungsverzeichnis` —
  a ready-to-fill Art. 30 DSGVO record of processing activities covering
  the platform's AI features, with embedded guidance (BRAK KI-Leitfaden).
- Tests: `tests/test_ai_review_gate.py` (3: plain passes, unreviewed AI
  blocked 400, reviewed AI passes).
- Files: `backend/app/models/documents.py`, `schemas/documents.py`,
  `api/{documents,templates,collab}.py`, `seeds/germany.py`, migration
  `01ed9e4e7fe8` (new), `tests/test_ai_review_gate.py` (new);
  `frontend/src/lib/{types,dictionaries}.ts`,
  `(app)/{matters/[id],templates}/page.tsx`.

## 2026-08-01 — KI-Nutzung register: per-office AI usage report + CSV (D-044 F5, part 1)

- New: `GET /firm/ai-usage?days=` (admin) — the office's own AI usage
  register per BRAK KI-Leitfaden / Art. 5 II DSGVO accountability, built
  from the append-only audit trail (actions `assistant.*`, `ai.*`,
  `template.ai_assist`, `deadline.bulk_create_ai`): totals, per-action
  counts with last-use, per-user counts, plus the tenant's effective LLM
  provider (jurisdiction override or default) with data-locality flag
  (local vs external API; embeddings always local per hard rule §5.7).
- New: `GET /firm/ai-usage.csv?days=` — full register as semicolon CSV
  (timestamp, user, action, entity, provider, locality), capped at 20k
  rows; the export itself is audit-logged (`firm.ai_usage_export`).
- UI: new admin card "KI-Nutzungsregister" in settings → security group:
  period picker (30/90/180/365 d), provider + locality summary, by-action
  and by-user breakdowns, CSV download. 13 new `kiu*` dictionary keys in
  all 7 locales.
- Live E2E: fresh DE office + document upload → background deadline scan
  logged `ai.deadline_suggest`, register shows total 1 with provider
  `deepseek`/external, CSV row matches.
- Files: `backend/app/api/firm.py`, `frontend/src/lib/dictionaries.ts`,
  `(app)/settings/page.tsx`.

## 2026-08-01 — Token-less email classification: sender→matter suggestions (D-043 F4, part 3)

- New: inbound mail without a plus-address token is no longer dropped —
  if the sender's address matches a `Contact`, the full raw message is
  stored encrypted and parked as an `EmailSuggestion` (migration
  `4eb4cfbac653`) pointing at the contact's best matter (open first, then
  most recently updated). Nothing is filed until the lawyer accepts.
- API (`api/email_suggestions.py`, new): `GET /email-suggestions`
  (pending, respects restricted visibility), `POST .../accept` (re-parses
  the stored message and files it exactly like a token-addressed email —
  note + attachments + deadline scan; audited), `POST .../dismiss`
  (deletes the parked raw message; audited).
- UI: dashboard card "E-Mails von bekannten Absendern" with per-item
  file-into-matter / dismiss buttons and a link to the suggested matter.
  6 new `ems*` dictionary keys in all 7 locales.
- Tests: `tests/test_email_suggest.py` (2: sender parsing/normalization,
  matter preference) — 175 total green. Live E2E: token-less German email
  from a known client → suggestion with correct matter, accept filed the
  note + attachment (category `email`), pending list emptied.
- Files: `backend/alembic/versions/20260801_4eb4cfbac653_*.py` (new),
  `models/matters.py`, `models/__init__.py`, `schemas/matters.py`,
  `services/email_ingest.py`, `api/email_suggestions.py` (new),
  `app/main.py`, `tests/test_email_suggest.py` (new),
  `frontend/src/lib/dictionaries.ts`, `(app)/dashboard/page.tsx`.

## 2026-08-01 — Mahnwesen: one-click dunning drafts on overdue invoices (D-043 F4, part 2)

- New: `Invoice.mahnung_level` (0–3) + `last_mahnung_at` (migration
  `c9054a36297b`). Endpoints `GET /invoices/{id}/mahnung/draft` (returns a
  ready-to-edit email in the client's locale: level 1 payment reminder /
  2 Mahnung / 3 final Mahnung, new payment deadline +14 days) and
  `POST .../mahnung/send` (sends the edited text with the invoice PDF —
  ZUGFeRD for DE — attached, bumps the level, audited as
  `invoice.mahnung`). Only sent+overdue invoices can be dunned; sending is
  always a human click (D-043 suggest→accept contract).
- i18n: 6 new backend email keys (`email_mahnung_subject/body_1..3`) in
  all 7 locales; German follows the Zahlungserinnerung → Mahnung → Letzte
  Mahnung convention with legal-steps wording only at level 3.
- UI (billing → invoices): red "{n} days overdue" marker, amber
  "Mahnstufe {n}" badge, dunning button on overdue invoices opening an
  inline editor (recipient, subject, body) with explicit send. 13 new
  `mhn*` dictionary keys in all 7 locales.
- Tests: `tests/test_mahnung.py` (4) — 173 total green. Live E2E: DE
  office → overdue invoice → draft rejected while `draft` status (400),
  correct German level-1 letter once sent, empty subject 422.
- Files: `backend/alembic/versions/20260801_c9054a36297b_*.py` (new),
  `models/billing.py`, `schemas/billing.py`, `api/billing.py`,
  `app/i18n.py`, `tests/test_mahnung.py` (new),
  `frontend/src/lib/types.ts`, `lib/dictionaries.ts`,
  `(app)/billing/page.tsx`.

## 2026-08-01 — AI deadline suggestions from document/email scans (D-043 F4, part 1)

- New: `DeadlineSuggestion` model + migration `1dd3e30e543f` — every
  document upload (and email attachment) with text is scanned in the
  background by the LLM (existing `EXTRACT_DEADLINES_PROMPT`, now asks
  for titles in the document's language); extracted deadlines are matched
  against `DeadlineRule` (legal-basis normalization + weighted title-token
  overlap) and stored as pending suggestions. Nothing is ever created
  without the lawyer clicking accept (suggest → human accept, D-043).
- API: `GET /deadline-suggestions` (office-wide) +
  `GET /matters/{id}/deadline-suggestions`, `POST .../accept` (rule-based
  via engine when matched + trigger date, else direct date; audited),
  `POST .../dismiss`. Accepting stores the created `deadline_id` on the
  suggestion; duplicate scans are skipped per document.
- UI: amber suggestions banner in the matter Deadlines tab (accept /
  dismiss per item, shows rule + § + confidence) and a dashboard card
  listing pending suggestions across matters. 12 new `dls*` dictionary
  keys in all 7 locales.
- Tests: `tests/test_deadline_suggest.py` (13: rule matching, date
  parsing) — 169 total green. Live E2E: German Urteil upload → 3
  suggestions (Berufungsfrist matched to rule, § 517 ZPO), accept
  created the deadline 2026-08-28 from Zustellung 28.07, dismiss OK.
- Files: `backend/alembic/versions/20260801_1dd3e30e543f_*.py` (new),
  `models/matters.py`, `schemas/matters.py`,
  `services/deadline_suggest.py` (new), `services/assistant.py`,
  `services/email_ingest.py`, `api/documents.py`, `api/deadlines.py`,
  `tests/test_deadline_suggest.py` (new), `frontend/src/app/(app)/
  matters/[id]/page.tsx`, `(app)/dashboard/page.tsx`,
  `lib/dictionaries.ts`; `models/jurisdiction.py` (GIN index moved into
  model `__table_args__` so autogenerate stops fighting it).

## 2026-08-01 — Deep research: hybrid retrieval + federal case law with Aktenzeichen (D-042 F3)

- New: hybrid corpus retrieval. Migration `d858e0f31af4` adds
  `legal_corpus_chunks.tsv` (tsvector, `german` config for de / `simple`
  otherwise, full backfill) + GIN index. `search_corpus` now fuses three
  rankings with RRF (k=60): pgvector cosine, `plainto_tsquery` AND, and a
  rare-word OR leg (up to 4 query words with document frequency ≤ 2%,
  prefix-matched so "Berufung" finds "Berufungsfrist"); judgments capped
  at limit//3 of the final slots. Corpus splitter also chunks judgments by
  Leitsatz/Tenor/Gründe headings.
- New: `scripts/import_de_rechtsprechung.py` — BGH/BAG/BVerfG decisions of
  the last 5 years from rechtsprechung-im-internet.de (BMJV, § 5 UrhG),
  `doc_type="judgment"`, reference = Aktenzeichen, resumable, retries
  across backend restarts. Ava (lawyer + public) cites judgments with
  court + Aktenzeichen; DE public prompt now covers case law.
- Fix: lawyer-side assistant calls never passed `region`, so Landesrecht
  was invisible in ask/deep-research/prepare/hearing-prep — added
  `_office_region` and threaded the parameter through.
- Eval: `scripts/eval_de_recherche.py` — natural-language §-recall 9/14
  (= vector baseline), explicit §-citation queries 1/6 → 5/6.
- Files: `backend/alembic/versions/20260801_d858e0f31af4_*.py` (new),
  `models/jurisdiction.py`, `api/corpus.py`, `services/rag.py`,
  `services/assistant.py`, `api/assistant.py`, `api/marketplace.py`,
  `scripts/import_de_rechtsprechung.py` (new),
  `scripts/eval_de_recherche.py` (new), `tests/test_rag_chunking.py`,
  `frontend/src/app/ava/page.tsx`, `(app)/assistant/page.tsx`.

## 2026-08-01 — Online-Verfahren assistant: eligibility, Klageschrift, citizen pointer (D-041 F2)

- New: support for Germany's civil online procedure (live 2026-04-15).
  Seeds: `DE_OV_COURTS` (18 pilot courts, scope payment/flight, go-live
  dates) + templates `civil.ov_klageschrift` / `civil.ov_fluggastrechte`.
  Service `online_verfahren.py`: eligibility (≤ 10,000 €, pilot-court
  match, flight-case detection), reduced-fee comparison (2.0 vs 3.0),
  structured `avokatim.ov-export/v1` JSON as XJustiz groundwork.
- API: `GET /matters/{id}/online-verfahren` + `/ov-export` (DE matters
  only, audited). Lawyer UI: "Online-Verfahren prüfen" in the matter AI
  tab — checks, fee saving, .docx Klageschrift download, JSON export.
  Citizen UI (RDG-safe, information only): pointer card to
  service.justiz.de on /posto-rastin and Ava DE when the case matches
  (`lib/ov.ts`). 20 new `ov*` dictionary keys in all 7 locales.
- Tests: `tests/test_online_verfahren.py` (6) — 156 total green; live E2E
  check against a fresh DE office (court match, fees, template, export).
- Files: `backend/app/seeds/germany.py`, `backend/app/services/
  online_verfahren.py` (new), `api/matters.py`, `tests/
  test_online_verfahren.py` (new), `frontend/src/lib/ov.ts` (new),
  `matters/[id]/page.tsx`, `posto-rastin/page.tsx`, `ava/page.tsx`,
  `lib/dictionaries.ts`.

## 2026-08-01 — Prozesskostenrechner: GKG court fees + litigation cost risk (D-040 F1)

- New: full German litigation cost-risk calculator on top of the existing
  RVG engine. `DE_GKG_TABLE` (§ 34 GKG / Anlage 2, KostBRÄG 2025) +
  `DE_PROZESSKOSTEN_INSTANCES` as seeds; `services/prozesskosten.py`
  computes per instance (1st, appeal, BGH revision): court fee, own +
  opponent lawyer (statutory RVG, VAT), loser-pays total (§ 91 ZPO),
  cumulative risk and the § 12 GKG filing advance.
- API: `GET/POST /public/tools/process-cost` (DE host only, rate-limited)
  and `POST /billing/fee-calc/process-cost` for offices. UI: new
  "Prozesskostenrisiko" section on `/rvg` with per-instance cards; 12 new
  `pkr*` dictionary keys in all 7 locales; /rvg SEO metadata extended.
- Tests: `tests/test_prozesskosten.py` with official reference values
  (5,000 € → unit 170.50 / KV 1210 511.50; 3-instance risk 9,866.56).
- Files: `backend/app/seeds/germany.py`, `backend/app/services/
  prozesskosten.py` (new), `services/rvg.py` (banded_fee), `api/
  public_tools.py`, `api/billing.py`, `frontend/src/app/rvg/page.tsx`,
  `rvg/layout.tsx`, `lib/dictionaries.ts`.

## 2026-08-01 — Full mobile web audit (DE first, then XK) + per-host SEO (D-039)

- Audited both hosts on a real mobile viewport (Playwright, iPhone 14):
  DE public (16 pages), DE lawyer app (12 pages, logged in through the UI),
  XK public + citizen (17 pages). Automated checks: horizontal overflow,
  tap targets < 24 px, fonts < 11 px, viewport meta, console errors.
- Fixed critical: `/ava` hard-crashed on browsers without
  `crypto.randomUUID` (iOS < 15.4, old WebViews) — hex fallback in
  `app/ava/page.tsx`. DE host served Albanian `<html lang>`, titles,
  JSON-LD, sitemap and even XK lawyers in the directory ItemList — new
  `lib/seo.ts` (`serverCountry()`), root + 7 public layouts, `sitemap.ts`,
  `robots.ts` now resolve per host; server-side JSON-LD/sitemap fetches
  pass the country header. Removed dead `/apliko` from the sitemap.
- Fixed UX: `/platform` showed an endless spinner on 403; tap targets
  enlarged (footer, PageIntro, RVG/consent checkboxes, dashboard links,
  settings buttons, citizen auth links, email-verification banner); DE
  bottom-nav label "Einstellen" → "Fall posten".
- Ops root-cause: a stale `next-server` over a new build (404 chunks) came
  from restarting `avokatim` instead of `avokatim-frontend` after builds.
- Files: `frontend/src/lib/seo.ts` (new), `app/layout.tsx`, 7 public
  layouts, `sitemap.ts`, `robots.ts`, `app/ava/page.tsx`,
  `app/(app)/platform/page.tsx`, tap-target touch-ups across public/app
  pages, `lib/dictionaries.ts` (pnPost de).

## 2026-08-01 — Investor presentation for the German market (docs/pitch)

- New `docs/pitch/prezantimi-investitori-gjermani.md`: full Albanian
  investor letter for a lawyer-investor — market moment (E-Rechnung
  2027/28, beA, AI wave), product overview, honest comparison table vs
  RA-MICRO/AnNoText/Actaport (beA named as the one open gap), privacy &
  compliance section with the local LLM framed as "in preparation"
  (validated, activated before public launch), status, and a 4-point
  partnership proposal (legal review, EU infra, beA process, pilot
  offices). No prices anywhere, per owner instruction (also noted in the
  self-notes section).

## 2026-08-01 — Multilingual voice (D-038): stock Whisper for non-sq STT, Piper voices in 6 languages

- Measured German quality of the Albanian Whisper fine-tune with real
  German audio (Piper thorsten voice as test signal): unusable —
  "Kündigung"→"kindikung", a § 195 BGB sentence came out as gibberish.
  Stock `large-v3-turbo` on the same clips: near-perfect legal German in
  0.14–0.47 s on CUDA.
- STT now routes by language (`services/voice.py`): sq → fine-tune,
  everything else → stock turbo (`voice_stt_fallback_model` finally
  implemented, cache `data/models/whisper-cache`, ~1.6 GB VRAM each).
- Server TTS beyond Albanian: Piper voices de/en/tr/sr/zh in
  `data/models/piper-voices/{lang}.onnx` (rhasspy/piper-voices;
  de=thorsten). `POST /voice/tts` takes `language`; `/voice/status`
  returns `tts_langs`; `voice.ts` uses server TTS when the locale is
  listed, browser speechSynthesis otherwise (bs). New language = drop in
  an .onnx, no code.
- Tests: German TTS→STT roundtrip + tts_languages test; Albanian roundtrip
  assertion made robust to CUDA decode wobble. 152 green ×3 runs; tsc +
  build clean. Live: German STT 0.27 s warm via API, German WAV 1.3 s.

## 2026-08-01 — Ava voice audit: STT on CUDA, German whitelist, lawyer tier; DE demo on DeepSeek

- Full audit of the voice pipeline (mic → `/api/public/voice/transcribe`
  faster-whisper → Ava LLM → Piper sq / browser speechSynthesis). Fixes:
  - STT now loads on **CUDA float16** when available
    (`voice_stt_device="auto"` in config, CPU int8 fallback) — warm
    transcription of a 4.6 s clip dropped from ~9.6 s to ~0.3 s on the
    RTX 5090. Verified live on the running server (log: "on CUDA").
  - `de` added to `_WHISPER_LANGS` — German UI locale was silently ignored
    and decode fell back to auto-detect; now honored (verified via API).
  - Voice endpoints now recognize the **staff JWT** for rate-limit tiering
    (`_staff_sub` in `api/voice.py`): logged-in lawyers get 60 STT /
    120 TTS per hour instead of the anonymous 10/20 per IP; `voice.ts`
    sends the citizen or lawyer token, whichever exists.
  - Browser TTS language map gets `de` → `de-DE`.
  - Audit findings left as-is (documented): push-to-talk only (no duplex),
    `voice_stt_fallback_model` setting unused, Piper TTS sq-only by design,
    one STT at a time (`_stt_lock`), `vUnavailable` i18n key unused.
- **DE temporarily on DeepSeek** (owner request, full-feature demo):
  `PROFILES["DE"].llm_provider = None`. gemma3:27b stays installed and
  validated; launch gate item 3 reverted to "ready but pending flip" —
  must return to `"local"` before public launch. Verified live: DE Ava
  answers § 4 KSchG via api.deepseek.com.
- Tests: whitelist test updated; suite 150 green; tsc + build clean.

## 2026-08-01 — beA/KSW registration prepared (D-037 phase 6) + D-037 docs

- New `docs/legal/BEA-KSW-REGISTRATION.md`: what the KSW-Schnittstelle is
  (SOAP webservice + Java toolkit, access after "berechtigtes Interesse"
  review + registration, SSL client auth with beA-Betrieb), contacts
  (servicedesk@beasupport.de, portal.beasupport.de, BRAK Berlin), owner
  steps, and a ready-to-send German registration email. Planned module
  architecture: Java sidecar wrapping the official KSW-Toolkit + Python
  `services/bea/` — development starts once BRAK grants test access.
- D-037 recorded in DECISIONS (agents), JOURNAL entry 2026-08-01f, STATE
  and ROADMAP updated (market-gap item closed, beA + GKG split out,
  stale "no GPU/Ollama" watch item corrected).

## 2026-08-01 — DE launch gate: local LLM + full E2E test (D-037 phase 5)

- `PROFILES["DE"].llm_provider = "local"` — Ava DE and all German LLM calls
  now run on Ollama locally (`LOCAL_LLM_MODEL=gemma3:27b` in backend/.env),
  so no German citizen data leaves the machine. Model chosen after a
  RAG-grounded German-quality shootout vs qwen3:14b (qwen3 burned its token
  budget on "thinking" and returned empty answers through the OpenAI-compat
  endpoint; gemma3:27b fits the RTX 5090 at 17.5 GB VRAM, ~50 tok/s, cites
  provided norms correctly). Verified live: § 573c BGB answer via
  /public/ava/ask on the DE host, backend log shows 127.0.0.1:11434.
- New `backend/scripts/de_simulation.py`: 15-check E2E of all D-037 features
  on the DE host — office signup + fiscal config (IBAN, DATEV accounts), RVG
  calc, ZUGFeRD hybrid PDF + XML download, invoice sent/paid, DATEV EXTF
  export, Deckungsanfrage template, citizen case with Rechtsschutz, lawyer
  sees the insurance badge. All pass.
- Regression: full_simulation XK 187 PASS / 0 FAIL, pytest 150 green.
- DE-LAUNCH-GATE.md updated: gate item 3 (EU LLM provider) closed; remaining
  gate items are operational/owner-side (EU server, Art. 27 rep, German
  lawyer review of legal texts, VAT before first real invoice).

## 2026-08-01 — DATEV EXTF export (D-037 phase 4)

- New `services/datev.py`: EXTF Buchungsstapel CSV (header 700 / format v13,
  cp1252 + CRLF, decimal comma) built from two booking types per period —
  issued invoices (debtor an Erlöskonto, gross) and payments (bank 1200 an
  debtor). SKR03 defaults 8400/10000, no BU-Schlüssel (Automatikkonto).
- New router `api/exports.py`: `GET /api/export/datev?date_from&date_to`
  (DE offices only, audited). Tenant config columns
  `datev_consultant_no/client_no/revenue_account/debtor_account`
  (migration 39eb3d97a67c) editable in settings (DE block).
- Frontend: DATEV card on the billing invoices tab (period + download);
  9 new datev* keys in 7 locales. 2 new tests; suite 149 green, tsc clean.

## 2026-08-01 — Rechtsschutzversicherung in the case flow (D-037 phase 3)

- `CaseRequest.has_legal_insurance` + `insurer_name` (migration f13891b21e80);
  accepted on `POST /citizen/cases`, returned by `_case_out` to both citizen
  and lawyer views.
- /posto-rastin asks the question on the DE host (yes/no + insurer, optional);
  Ava DE now casually asks about Rechtsschutz when someone wants a lawyer, and
  /ava/structure-case extracts `has_legal_insurance`/`insurer_name` from the
  conversation into the case draft (prefills the form via localStorage).
- Lawyer marketplace card shows a "Rechtsschutz vorhanden · <insurer>" badge
  (Advocado-style conversion signal). New lawyer template
  `general.deckungsanfrage` (coverage inquiry letter) in DE_TEMPLATES.
- 6 new rsv* keys in 7 locales. Suite 147 green + tsc clean; template seeded
  and verified live after restart.

## 2026-08-01 — E-Rechnung: ZUGFeRD/Factur-X hybrid invoices (D-037 phase 2)

- New `services/einvoice.py` (drafthorse): EN 16931 CII XML from the invoice
  (seller USt-IdNr/Steuernummer, SEPA IBAN payment means, per-line VAT,
  German "Straße, PLZ Stadt" address splitting) + PDF embedding.
- Every invoice PDF of a DE office is now a hybrid e-invoice: WeasyPrint
  renders PDF/A-3b (`pdf_variant`) and the XML is attached (both the /pdf
  endpoint and the send-to-client email). New `GET /invoices/{id}/e-invoice.xml`
  returns the raw XML for B2G/XRechnung recipients.
- `Tenant.iban` (new column + migration 73a50f24e105) editable in settings
  (DE offices); `bank_details` stays the free-text print line. Frontend:
  IBAN field + "E-Rechnung (XML)" download button; 3 new keys in 7 locales.
- Validated one-off with Mustangproject CLI: XML = valid EN 16931, hybrid
  PDF = PDF/A-3b compliant, overall "valid". 2 new tests (XML structure,
  Factur-X embedding); suite 148 green.

## 2026-08-01 — Full RVG fee engine (D-037 phase 1)

- § 13 Abs. 1 RVG table (KostBRÄG 2025) as band data + 5 rate-based VV items
  in `seeds/germany.py`; new `services/rvg.py` computes fee lines (kaufmännisch
  rounding, § 13 Abs. 2 minimum, Anrechnung Vorbem. 3 Abs. 4 VV capped at
  0.75, VV 7002 pauschale per Angelegenheit, VAT).
- API: `GET/POST /api/fee-calc/rvg` (DE offices) + public
  `GET /public/tools/fee-items`, `POST /public/tools/fee-calc` (DE host,
  rate-limited). Corrected the three 5.000-€ tariff anchors (old values used
  372 € as 1.0 fee; official 2025 table says 354,50 €) and taught the seeder
  to sync tariff amounts/notes from seeds.
- Frontend: RVG panel in billing (computes lines straight into invoice items;
  invoice item filter now accepts negative Anrechnung lines) + public
  `/rvg` page ("Was kostet ein Anwalt?") linked in tools nav/footer/sitemap
  on the DE host; 15 new rvg* keys in 7 locales.
- Verified: 7 new tests in `tests/test_rvg.py` against the published table
  (146/146 total), tsc clean, live calc on de host returns 460,85/460,85/
  425,40/-230,43 + 2x pauschale for 5.000 € — matches reference calculators.

## 2026-08-01 — Exact calendar-month deadline math (D-036)

- Industry comparison vs the German market (RA-MICRO/Actaport, Advocado,
  beA/E-Rechnung mandates) → new ROADMAP items; the top-risk gap fixed now:
  German month deadlines were 30/60-day approximations.
- `day_type="months"` in the deadline engine: `add_months()` per §§ 187–188
  BGB (same day number in the target month, else last day; § 222 (2) ZPO
  weekend/holiday extension incl. Land holidays already handled). 6 DE rules
  converted (ZPO 517/520, VwGO 70/74, SGG 84, AO 355); seeder now syncs
  rule substance (days/day_type/legal_basis/notes/trigger_event) from seeds
  so existing DBs convert at startup. Frontend shows months (dcMonths* keys
  in 7 locales, /afatet + matter deadline picker).
- Verified: pytest 139/139 (5 new month-math tests), tsc clean, build +
  restart + live /afatet calc OK.
- Files: `backend/app/services/deadlines.py`,
  `backend/app/models/jurisdiction.py`, `backend/app/seeds/{__init__,germany}.py`,
  `backend/tests/test_deadline_engine.py`, `frontend/src/lib/dictionaries.ts`,
  `frontend/src/app/afatet/page.tsx`,
  `frontend/src/app/(app)/matters/[id]/page.tsx`; D-036 in DECISIONS,
  JOURNAL 2026-08-01e.

## 2026-08-01 — Landesrecht (D-035) phase 5: tests + docs; remaining Länder blocked

- 7 new tests in `tests/test_regions.py` (Länder registry, city prefill,
  Land holiday rows, Buß- und Bettag math, AvaAskIn.region) — 135/135 pass.
- BW/BE portals probed: juris SPAs with token-authenticated API → curl
  adapters impossible; recorded as LESSONS #1 + ROADMAP rollout item
  (headless browser or juris agreement). Pilot stays NRW+BY (~30M).
- D-035 in DECISIONS; JOURNAL 2026-08-01d; STATE (corpus 99 acts, region
  dimension); ROADMAP updated.

## 2026-08-01 — Landesrecht (D-035) phase 4: region-aware retrieval + Ava

- `search_corpus` takes `region`: federal docs (region IS NULL) always,
  the given Land's docs on top; no region → federal only (lawyer assistant
  unchanged/safe). Hits and citations now carry `region`.
- Public Ava: `AvaAskIn.region` (validated against the profile registry),
  Landesrecht context labels show the Land ("NachbG NRW, § 15
  [Nordrhein-Westfalen]"); DE prompt updated — NRW+BY Landesrecht now in
  scope, other Länder explicitly declared as not yet covered.
- DE Ava page: "Bundesland (optional)" dropdown (localStorage-persisted,
  `avaRegionLabel` in 7 locales), sent with each question.
- Verified live: NW question → NachbG NRW citations; BY → AGBGB Bayern +
  BGB; no region → BGB only; XK Ava unaffected.

## 2026-08-01 — Landesrecht (D-035) phases 1–3: region schema, Land holidays, NRW+BY corpus

- New `region` dimension (Bundesland codes, NULL = nation-wide/federal):
  columns on `Holiday` (unique now `(jurisdiction_id, day, region)` NULLS NOT
  DISTINCT), `LegalCorpusDoc`, `Tenant`; Alembic `cb917eb4a318`. DE profile
  in `jurisdictions.py` gains the 16-Länder registry + city→Land prefill map
  (`region_for_city`); `POST /corpus` accepts validated `region`.
- Land holidays 2026–27 seeded per Land (Heilige Drei Könige, Fronleichnam,
  Allerheiligen, Reformationstag, Mariä Himmelfahrt SL, Frauentag BE/MV,
  Buß- und Bettag SN, Weltkindertag TH) — whole-Land holidays only,
  conservative for deadline math. `_holiday_set`/`compute_due_date` take
  `region`; matter deadlines use `tenant.region`, public calculator accepts
  optional `region`. Settings shows a Bundesland picker for DE offices
  (`firmRegion` in all 7 locales); first saved profile city prefills it.
- New `scripts/import_de_landesrecht.py`: portal-adapter architecture —
  NRW (recht.nrw.de lrgv pages, § blocks from `field--field_num`/
  `field--name-field-text`) and Bayern (gesetze-bayern.de
  `/Content/Document/{slug}/true`, `paraheading` blocks). 20 curated acts
  imported (10 per Land: Polizei, Bauordnung, Schule, Nachbarrecht, Kita,
  Ladenöffnung, Feiertage, Datenschutz, Gemeindeordnung, Presse), ~2,900
  chunks tagged with their region.
- Verified: regional deadline test (Allerheiligen 2027-11-01: NW extends to
  11-02, NI stays 11-01); clean chunk text on both portals.

## 2026-08-01 — DE corpus wave 2: +20 citizen-topic acts + DSGVO, Ava language fix

- `import_de_laws.py`: 20 new federal acts for high-frequency citizen topics
  (BEEG, MuSchG, GewSchG, UhVorschG, BerHG, GKG, FamGKG, UWG, SGB IV/VII/
  VIII/IX/X, WoGG, BAföG, BBiG, NachwG, PflVG, FeV, ZVG); corrected slugs
  (`berathig`, `baf_g`, full `sgb_10` instead of chapter stubs).
- New `scripts/import_dsgvo.py`: German GDPR from the EU Publications
  Office CELLAR API (EUR-Lex portal blocks bots with empty 202), XHTML →
  "Artikel N" blocks, 99 articles, sanity gate before posting.
  DE corpus total: 79 acts / 16,435 chunks.
- DE Ava: RAG context framing now German on the DE host (Albanian labels
  were pulling whole answers into Albanian); prompt discloses the corpus
  boundary — federal law + DSGVO, no Landesrecht/case law.
- Files: `backend/scripts/import_de_laws.py`, `backend/scripts/
  import_dsgvo.py` (new), `backend/app/api/marketplace.py`.
- Verified: pytest 128/128; live DE Ava: Beratungshilfe question answered
  in German citing § 44 RVG; stats endpoint shows 79 laws.

## 2026-08-01 — Germany expansion (D-034), phases 1–4: locale, data, Ava, legal

- German locale end-to-end: `de` added to `Locale` + ~1,130 translated keys in
  `frontend/src/lib/dictionaries.ts`, per-country language menu
  (`COUNTRY_LOCALES`: DE shows de/en/tr), host-aware default locale in
  `i18n.tsx`; full `_DE` catalog in `backend/app/i18n.py` (emails/SMS) and
  `de` in `supported_locales`.
- Public pages host-aware: landing, per-qytetaret, rasti-im, onboarding,
  settings, public shell + footer adapt copy/cities/languages for DE; SOS and
  notary hidden on the DE host and blocked server-side (signup 400, SOS 403).
- German legal data: `backend/app/seeds/germany.py` — DE jurisdiction active,
  9 federal holidays (2026–2027), 12 deadline rules (ZPO §§ 517/520/339,
  Mahnbescheid, KSchG § 4, StPO §§ 314/341, VwGO, ArbGG), RVG starter
  tariff, 6 citizen document templates. `backend/scripts/import_de_laws.py`
  imports federal laws from gesetze-im-internet.de (XML, public domain):
  58 laws / 14,443 § chunks loaded with local embeddings. RAG fallback
  language now resolves from the jurisdiction profile (`rag.py`).
- DE Ava: Rechtsinformation-only system prompt (RDG § 2 boundary, EU AI Act
  Art. 50 "you are talking to an AI" disclosure, § citations, lawyer
  recommendation); LLM provider selectable per jurisdiction profile through
  the existing router. German VAT (19%) set on DE signups.
- German lawyers: BRAV registry has no emails → no auto-verify; signup
  notifies ops with a prefilled BRAV search link for one-click approval
  (`license_verify.py`); procedure added to Halim's AVOKATIM-OPS.md.
- Legal: German AGB + Datenschutzerklärung (`legal.ts`), static `/impressum`
  page (§ 5 DDG, address placeholders); `docs/legal/DE-LAUNCH-GATE.md`
  documents the four conditions before public German promotion (EU server,
  GDPR Art. 27 representative, EU LLM, German-lawyer text review).
- Files: `backend/app/{i18n,config}.py`, `backend/app/api/{auth,marketplace,
  public_tools}.py`, `backend/app/seeds/{__init__,germany}.py`,
  `backend/app/services/{rag,license_verify}.py`,
  `backend/scripts/import_de_laws.py` (new), `frontend/src/lib/
  {dictionaries,i18n,legal,country}.ts*`, `frontend/src/app/{page,
  per-qytetaret,rasti-im,onboarding,regjistrohu,impressum,(app)/settings}`,
  `frontend/src/components/{public-shell,public-footer,ui}.tsx`,
  `docs/legal/DE-LAUNCH-GATE.md` (new).
- Verified: pytest 128/128, tsc clean, build 44 pages, both hosts 200,
  DE stats show the German corpus, live German Ava answer correct
  (Kündigungsschutzklage → 3 Wochen, § 4 KSchG, German citations).

## 2026-08-01 — Germany expansion (D-034), phase 0: country scoping

- One codebase, two countries: new `app/jurisdictions.py` (declarative
  per-country profiles XK/DE — currency, VAT, timezone, locales, registry,
  feature switches, host mapping), `country` columns on tenants /
  citizen_users / case_requests (Alembic bc70e34d10f2, default XK),
  host→country resolution (`de.avokatiim.ai` → DE) in proxy.ts
  (x-avokatim-country header) + `country_from_request` on all public
  endpoints. Signup (lawyer + citizen + OAuth state) records the country;
  directory, stats, case posting/browsing/claiming, match/SOS alerts and the
  public deadline calculator are country-scoped. XK hardcodes removed:
  intake/imports/matters use the tenant's jurisdiction, templates/fee-tariff/
  corpus lists default to it, matter page fetches rules via new
  `/matters/{id}/deadline-rules`. Public Ava picks the corpus + system prompt
  per country (German prompt is RDG-§2-safe with AI-Act Art. 50 disclosure).
  Corpus splitter now recognizes German `§`/`Artikel` markers. Tunnel +
  Cloudflare DNS for de.avokatiim.ai are live.
- Files: `backend/app/jurisdictions.py` (new), `backend/app/models/
  {tenancy,marketplace}.py`, `backend/app/api/{auth,marketplace,
  oauth_citizen,intake,imports,matters,deadlines,templates,billing,corpus,
  public_tools}.py`, `backend/app/schemas/matters.py`, 1 Alembic revision,
  `frontend/src/proxy.ts`, `frontend/src/lib/country.ts` (new),
  `frontend/src/app/(app)/matters/[id]/page.tsx`, `~/.cloudflared/config.yml`.
- Verified: pytest 128/128, imports OK, https://de.avokatiim.ai returns 200.

## 2026-08-01 — Housekeeping: LiveKit 7881 → localhost, visibility-nudge script

- LiveKit's TCP-ICE fallback port 7881 now binds to 127.0.0.1 only (LAN media
  uses 7882/udp) — closes an unnecessary LAN-exposed port, D-033 spirit.
- Committed the one-shot `backend/scripts/send_visibility_nudge.py` used on
  07-31 to ask the two newly verified lawyers to publish their profiles
  (already sent; kept for the record, noted in `docs/agents/COMMS.md`).
- Files: `docker-compose.yml`, `backend/scripts/send_visibility_nudge.py`.

## 2026-07-31 — Fully automatic lawyer/notary verification (email = proof)

- Owner's call: if the system finds the lawyer in the OAK registry, no extra
  step may be required. `try_auto_verify` no longer demands a typed license
  number or an existing profile row — a confirmed email that matches the
  chamber registry verifies on the spot (profile auto-created invisible if
  onboarding wasn't opened). Changing the license number later no longer
  resets an email-anchored verification (no badge flapping / repeat emails).
  License field copy across 6 languages now says "optional". Backfill
  verified 3 real lawyers instantly: Adnan Pacolli (now live in the
  directory — 7 total), Betim Sijarina, Marigona Gashi (verified, awaiting
  their own publish). Manual review remains only for no-match cases.
- Files: `backend/app/services/license_verify.py`,
  `backend/app/api/marketplace.py`, `frontend/src/lib/dictionaries.ts`.

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
