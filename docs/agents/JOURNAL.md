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

## 2026-07-13 — "Jam noter": notaries become the second paying profession (Cursor / Fable 5)

- Done (plan "Jam noter", all 6 todos; decision D-024):
  - `Tenant.profession` (lawyer|notary, migration `d4761aba9c68`); signup
    with "Jam avokat / Jam noter" cards (`?profesioni=noter` preselects);
    notary welcome email ×6 (`notary_welcome_*`); `/auth/me` returns
    `tenant_profession`.
  - Conditional app: marketplace nav hidden for notaries, notary tagline,
    settings/onboarding show ONK license (no OAK, no SOS, no practice
    areas, no consult fee, no referral), "Përgjegjësi" label in matters.
    Claim endpoint 403 for notary tenants; excluded from /public/lawyers,
    matching alerts and public stats.
  - `/per-noteret` marketing page ×6 (violet), linked from `/` (umbFnL9)
    and a CTA banner on `/noteret`.
  - Verification: platform queue shows profession badge (ONK/OAK) and an
    automatic registry match (`_onk_match`: email, then normalized name
    against `data/notaries.json`); founder badge stays lawyer-only.
  - Adapted market: `/public/tools/notaries` merges registered verified
    notary offices (listed equally, deduped from the scraped registry)
    with a booking widget on /noteret; the citizen attaches a prepared
    dossier (PDF ≤2 MB) to the booking (migration `c24b4c54ac8f`), the
    notary downloads it (`GET /marketplace/bookings/{id}/attachment`) and
    confirms from a shared BookingsPanel now also on the dashboard.
- Verified: pytest 83/83 (new `test_profession.py`);
  `scripts/notary_simulation.py` 16/16 (signup → profile → verify →
  /noteret listing → 403 claim guard → citizen books with PDF dossier →
  notary downloads + confirms → Ava answers a notary tariff question);
  `full_simulation.py` 187 PASS / 1 stale check (template category list
  missing "noteria" — fixed in the script); frontend build OK, health OK.
- Left open / next: notary-specific matter templates in the app,
  art. 50 registers on ONK interest, rename of `LawyerProfile` if a third
  profession ever lands.

## 2026-07-13 — Notary surfaced as the visible third pillar (Cursor / Fable 5)

- Context: after building /noteret, the owner asked where notary services
  belong in the UI — integrated or separate. Industry pattern (Rocket
  Lawyer, LegalZoom, Proof): service verticals under one brand with a
  dedicated landing, surfaced in main nav and contextual flows — never a
  separate site. Decision: integrated, elevated from the hidden "Vegla"
  dropdown to a first-class pillar.
- Done:
  - Desktop header: "Noterët" is now a top-level nav link right after
    "Avokatët" (chain reads Ava · Avokatët · Noterët · Posto · Rasti im);
    removed from the Vegla dropdown. Mobile bottom nav intentionally
    unchanged (4 core actions + SOS).
  - Footer citizen column: /noteret link added.
  - Umbrella landing `/`: new citizen function bullet `umbFnC8` (find the
    notary, know the fee, arrive prepared), placed after the directory line.
  - `/per-qytetaret`: fifth story section "Edhe kur të duhet noteri"
    (violet tone) with CTA to /noteret and a "notary pack" link to
    /dokumentet.
  - Ava page: fifth example chip "Çfarë më duhet për ta shitur banesën te
    noteri?" (avaEx5) — Ava already routes these to /noteret.
  - Strings ×6 (umbFnC8, avaEx5, landNotary*); sw cache → v17.
- Verified: build OK, all four pages 200 and render the new content
  (checked server-rendered HTML for the section title and the C8 bullet).

## 2026-07-13 — Notary integration: third bridge citizen → lawyer → notary (Cursor / Fable 5)

- Done (plan "Integrimi i noterisë", phases 1+2+3):
  - **Corpus**: Law 06/L-010 on Notary (80 chunks, GZK ActID 18334) and
    amendment 08/L-149 (4 chunks, MoJ PDF mirror — GZK page has no inline
    text) indexed via `import_gzk.py` (now supports per-law `min_chars` and
    PDF candidates). Amendment 08/L-272 (e-signature arts. 31A/31B) has NO
    machine-readable text online (empty GZK span, gazette PDF behind ASP.NET
    postback, Assembly site behind Cloudflare) — noted in the script, retry
    later.
  - **Directory**: `scripts/scrape_onk_registry.py` scrapes
    noteria-ks.org/noteret (141 notaries, all 141 Cloudflare-obfuscated
    emails decoded) → `data/notaries.json` (git-ignored, like the OAK
    registry). Served by `GET /public/tools/notaries?city=` (mtime-cached).
  - **Tariffs**: AI 02/2012 on provisional notary fees (found on ONK site)
    seeded as data in `backend/app/seeds/notary.py`: Annex-1 value brackets,
    +20€/20k over 100k capped at 1000€ (art. 21.2), 80% solemnization factor
    (art. 23), fixed fees (testament 50€, PoA 20€, founding act 100€,
    signature/copy 1€). `POST /public/tools/notary-fee` estimates.
  - **Public page `/noteret`** (×6 locales): act picker → act-type badge
    (akt/solemnizim/vërtetim), fee estimate, document checklist ("bring with
    you"), directory with city filter (38 cities), physical-presence
    disclaimer. Linked from the Vegla dropdown in the public shell.
  - **Notary pack at `/dokumentet`**: 4 new templates in category "noteria"
    (vehicle sale contract, power of attorney, spousal property agreement
    draft, inheritance-opening request), each flagged `requires_notary` —
    amber banner + link to /noteret in the picker and the form; PDF bodies
    carry a VËREJTJE that notarization is required.
  - **Ava public prompt** now distinguishes notary matters (property sales,
    wills, inheritance, PoA, spousal agreements per art. 41), explains which
    act type is needed and points to /noteret. Live-tested: apartment-sale
    question correctly answered "needs a notary" with law citations and the
    /noteret link.
  - **Docs**: `docs/rekrutimi/kontakt-onk.md` (draft ONK partnership email,
    owner sends when ready) and `docs/integrimet/e-noteria.md` (remote
    notarization readiness: legal gap analysis, Estonian/US RON models, why
    our LiveKit + evidence-vault + hash-chain stack is the ready
    infrastructure).
- Verified: 77/77 backend tests (new `tests/test_notary.py` locks fee
  brackets; template-count test updated 7→11), frontend build OK
  (sw cache → v16), /noteret 200, fee API returns 120€/96€ for an
  85k€ sale/solemnization, notary-pack PDF generates correctly.
- Left open: 08/L-272 full text ingestion (no source yet); ONK email is a
  draft — the owner decides when to send; Phase-3 notary-office accounts
  only if ONK shows interest.

## 2026-07-13 — Leaked simulation lawyer removed from live directory; sim cleanup made crash-proof (Cursor / Fable 5)

- Context: the owner celebrated "the first lawyer in the directory" — but the
  entry was **"Zyra Sim 928866 / Av. Driton Sim"**, a leftover from a
  `full_simulation.py` run whose cleanup never executed (the run aborted after
  a FAIL path). A fake verified lawyer (license SIM-928866, rating 4.7) was
  publicly visible on avokatiim.ai.
- Done:
  - Deleted the leaked sim tenant, its citizen and its case from prod DB;
    `/public/lawyers` now returns [] and stats show 0 lawyers in directory.
  - `full_simulation.py`: cleanup moved to a `cleanup()` coroutine that runs
    in `finally` (always executes even on crash) and deletes by pattern
    (`Zyra Sim %`, `qytetari.sim.%@gmail.com`) instead of the exact suffix,
    so it also sweeps residue from older crashed runs.
- Also investigated for the owner: real first-lawyer candidates are Marigona
  Gashi (signed up, verified email, 1 login, no public profile yet — nudge
  email fires at +48h) and "Vegim H" (disposable yopmail address, unverified
  email, self-upgraded to solo → invoice P-2026-0001 €24 open, created 107
  contacts in ~1/sec scripted bursts — watch this tenant).
- Verified: py_compile OK, live directory/stats clean after deletion.
- Follow-up same day: personal email SENT to Marigona Gashi from the owner's
  address (script `backend/scripts/send_marigona_email.py`, SMTP OK) with the
  remaining onboarding steps; her `profile_nudge_sent_at` was set so the
  automated 48h nudge won't duplicate it. Status tracked in
  docs/rekrutimi/kontakt-oak-dhe-avokatet.md.
- Follow-up 2: the owner's Gmail inbox was full of "Address not found"
  bounces. Cause: SMTP_FROM is his personal Gmail, and the platform mailed
  nonexistent addresses — simulation accounts (`*.sim.*@gmail.com`), fake
  signups (`daaaaa@gmail.con`, earlier `leof*@gmail.com` wave) — so Gmail
  returned an NDR per message. Fix: `send_email()` now suppresses test/
  seed/typo recipients via `_TEST_RECIPIENT_RE` (sim pattern, example.*,
  avokatim.local/app, gmail.con) and logs instead. New unit tests in
  tests/test_email_suppression.py; 73 passed, health OK after restart.
- Follow-up 3: personal re-engagement emails sent from the owner's address
  to every real incomplete signup (`scripts/send_incomplete_signup_emails.py`,
  dry-run previewed first): 2 lawyers (Kujtim — unverified email, fresh
  verify link; Jeton — missing OAK license) and 6 unverified citizens (fresh
  3-day verify links). Skipped: obvious test accounts, gmail.con typo,
  yopmail. Nudge timestamps set to prevent automated duplicates. Status
  tracked in docs/rekrutimi/kontakt-oak-dhe-avokatet.md.
- Follow-up 4 — OAK-wide outreach campaign started: scraped the public OAK
  registry (oak-ks.org/avokatet, polite sequential fetch) into
  data/oak_registry.csv — 1457 lawyers, 1456 with email (Prishtinë 771).
  New `scripts/oak_outreach_campaign.py` sends personalized batches (default
  30/run, 8s apart, Prishtinë first) from the owner's Gmail with dedup log
  in data/oak_outreach_log.csv, opt-out via "STOP", source of address
  disclosed. Batch 1 (30 Prishtina lawyers) sent successfully. Rationale
  for the small batch: same Gmail account carries transactional email, so
  sender reputation is protected. Full list coverage at this pace ≈ 7 weeks;
  a dedicated sending domain would allow faster ramp.
- Left open / next: run the next OAK batch daily (script is idempotent);
  add "STOP" repliers to SUPPRESS; await Marigona's reply/activation; decide
  what to do with the Vegim tenant if it stays unverified past the invoice
  due date.

## 2026-07-13 — Public presentation catch-up: marketing pages now cover every new feature (Cursor / Fable 5)

- Context: an inventory of `/`, `/per-qytetaret` and `/per-avokatet` against
  the current product showed the newest capabilities (deep research, AI
  clause assist, doc summaries, paid consultations, onboarding wizard,
  referrals, SMS alerts, Ava-intake, /siguria) were not presented anywhere
  on the marketing pages. WhatsApp deliberately NOT advertised (no
  credentials yet — don't promise what doesn't run).
- Done (all strings ×6 locales):
  - **Landing `/`**: lawyer function list 6→8 items (`umbFnL7` deep
    research, `umbFnL8` paid consults; `umbFnL2` now mentions summaries +
    "Përmirëso me AI" with risk flags); `umbFnC5` mentions online payment;
    trust section gained a "Si i mbrojmë të dhënat →" link to `/siguria`
    (`landPrivLink`).
  - **`/per-avokatet`**: new "Ava — ekipi yt juridik me AI" section (4
    cards: deep research, template AI assist, doc summaries, deadline
    extraction; `lpAi*`); `lpFeat2`/`lpFeat8` rewritten, new `lpFeat9`
    (instant push/email/SMS match alerts); onboarding hint under the hero
    CTA (`lpOnboardHint`); referral sentence in the Founder card
    (`lpReferralHint`).
  - **`/per-qytetaret`**: `landAvaB` now tells that Ava structures the
    case from the chat; `landMarketB` mentions paying the consult by card;
    SOS section links to `/siguria` (`landSosSecLink`).
  - **In-app intros**: `assistantIntro` (deep-research toggle),
    `templatesIntro` ("Përmirëso me AI" flow), `mattersIntro` ("Nxirr
    afatet" + "Përmbledh me AI") rewritten so the story continues from the
    landing into actual usage.
- Verified: build OK, restart OK, all new strings render on the three live
  pages (curl grep); sw bumped to v15.
- Left open / next: none for this task.

## 2026-07-13 — Improvement backlog Phase 3: agentic AI + trust pages (Cursor / Fable 5)

- Done (points 11–15 of the 15-item plan — see D-022):
  11. **Deep research** (`deep_research_stream` in `services/assistant.py`,
      `POST /assistant/deep-research` SSE): the question is decomposed into
      3–5 sub-questions (LLM JSON), each searched in the corpus, then one
      synthesis with merged deduped citations. UI: "Hulumtim i thelluar"
      toggle in the assistant with a live step list (`deepResearch`/`dr*`
      keys ×6).
  12. **AI clause assist** (`POST /templates/ai-assist`): draft +
      instruction → improved text + risk flags + change list (JSON).
      "Përmirëso me AI" panel next to the template output with
      accept/discard; respects `allow_external_ai`.
  13. **Document AI summaries** (`POST /documents/{id}/summarize`):
      summary + key points + possible deadlines (reuses the deadline
      extractor); cached in new `documents.ai_summary` column (migration
      `31de290208e7`); "Përmbledh me AI" button + modal in the matter
      Documents tab.
  14. **Public /siguria page** (×6, `sec*` keys): encryption at rest,
      local embeddings, evidence hash chain, external-AI kill switch,
      daily backups, 06/L-082 compliance; linked from the public footer
      and a security card on /per-avokatet.
  15. **e-Kosova readiness**: `docs/integrimet/e-kosova.md` (6 prepared
      integration points: SMIL statuses, hearings, e-filing, eID login,
      OAK registry, free legal aid) + new section in the government pitch
      (`docs/pitch/qasje-ne-drejtesi.md`).
- Verified: pytest 69 passed; full_simulation **188 checks / 0 FAIL**
  (new: deep-research steps + citations, ai-assist, doc summary + cache
  hit); build + restart OK; sw bumped to v14.
- Left open / next: Stripe Connect per-office payouts when consult-payment
  volume justifies it (D-021); WhatsApp/SMS/Stripe remain off until
  credentials are configured.

## 2026-07-13 — Improvement backlog Phase 2: growth (founders, Ava-intake, WhatsApp, SMS, paid consults) (Cursor / Fable 5)

- Done (points 6–10 of the 15-item plan):
  6. **Founder badge + referrals**: `lawyer_profiles.is_founder` set
     automatically for the first 20 verified offices (`FOUNDER_LIMIT` in
     `api/platform.py`); "Themelues" badge in the directory and a section on
     `/per-avokatet`. Referral program: `tenants.referral_code` /
     `referred_by_code`, `?ref=` accepted at `/regjistrohu`, lazy code +
     referred-count via `GET /marketplace/referral`, section in settings.
     Draft outreach emails for OAK and Marigona in
     `docs/rekrutimi/kontakt-oak-dhe-avokatet.md`.
  7. **Ava-intake**: `POST /public/ava/structure-case` turns the chat
     history into a clean JSON draft `{category, description, city,
     urgency}` via the LLM abstraction (rate-limited); "Më lidh me avokat"
     on `/ava` now prefills `/posto-rastin` with the structured case.
  8. **WhatsApp webhook stub** (`api/whatsapp.py`): Meta verification
     handshake + inbound text → Ava reply via Graph API (httpx); logs
     instead of sending when `whatsapp_*` credentials are unset; daily
     quota per phone number. Activation guide in
     `docs/integrimet/whatsapp.md`.
  9. **iOS push + SMS**: "Add to Home Screen" PWA guide for Safari in
     settings; `lawyer_profiles.phone` + `sms_case_alerts` columns; new-case
     and SOS notifications also go out via the existing Twilio-compatible
     SMS service when enabled.
  10. **Paid consultations**: when the lawyer has `consult_fee_eur` and
     Stripe is configured, bookings are created as `pending_payment` with a
     Stripe Checkout link (`metadata[booking_id]`); the webhook flips them
     to `pending` and only then notifies the lawyer; `pending_payment`
     holds the slot; fail-open to the free flow if Stripe errors. New
     status shown at /rasti-im (`bkStatusAwaitingPay` ×6).
- Migrations: `c3a3e4c5a37f` (founder + referral codes), `8fc9637a45d9`
  (lawyer phone/SMS), `e0c562b27017` (booking fee_eur).
- Verified: pytest 69 passed; full_simulation 183 checks (incl. spam-case
  LLM rejection, structure-case, no-Stripe booking flow); health OK; build
  + restart OK; sw bumped to v13.
- Left open / next: Phase 3 (deep research, AI clause assist, doc
  summaries, /siguria page, e-Kosova readiness doc).

## 2026-07-13 — Improvement backlog Phase 1: onboarding, emails, quality gate, analytics (Cursor / Fable 5)

- Context: interest analysis showed real demand (79 Ava questions from 47
  unique IPs, 13 citizen accounts, 5 cases) but both new lawyer signups
  (incl. the first real one, Marigona Gashi) stopped before activating the
  public profile, and all 4 real /kontakti attempts failed with 422.
- Done (points 1–5 of the 15-item plan):
  1. **Onboarding wizard** `/onboarding` (3 steps: public profile → OAK
     license + fee → optional booking hours); signup now redirects there
     instead of the dashboard. Fixed the broken `#public-profile` anchor
     (Card now accepts `id`). New `ob*` strings ×6.
  2. **Automatic emails**: lawyer welcome email with concrete next steps
     (i18n ×6, `lawyer_welcome_*`); verification email moved from hardcoded
     text to `tr()`. One-shot nudges in `reminder_loop`: lawyer with
     inactive profile after 48h, citizen unverified after 24h (columns
     `users.profile_nudge_sent_at`, `citizen_users.verify_reminder_sent_at`,
     only accounts from the last 14 days).
  3. **/kontakti fixed**: code-point character counter (emoji-safe, matches
     Python len), inline email validation, friendly 422/429 messages ×6.
  4. **Case quality gate** (`services/case_quality.py`): heuristics
     (repetition/gibberish/too short) + LLM JSON classification, fail-open;
     `case_requests.quality_flag` column; localized rejection message ×6.
     The simulation's ad-spam case is now genuinely rejected by the LLM.
  5. **Umami analytics** self-hosted: new compose service (port 3210,
     own DB in the existing Postgres), public at https://stats.avokatiim.ai
     via the Cloudflare tunnel, cookie-free script injected in layout via
     `NEXT_PUBLIC_UMAMI_*` (frontend/.env.local). Admin password in `.env`.
- Migrations: `35b967911198` (nudge timestamps), `709756624282` (quality_flag).
- Verified: 65 backend tests pass, full simulation 180/180 PASS, health OK,
  /onboarding 200, Umami script in HTML, stats subdomain live.
- Next: Phase 2 (founder badge, Ava-intake, WhatsApp, iOS push + SMS, Stripe
  consult payments) and Phase 3 (deep research, AI clauses, doc summaries,
  /siguria, e-Kosova doc).

## 2026-07-12 — First real-usage check + fake-signup cleanup (Cursor / Fable 5)

- Context: the owner received Gmail bounce emails ("Address not found")
  for verification mails; asked whether the service has problems and
  whether people are using it.
- Findings: service healthy (SMTP sends fine — bounces exist because the
  recipients were fake); real usage in the last 24h: 430 audit actions
  from 10 distinct public IPs (mostly Kosovo ISPs), 14 citizen accounts,
  4 posted cases (incl. one SOS from Prishtina, one urgent from Peja) —
  all still open, no verified lawyers claiming yet. One actor
  ("leo frateli", US hosting IP 69.16.157.92, likely VPN) created 5
  accounts with fake gmail addresses in ~70s; the 5/hour/IP signup rate
  limit stopped them exactly at 5, and unverified accounts cannot post.
- Done: deleted the 5 fake unverified `leof*@gmail.com` accounts after
  confirming zero dependent rows (cases/bookings/evidence). 9 accounts
  remain. No code changes; CAPTCHA noted as the next step only if VPN
  abuse grows.

## 2026-07-12 — Aesthetic refresh of the public surfaces (Cursor / Fable 5)

- Context: the owner liked the new landing content but asked for a more
  modern visual treatment ("jepi një frymë moderne").
- Done: **Inter** via next/font (self-hosted woff2 at build, latin +
  latin-ext for ë/ç; replaces Arial in globals.css). New CSS utilities:
  `.hero-backdrop` (two soft radial glows + faint dot grid),
  `.text-hero-gradient` (slate→indigo→violet headline), staggered
  `fade-in-up-d1/d2`. Landing: hero badge pill, extrabold gradient
  headline (up to text-6xl), trust chips as pills, audience cards with
  gradient top border / ring / hover lift; function and privacy cards
  rounded-3xl with slate→indigo-950 gradient; stats with gradient
  numbers. /per-qytetaret: gradient headline, glassy Ava box, lifted
  path cards, gradient SOS tile. /per-avokatet: badge pill, white→indigo
  gradient headline, elevated CTAs, hover on feature cards. PublicShell
  logo got a gradient scale-icon mark. SW cache v7.
- Verified: build OK, restart, health OK, /, /per-qytetaret,
  /per-avokatet all 200, Inter variable class present on <html>.
- Left open / next: none.

## 2026-07-12 — Owner account becomes platform administrator + citizen (Cursor / Fable 5)

- Context: the owner's login (superadmin inside tenant "BoraArifi") was
  treated as a lawyer everywhere — /login sent them to /dashboard and the
  landing banner said "Je i kyçur si avokat". They asked to be an
  administrator + a citizen, not a lawyer.
- Done (UX): /login now fetches /auth/me after login — `is_superadmin` →
  /platform, else /dashboard (all 3 flows: setup, login, 2FA); the landing
  banner distinguishes admin (dark, "administrator i platformës" →
  /platform) from lawyer (indigo → /dashboard). `umbLoggedAdmin`/
  `umbGoPlatform` ×6.
- Done (data, one-off, owner-approved): deleted the synthetic test matter
  "TEST-CERT lende sintetike" + 2 "Test Certifikata" contacts from the
  owner tenant; renamed tenant "BoraArifi" → "AvokatIM Administrata"
  (plan stays firm/0 € — never billable, no lawyer profile — never in
  the directory). Seeded the owner's citizen account
  (arifi.arber@gmail.com, verified, temp password shared privately).
- Verified: build OK, restart, health OK, citizen login with the temp
  password returns a token.
- Left open / next: owner should change the temp citizen password in
  /llogaria.

## 2026-07-12 — Two-surface restructure + citizen account (Cursor / Fable 5)

- Context: "Ristrukturimi: dy botë + llogaria e qytetarit" plan — the owner
  wanted the landing to present the WHOLE project, a clear split between the
  two audiences, and a real "place" for citizens (their login used to be
  hidden and every visible "Kyçu" led to the lawyer login).
- Done (landing): `/` rebuilt as the umbrella presentation — mission hero,
  two big audience cards (citizen → /per-qytetaret, lawyer → /per-avokatet),
  side-by-side full function lists (7 citizen + 6 lawyer), "Pse AvokatIM"
  advantage grid, stats, privacy card. New `umb*` strings ×6.
- Done (story pages): new `/per-qytetaret` carries the citizen story (Ava
  box hero, 3 quick paths, 4 alternating feature sections, how-it-works);
  `/per-avokatet` gained a 3-step "how the marketplace works for you"
  section (`lpHiw*` ×6).
- Done (citizen account API): `PATCH /public/citizen/me` (name, phone,
  locale), `POST /public/citizen/change-password` (rate-limited, audited),
  `POST /public/citizen/forgot-password` (no account enumeration) +
  `reset-password` with a `citizen_reset` purpose token (1h; also verifies
  the email, since owning the link proves mailbox control). New
  `citizen_reset_*` email strings ×6.
- Done (citizen account UI): shared `citizen-auth.tsx` form (signup/login/
  forgot) reused by `/posto-rastin`, `/rasti-im` and the new `/kycu` (which
  also hosts the ?rivendos= reset form); new `/llogaria` page (profile,
  language, password change, quick links, Dil); `PublicShell` header now
  recognizes the citizen token — initials chip with menu (Rasti im,
  Llogaria, Dil) — and shows "Kyçu" → /kycu otherwise; `/login` got a
  "Je qytetar?" banner and /kycu the reverse link; footer links the new
  pages. SW cache bumped to v5.
- Verified: 60 pytest pass (new reset-token scope + validation tests),
  `npm run build` OK, service restarted, health OK, full simulation
  178 PASS / 0 FAIL (new: profile update, change-password wrong/right,
  login with new pw, forgot without enumeration, reset with token,
  invalid token rejected, login after reset).
- Follow-up (same day): the owner, signed in as a lawyer, could never see
  the new landing (valid lawyer token auto-redirected `/` → /dashboard).
  Changed: `/` always renders; a signed-in lawyer gets an indigo banner
  "Je i kyçur si avokat — Vazhdo te paneli" instead of a redirect
  (`umbLoggedLawyer`/`umbGoDash` ×6, SW cache v6).
- Left open / next: none for this plan.

## 2026-07-12 — Public redesign + letters & complaints + platform contact channel (Cursor / Fable 5)

- Context: "Ridizajni publik + shkresa e ankesa" plan — modern public UI,
  full project story on the landing, richer document generator, and a
  feedback channel to the platform operator.
- Done (identity): `icons.tsx` (shared SVG icon set, replaces emoji),
  `public-footer.tsx` (4-column footer mounted once in `PublicShell`),
  shell header with backdrop-blur + "Vegla" dropdown (afatet/dokumentet),
  `fade-in-up` CSS utility.
- Done (landing): rebuilt `/` as a full story — hero + trust strip, "Çfarë
  është AvokatIM" paragraphs, 4 alternating feature sections (Ava / SOS
  mbrojtja AI / tregu & drejtoria / veglat falas), how-it-works, dark
  trust-and-privacy card, stats, lawyer CTA. New `land*` strings ×6.
- Done (documents): 4 new deterministic templates in `citizen_docs.py`
  (qasje_dokumente 06/L-081, ankese_konsumatori 06/L-034, verejtje_pune
  03/L-212, kundershtim_urdherpagese LPK) — 7 total, each with a
  `category`; /dokumentet groups by category (Institucionet / Puna /
  Konsumatori / Të përgjithshme).
- Done (feedback): `PlatformFeedback` model (migration `391e7cf5703d`),
  rate-limited `POST /api/public/feedback` + email to superadmins, public
  page `/kontakti` (kind chips, optional identity), "Ankesat & sugjerimet"
  review section in /platform (new/handled tabs, mark-handled).
- Done (page polish): /ava avatar bubbles + 4 example-question chips;
  /avokatet sticky filter bar + skeleton loading; /posto-rastin 3-step
  indicator + success screen; /rasti-im case status timeline
  (postuar→marrë→konvertuar); /afatet + /dokumentet icon headers;
  /per-avokatet gained lpFeat7/8 (OAK badge + booking) and /kontakti link.
- Verified: 57 pytest pass (new `test_feedback.py`), `npm run build` OK,
  full simulation 169 PASS / 0 FAIL (7 templates, consumer-complaint PDF,
  feedback accept/reject, 403 for non-superadmin), health OK, sw cache v4.
- Left open: nothing blocking from this plan.

## 2026-07-12 — AI protection by phone (voice + evidence + SOS) + public tools + booking (Cursor / Fable 5)

- Context: phases 2–4 of the "Mbrojtja AI + backlog i plotë" plan (D-018).
- Done (Phase 2 — voice): `app/services/voice.py` + `/api/public/voice/*`
  (status, transcribe, tts) — faster-whisper Albanian CT2 int8 (fallback
  turbo for sr/tr/bs/en/zh) + Piper `sq_AL` as subprocess; rate-limited.
  Config keys `voice_*` in `config.py`; models under `data/models/`.
- Done (Phase 2 — evidence vault): `EvidenceSession`/`EvidenceChunk`
  (migration `5685c4b4cd3f`), 5 s chunked uploads with SHA-256 hash chain,
  Fernet encryption, audit log, chain-of-custody PDF package, background
  transcription; citizen endpoints + read-only lawyer endpoints on claimed
  cases; `evidence-vault.tsx` list + downloads in /rasti-im, evidence block
  in the lawyer's Tregu case cards.
- Done (Phase 2 — SOS UI): `sos-panel.tsx` — one screen, three big actions
  (record evidence / talk to Ava push-to-talk with live transcript + spoken
  replies / alert duty lawyers), one-time consent, red "recording" banner;
  SOS dispatch attaches the running evidence session to the case. Privacy
  policy gained an "SOS recordings & voice" section ×6.
- Done (Phase 2 — call recording, Egress replaced per D-018): `video-call.tsx`
  mixes both audio sides via Web Audio into evidence chunks (kind `call`);
  citizen gets a record button, lawyer must accept a consent notice to join.
- Done (Phase 3): `voice-controls.tsx` (MicButton hold-to-talk + SpeakButton)
  wired into public /ava and the lawyer assistant.
- Done (Phase 4): public deadline calculator `/afatet` over
  `GET/POST /api/public/tools/deadline-*`; citizen document generator
  `/dokumentet` (3 deterministic Jinja→PDF templates in
  `app/seeds/citizen_docs.py`: request letter, admin appeal, authorization);
  consultation booking — `ConsultBooking` + `LawyerProfile.booking_enabled/
  booking_slots` (migration `51f3b67b1756`), weekly-availability editor in
  Settings, slot picker in /avokatet, my-bookings in /rasti-im, confirm/
  decline panel in Tregu, emails ×6. Landing links both public tools.
- Verified: pytest 50 passed (new `test_voice.py`, `test_evidence.py`,
  `test_bookings.py`); `full_simulation.py` sections 29–32 (evidence chain +
  tamper/order rejection, TTS WAV, calculator due-date, doc PDF, booking
  lifecycle incl. double-book 409) — **163/163 PASS**; frontend build OK;
  service restarted, health OK.
- Left open: Egress container stays optional future infra (D-018); realtime
  duplex voice waits for GPU (LiveKit Agents); STT model download happens on
  first use if `data/models/` is empty.

## 2026-07-12 — OAK verification + client reviews + transparent pricing (Cursor / Fable 5)

- Context: Phase 1 of the "Mbrojtja AI + backlog i plotë" plan — the trust
  layer required before public promotion.
- Done: `LawyerProfile` gained `oak_license_no`, `verification_status`
  (none/pending/verified/rejected), `verified_at`, `verification_note`,
  `consult_fee_eur`. Migration `16241f40c7cc`. Entering/changing the license
  sets status to pending and emails superadmins; only `/platform` can decide
  (`GET /platform/verifications`, `POST /platform/verifications/{id}/decide`,
  approval/rejection emailed to the lawyer in their locale). Trust gate:
  unverified lawyers are excluded from the public directory, case-match and
  SOS-duty notifications, public stats, and get 403 on claim. New `CaseReview`
  model (1:1 with concluded claimed cases; communication/speed/clarity 1–5 +
  optional comment, never the legal outcome); citizen endpoints to post/read
  the review; directory now returns `verified`, `rating`, `review_count`,
  `consult_fee_eur` and sorts by plan tier then rating. UI: license field +
  status pill + consult fee in Settings, verification queue in /platform,
  verified badge + stars + price in /avokatet, star review form in /rasti-im,
  "verification required" banner in /marketplace. Strings ×6 (frontend and
  backend emails); added the previously missing `pubProfileNudge*` keys.
- Verified: pytest 39 passed; full_simulation extended (pending→hidden,
  verified→listed with badge/fee, review posted, duplicate 409, average in
  directory) — 138/138 PASS; frontend build OK; health OK.
- Left open: phases 2–4 of the plan (voice, evidence vault, SOS UI, egress,
  voice Ava, deadline calculator, booking, citizen docs).

## 2026-07-11 — Per-page onboarding intros + "how it works" landing section (Cursor / Fable 5)

- Context: owner asked to enrich every page with explanations so both
  citizens and lawyers understand how to use it, and to have the landing
  page tell the platform story exactly as in the presentation deck.
- Done: new `frontend/src/components/page-intro.tsx` — dismissible
  explainer card per page (localStorage-remembered, collapses into a
  "?" pill that reopens it). Mounted on 4 citizen pages (/ava,
  /posto-rastin, /rasti-im, /avokatet) and 11 lawyer pages (dashboard,
  intake, matters, contacts, calendar, templates, assistant, billing,
  marketplace, reports, settings). Landing `/` got a "Si funksionon
  AvokatIM" section: one-platform-two-worlds line, 3 steps
  (ask/post → marketplace matches → follow in portal), free-forever note.
  41 new dictionary keys ×6 locales. SW cache bumped to v3.
- Verified: tsc clean, `npm run build` OK, service restarted, health OK,
  /avokatet SSR shows the intro text (others render client-side by design).
- Left open: nothing.

## 2026-07-11 — Project presentation deck (Cursor / Fable 5)

- Context: owner asked for a presentation of the whole project now that the
  citizen side + marketplace exist, delivered to a folder on the Desktop.
- Done: 9-slide HTML deck (16:9, Albanian) + PDF via WeasyPrint in
  `~/Desktop/Prezantimi-AvokatIM/` (outside the repo, per request). Covers:
  the two-sided problem, the bridge/marketplace, citizen side (Ava/market/SOS),
  lawyer side (office + leads), quality-up/cost-down effects, revenue model
  (0€ citizens, 3mo trial, €24/user/mo, no fee split), tech/trust, call to
  action. Facts sourced from `docs/pitch/qasje-ne-drejtesi.md` and D-016.
- Verified: rendered all PDF pages to images and inspected layout.
- Left open: nothing; deck is a static artifact, regenerate from the HTML if
  pricing or stats change.

## 2026-07-11 — Platform subscription billing + demand↔supply matching (Cursor / Fable 5)

- Context: owner asked to compare AvokatIM with the field leaders
  (LegalMatch/Avvo/Thumbtack/Clio), close the gaps, and implement lawyer
  payments — "after 3 free months the system must collect revenue".
  Decision recorded as D-016 (per-seat subscription, never fee splitting).
- Done (billing): `PlatformInvoice` model + `Tenant.plan_price_eur`
  (migration `befbfa13f9f3`; founder tenant price 0). Service
  `app/services/platform_billing.py`: TRIAL_DAYS 30→90, idempotent
  monthly invoice generation (P-YYYY-NNNN, seats × price), daily billing
  loop in the lifespan (invoices + emails, weekly dunning with Redis dedup,
  trial-ending nudges). Tenant API `/billing/subscription` (+`/upgrade`
  self-service, +Stripe payment-link with `platform_invoice_id` metadata;
  webhook extended). Superadmin: `/platform/invoices`
  (list/generate/mark-paid/void) + per-tenant price. Enforcement: overdue
  past 14+14 days ⇒ `past_due` ⇒ marketplace claim 402 + red banners;
  data access never blocked. UI: Settings→"Abonimi" section, platform
  invoices panel, trial banner now points to self-serve upgrade.
- Done (matching): new non-directed cases push+email lawyers whose
  practice areas/cities match (`case_match_*` ×6); lawyer browse ranked
  SOS → directed → profile match → recency with `matches_profile` chip;
  paid plans sort first in the public directory (`highlighted` ring) —
  the "profil i theksuar" perk is now real.
- Done (i18n): 8 backend keys + ~28 UI keys ×6 languages; trial texts
  30 days → 3 months everywhere.
- Verified: 35 unit tests pass; `full_simulation.py` **133 PASS / 0 FAIL**
  (new section 28: upgrade → invoice = seats×price, double-upgrade 400,
  unlimited leads after upgrade, overdue→402, bank-transfer mark-paid →
  claim resumes); next build clean; health OK.
- Left open / next: set `PLATFORM_BANK_DETAILS` in backend/.env before the
  first real invoice; contract a card gateway usable in Kosovo (Stripe
  doesn't operate XK-direct) and route the webhook publicly; consider a
  subscription-invoice PDF if firms ask for one.

## 2026-07-11 — Citizen-first public UX: landing, bottom nav, /per-avokatet (Cursor / Fable 5)

- Context: owner asked whether citizens need their own interface separate
  from lawyers, especially on the phone. Researched Avvo, JustAnswer,
  LegalZoom, Airbnb (dual-persona, one platform) and 2026 marketplace-UX
  guides; delivered the analysis canvas `nderfaqja-qytetar-vs-avokat`
  and the owner approved the proposal.
- Done: `src/components/public-shell.tsx` — shared shell for all citizen
  pages: desktop header (nav links + SOS + discreet "Për avokatët") and a
  mobile **fixed bottom nav** (Ava · Avokatët · elevated red SOS center ·
  Posto · Rasti im; 48px+ targets, safe-area-inset). Landing `/` rebuilt
  citizen-first: hero = Ava question box (stores `avokatim_ava_prefill`;
  `/ava` auto-asks it on mount), 3 action cards, stats, footer. New dark
  marketing page `/per-avokatet` (features, trial-vs-paid plans, CTAs).
  `/ava`, `/avokatet`, `/posto-rastin`, `/rasti-im` now use the shell
  (own headers removed). Manifest: start_url `/` + shortcuts SOS/Ava/
  Rasti im. ~20 new keys ×6 languages.
- Verified: tsc + next build clean; all six public routes return 200;
  manifest serves the shortcuts. Lawyer app untouched.
- Left open / next: trust signals on lawyer profiles (reviews, verified
  OAK licence badge, response time) — after the pilot.

## 2026-07-11 — SOS video/audio room with self-hosted LiveKit (Phase 3, LAN) (Cursor / Fable 5)

- Done (infra): `livekit/livekit-server:v1.9` added to docker-compose
  (signaling 127.0.0.1:7880, media 7881/tcp + 7882/udp, `livekit.yaml`
  with `use_external_ip: false` for now). Generated API key/secret pair —
  stored ONLY in git-ignored `.env` (root, → container `LIVEKIT_KEYS`) and
  `backend/.env` (`LIVEKIT_API_KEY/SECRET`); the two must match. Caddy
  gained `https://:7443 → 7880` so LAN browsers get wss:// signaling.
- Done (backend): `app/services/livekit.py` mints HS256 join tokens with
  pyjwt (no SDK; 4h TTL, grant restricted to one `sos-<case_id>` room).
  `POST /api/marketplace/cases/{id}/call-token` +
  `/api/public/citizen/cases/{id}/call-token` give the lawyer and the
  citizen tokens for the same room (claimed/converted cases only,
  audit-logged, `enabled:false` graceful when keys missing). New config:
  `livekit_api_key/secret/url` in `config.py`.
- Done (frontend): `src/components/video-call.tsx` (npm `livekit-client`) —
  full-screen call overlay (remote video, local preview, mic/cam toggles,
  hang up, waiting/off/error states); "Thirrje video" buttons on claimed
  cases in Tregu and `/rasti-im`. Signaling URL derived from the page host
  (ws://127.0.0.1:7880 local, wss://<host>:7443 LAN). 8 new UI keys ×6.
- Verified: 31 pytest pass; tsc + next build clean; simulation section 27 —
  **123 PASS / 0 FAIL** (both sides get tokens for the same room, LiveKit
  server itself validates both tokens via /rtc/validate, non-active case
  denied). Token generation verified against the running server.
- Left open / next: calls work on localhost + LAN today. For calls over the
  public internet (avokatiim.ai) the owner must either port-forward
  7881/tcp + 7882/udp on the router (then set `use_external_ip: true` in
  livekit.yaml) or stand up a coturn TURN relay on a small VPS, plus a
  public wss signaling route. Everything else is ready and unchanged.

## 2026-07-11 — SOS duty flow (Phase 3, no video) + lead limits (Phase 4) (Cursor / Fable 5)

- Done (backend): `LawyerProfile.sos_on_duty` + migration `e98ec43b937a`;
  `POST /api/public/citizen/sos` (citizen account required, verified email
  NOT required — emergencies can't wait for an inbox; rate limit 2/24h per
  citizen) creates a `CaseRequest` with `urgency="sos"` and background-alerts
  every on-duty lawyer of every active tenant via push + email
  (`sos_alert_*` ×6 languages). SOS cases sort first in lawyer browse.
  Lead limits: trial plan = 5 claims/calendar-month (claim → 402 when
  exhausted), solo/firm unlimited; `GET /api/marketplace/lead-quota`.
- Done (frontend): red SOS button + form on `/rasti-im` (auto-opens with
  `?sos=1`; landing citizen block links to it), SOS badges on both sides,
  SOS-duty toggle in the Tregu header + settings public-profile checkbox
  (settings now round-trips `sos_on_duty` so saving the profile doesn't
  wipe the duty flag), lead-quota counter in the Tregu header,
  friendly 6-language message when the lead limit is hit. 10 new UI keys ×6.
- Verified: 29 pytest pass; tsc + next build clean; full_simulation section
  26 — **118 PASS / 0 FAIL** (duty opt-in, SOS posted, sorts first, claimed,
  quota 1→2 of 5, third SOS in 24h blocked with 429).
- Left open / next: Phase 3 video/audio room still blocked on WebRTC media
  ports (Cloudflare Tunnel is HTTP-only; needs router port forwarding or a
  TURN relay VPS — owner's call). When infra lands: LiveKit self-hosted +
  room tokens on SOS claim. Paid-plan billing itself stays manual (D-008).

## 2026-07-11 — Public stats + "access to justice" pitch (Phase 4 groundwork) (Cursor / Fable 5)

- Done: anonymous `GET /api/public/stats` (visible lawyers, cases
  posted/taken, average hours from posting to claim, laws/chunks in the
  corpus — no personal data) + 4-card stat strip on the public landing
  (4 new UI keys ×6 languages); pitch document
  `docs/pitch/qasje-ne-drejtesi.md` for the government/OAK proposal.
  full_simulation gained a stats check and now clears citizen-signup
  rate-limit keys at the start of section 24 (repeated runs from the same
  IP were hitting the 5/hour limit — first re-run crashed on that; also
  cleaned up the leftover "Zyra Sim 95b156" tenant from the crashed run).
- Verified: 26 pytest pass; tsc + next build clean; full_simulation
  **111 PASS / 0 FAIL**; /api/public/stats live (9 laws, 4016 chunks).
- Left open / next: Phase 3 SOS video/audio — blocked on network
  infrastructure (WebRTC media can't cross Cloudflare Tunnel; needs router
  port forwarding or a small TURN relay VPS — owner's call); paid lawyer
  plans/lead fees (billing stays manual per D-008 until the owner decides).

## 2026-07-11 — Public Ava: free legal chat for citizens (Phase 2) (Cursor / Fable 5)

- Done (backend): `/api/public/ava/ask` + `/ask-stream` (SSE) + `/quota` in
  `app/api/marketplace.py`. Reuses the platform-level RAG corpus (XK) for
  citations; dedicated public system prompt (legal information, NOT advice;
  answers in the question's language; recommends "Më lidh me avokat").
  Stateless (client-held history, nothing persisted). Redis daily quotas:
  5/day anonymous (IP+session), 20/day with citizen account (optional
  citizen token). Provider goes through the existing LLM abstraction.
- Done (frontend): public `/ava` streaming chat (citation chips, disclaimer,
  quota display, Enter-to-send), "Më lidh me avokat" prefills
  `/posto-rastin` via localStorage draft; landing citizen block gained the
  "Pyet Avën falas" button. 10 new UI keys ×6 languages.
- Verified: 26 pytest pass (2 new); tsc + next build clean; full_simulation
  section 25 — **110 PASS / 0 FAIL** (anon quota 5, citizen quota 20, real
  LLM answer with 6 corpus citations, quota decrement); /ava returns 200.
- Left open / next: Phase 3 SOS (still blocked on WebRTC ports / TURN),
  Phase 4 (plans/lead fees + public stats + government pitch).

## 2026-07-11 — Public citizen marketplace: Phase 1 of the citizen-bridge vision (Cursor / Fable 5)

- Why: extend AvokatIM from a professionals-only tool into a public bridge
  citizens ↔ lawyers (owner's "pocket lawyer" vision, D-013). Phase 1 = the
  case marketplace; Phases 2–4 (public Ava, SOS video, revenue) designed only.
- Done (backend): `app/models/marketplace.py` — platform-level (tenantless)
  `CitizenUser`, `LawyerProfile`, `CaseRequest`, `CaseRequestMessage`;
  Alembic `ca20354674bd`. `app/api/marketplace.py` — citizen signup/login
  (own JWT claim `citizen`, mandatory privacy consent, email verification via
  purpose token, Redis rate limits), public lawyer directory with filters,
  case CRUD + messages; lawyer side: profile upsert, browse (masked citizen
  name), claim → existing conflict check → IntakeRequest source="marketplace",
  report-abuse. Intake accept now converts the linked case: Contact gets the
  citizen's email/locale/same password hash with portal auto-enabled, signup
  consent lands in ConsentRecord, citizen gets a localized "portal ready"
  email. 10 new email keys ×6 languages in `app/i18n.py`.
- Done (frontend): public `/avokatet`, `/posto-rastin` (auth + form,
  `?avokati=` for directed requests), `/rasti-im` (statuses, chat, close,
  `?verifiko=` email confirmation), new two-audience landing `/`; in-app
  `(app)/marketplace` "Tregu" (open/mine, claim + conflict warning, chat,
  report) + Settings "Profili publik"; `lib/citizen.ts` client with separate
  token. ~60 new UI keys ×6 languages.
- Verified: 24 pytest pass (5 new in test_marketplace.py); tsc + next build
  clean; full_simulation extended with section 24 — **106 PASS / 0 FAIL**
  (citizen signup guards, masked browse, claim/convert, same-password portal
  login, abuse report); all new pages return 200 on the live stack.
- Left open / next: Phase 2 public Ava (RAG is already platform-level),
  Phase 3 SOS video/audio (blocked on WebRTC media ports — Cloudflare Tunnel
  is HTTP-only; needs port forwarding or a TURN relay VPS), Phase 4 lawyer
  plans/lead fees + public stats dashboard for the government pitch.

## 2026-07-11 — Full rebrand: BoraLaw → AvokatIM, assistant Bora → Ava (Cursor / Fable 5)

- Why: the owner's daughter now works at a company with a similar product;
  keeping her name on this project could look like a conflict of interest.
- Done (visible): every UI string in all 6 locales, PWA manifest + regenerated
  icons/favicon ("A" on indigo), sidebar/mobile wordmark Avokat|IM, signature
  certificate brand, legal docs (ToS/PP/DPA/SLA/AML/RoPA), pitch docs, README,
  ICL offer on Desktop (folder + files renamed, PDF regenerated). Assistant
  renamed to "Ava" (system prompt, dictionaries in 6 languages incl. inflected
  forms, dictionary key askBora→askAva). Demo persona now "Av. Vera Demolli",
  demo login demo@avokatim.app / Demo2026!ava (tenant deleted + reseeded;
  seed_demo gained the now-required accept_tos flag).
- Done (infra): project folder ~/BoraLaw → ~/AvokatIM (compat symlink
  ~/BoraLaw kept for the IDE workspace); DB migrated to new cluster
  (user/db avokatim, dump+restore, 0 errors, 4016 corpus chunks verified);
  containers/volumes now avokatim-*; systemd units renamed to avokatim.service,
  avokatim-tunnel.service, avokatim-backup.{service,timer} (old ones removed,
  new enabled); backups dir → ~/AvokatIMBackups with key copied to
  ~/.config/avokatim/backup.key; backend/.env DATABASE_URL + SMTP_FROM updated.
  Cloudflare tunnel keeps its internal name `boralaw` (ID is wired into DNS).
- Verified: 19 pytest pass; tsc + next build clean; full_simulation 89/89 PASS;
  https://www.avokatiim.ai serves title "AvokatIM" + health {"app":"AvokatIM"};
  boraarifi.ai still shows the parking page.
- Left open / next: old docker volumes (boralaw_boralaw_*) kept as a safety
  net — remove after a few weeks; AGENTS.md keeps a historical-note line about
  the old names (intentional, so agents don't reintroduce them); old encrypted
  backups (boralaw-*.tar.gz.enc) remain readable with the same key.

## 2026-07-10 — Domain change: boraarifi.ai → avokatiim.ai (Cursor / Fable 5)

- Done: owner bought avokatiim.ai; updated `PUBLIC_BASE_URL` in `backend/.env`,
  added avokatiim.ai + www to the Cloudflare tunnel ingress
  (`~/.cloudflared/config.yml`) while keeping boraarifi.ai routed during the
  transition; replaced the domain in `full_simulation.py`, `isolation_check.py`,
  `docs/pitch/skenari-demo.md`, the ICL offer files on Desktop (HTML + email,
  PDF regenerated), and STATE.md. Stack + tunnel restarted.
- Verified: health OK, frontend 200, old domain https://boraarifi.ai still 200.
- Update (same evening): owner added avokatiim.ai to Cloudflare + switched
  nameservers; re-ran `cloudflared tunnel login` (new cert.pem scoped to the
  new zone; old cert kept as `cert.pem.boraarifi.bak2`), then
  `cloudflared tunnel route dns --overwrite-dns avokatim avokatiim.ai` (+ www).
- Verified: https://avokatiim.ai and https://www.avokatiim.ai serve the app
  (200 + `/api/health` ok); old domain boraarifi.ai still 200.
- Update 2: owner asked that boraarifi.ai no longer serve the app. Added a
  minimal parking page in the Caddyfile (`http://:8099`, inline HTML respond)
  and pointed the tunnel ingress for boraarifi.ai + www there instead of
  127.0.0.1:3000. Note: `http://127.0.0.1:8099` as the site address made
  Caddy return empty 200 bodies through the tunnel — binding `http://:8099`
  fixed it.
- Verified: boraarifi.ai + www serve the parking page (200, "Ky domen është i
  rezervuar"); avokatiim.ai + www serve the app (200 + /api/health ok); LAN
  :8443 unaffected.
- Left open / next: two stray CNAMEs `avokatiim.ai.boraarifi.ai` /
  `www.avokatiim.ai.boraarifi.ai` in the boraarifi.ai zone are harmless but
  can be deleted in the dashboard. When the old domain is dropped entirely,
  remove its ingress entries and the :8099 block.

## 2026-07-10 — Refresh the first-client proposal before sending (Cursor / Fable 5)

- Done: updated `docs/pitch/prezantimi-firma-avokatesh.md` (still unsent) to
  match the current product: 6 languages instead of 3 (Law 02/L-37 argument),
  the multi-lawyer firm layer is now described as BUILT (roles, restricted
  matters, per-lawyer reports) instead of "next step" — partnership argument
  repositioned to roadmap prioritization; added the newer differentiators
  (e-signature + certificate 08/L-022, trust ledger, OAK tariff, fiscal
  invoice PDF + card payments, email/SMS/calendar, public intake) and a new
  section on legal compliance as a product feature (06/L-082 consents/
  erasure/retention + ready contract pack, 05/L-096 KYC/source of funds/
  NjIF-K reports). Confidentiality paragraph now mentions the external-AI
  kill switch. Self-notes updated (demo flow, don't sell the firm module as
  future, demo tenant + runbook pointers).
- Verified: n/a (docs only).
- Left open / next: owner fills [emri]/[numri]/[emaili] and sends.

## 2026-07-09 — Full Kosovo-law compliance: 6 languages, data protection (06/L-082), AML (05/L-096) (Cursor / Fable 5)

- Done — **Phase 1, languages (Law 02/L-37)**: `Locale` extended to
  sq/sr/tr/bs/en/zh; ~490 keys × 3 new languages in `dictionaries.ts`;
  6-language `LocaleSwitcher`. New backend catalog `app/i18n.py`
  (`tr`/`pick_locale`/`bilabel`) — reminder emails, SMS, invoice email,
  **bilingual invoice PDF** (sq + client language), signature email and
  certificate follow `Contact.locale` (new column + contact UI; fallback
  contact → tenant default → sq; portal login returns it and the portal
  auto-switches). Seeds: sr/tr/bs names merged into deadline rules, holidays,
  OAK tariff (`_merge_name` keeps user edits); 3 Serbian templates seeded
  marked "kërkon rishikim nga avokati". AGENTS.md §5 now demands 6 languages.
- Done — **Phase 2, data protection (Law 06/L-082)**: public `/kushtet` +
  `/privatesia` pages in 6 languages (`lib/legal.ts`; Albanian originals in
  `docs/legal/`); required checkboxes at signup / public intake / portal
  first-login (all recorded with timestamp; portal via ConsentRecord with
  IP). `ConsentRecord` model + API + consent card on contact detail;
  SMS only with recorded consent. Erasure endpoint (anonymization, blocked
  on open matters), data-subject export ZIP, retention review
  (`Tenant.retention_years`, list in Settings — flags only, lawyer decides).
  `Tenant.allow_external_ai` gates the assistant to the local provider;
  UI warning/lock note (art. 49 transfers). New docs: breach procedure
  (72h → AIP), RoPA, DPA Annex A (DeepSeek/Stripe/SMTP/Twilio/Cloudflare).
  `backup.sh` retention 14→30 to match the SLA.
- Done — **Phase 3, AML (Law 05/L-096)**: KYC fields on Contact
  (document, verification date, risk level, PEP, beneficial owner) + form
  in the new contact-detail view; `TrustTransaction.source_of_funds` +
  audit flag + UI warning ≥ 10,000 €; 10 NjIF-K indicators × 6 languages as
  seed data; per-matter AML checklist (AML tab; scope auto-suggested from
  trust ledger; state in `Matter.extra`); `SuspicionReport` model + API +
  PDF export for NjIF-K + mark-submitted; compliance-officer picker in
  Settings; internal AML policy model `docs/legal/politika-aml.md`.
- Fixed en route: `Tenant.users` relationship became ambiguous after
  `compliance_officer_id` (second FK path) — explicit `foreign_keys`;
  contact export 500 (lazy `Invoice.items` in async) — `selectinload`.
- Verified: pytest 19 passed (new `test_i18n.py`); `npm run build` OK;
  migration `50226da4a670` at head; **full_simulation.py extended with
  sections 20–23 (languages, consents/privacy, external-AI gate, AML):
  89 PASS / 0 FAIL**; health OK; public pages 200.
- Left open / next: Serbian legal templates need lawyer review before use;
  qualified e-signature (QTSP) remains future work; AIP authorization for
  DeepSeek transfers is an organizational (not technical) step — documented
  in DPA Annex A.

## 2026-07-09 — Assistant answers now stream (SSE) — NetworkError fixed for good (Cursor / Fable 5)

- Bug persisted: even with `proxyTimeout: 300_000`, a user ask dropped
  mid-flight (browser-side), and Cloudflare tunnel (boraarifi.ai) kills
  idle connections at ~100s anyway. Root problem: one silent HTTP request
  hanging 60–180s while DeepSeek thinks is fragile everywhere.
- Fix (industry standard): **streaming end-to-end**.
  - `LLMProvider.chat_stream()` in `app/llm/base.py` (default: one chunk),
    real SSE streaming in `deepseek.py` and `local.py` (`stream: true`,
    yields `("thinking"|"delta", text)`; thinking tokens keep data flowing
    during reasoning so no idle timeout can trigger).
  - `ask_bora_stream()` in services (shared RAG prompt assembly factored
    into `_build_ask_messages`).
  - `POST /api/assistant/ask-stream` (SSE: meta / thinking / delta / done /
    error events; persists messages + audit on completion; uses its own DB
    session, not the request-scoped one). Old `/ask` kept for compatibility.
  - Frontend: `apiStream()` helper in `lib/api.ts`; assistant page renders
    the answer progressively as it streams in.
- Verified: exact user question through the :3000 proxy → HTTP 200, first
  bytes at 8s, 1383 thinking + 2138 delta events over 88s, final answer
  5097 chars with 6 citations (KPRK arts. 267–272); pytest 13 passed;
  build OK; service restarted.
- Note: matter AI tab (summarize/hearing-prep) still non-streaming — those
  are shorter, but candidates for the same treatment if timeouts appear.

## 2026-07-09 — Fix: Ava "NetworkError" on long answers (Cursor / Fable 5)

- Bug: asking Ava on `/assistant` sometimes showed "NetworkError when
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
  signature; logins demo@avokatim.app / klienti.demo@avokatim.app); demo script
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
  extraction → doc review workflow → template render → Ava ask (7 citations)
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
- Verified: 9 pytest pass; tsc + build clean; Ava answers real questions with
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
  `~/Desktop/Oferta-AvokatIM-ICL/` (HTML + WeasyPrint PDF + cover email text).
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
  created tunnel `avokatim`, CNAMEs for apex + www (--overwrite-dns over old
  parking records), config → 127.0.0.1:3000 (Next rewrites carry /api),
  systemd user service `avokatim-tunnel.service` (enabled, Restart=always).
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
  pages never hydrated. Fixed by `systemctl --user restart avokatim.service` and
  **hardened `start.sh`**: it now rebuilds when `frontend/src`/`public` is newer
  than `.next/BUILD_ID` and kills the stale server before starting a fresh one.
- Full audit (all green): 9 pytest pass; alembic at head `fdb43a0e95bc`; every
  app page (/, login, dashboard, matters, contacts, calendar, intake, billing,
  reports, assistant, templates, settings, portal) returns 200; all 11 JS/CSS
  chunks referenced by /dashboard load 200; /api reports/dashboard + analytics,
  matters, invoices, time-entries, team, intake, templates all 200 with a real
  token; public intake page (/apliko/{token}) 200 + its public API OK; ICS feed
  200; Caddy HTTPS 200; containers healthy; avokatim.service + backup timer
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
  `avokatim-backup.timer` (03:00, enabled); key at `~/.config/avokatim/backup.key`.
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
  `~/.cursor/projects/home-kllosha-AvokatIM/canvases/krahasimi-i-plote-aplikacionit.canvas.tsx`.
- Scores: Clio 24/27, Smokeball 21.5/27, MyCase 20/27, AvokatIM 16.5/27.
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
  `~/.cursor/projects/home-kllosha-AvokatIM/canvases/dashboard-krahasimi.canvas.tsx`.
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
- Done: `avokatim.service` (systemd user unit, enabled) so the stack starts on boot;
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
