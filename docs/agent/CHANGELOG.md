# CHANGELOG — dated trail of changes (newest on top)

> One entry per finished piece of work. Never optional (Definition of Done).
> Format: date, what changed, why, files touched.

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
