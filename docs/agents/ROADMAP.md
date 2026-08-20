# ROADMAP — vision, phases, backlog

> The owner decides priorities; agents propose. Keep this current: move items to
> "Done" (with date) or into STATE.md when completed.

## Vision

A platform where one lawyer works with the capacity of a whole firm — from case
intake to full processing, eventually assisting in court itself.
Target: competitive with the global legal-tech
standard, multi-jurisdictional (XK active; GB, CN, INTL prepared).

## Phase 1 — Solo lawyer MVP  ✅ (2026-07-06)

Everything in STATE.md "What exists and works".

## Phase 2 — Hardening & daily-use polish (current)

- [x] Backups ✅ (2026-07-07): `backup.sh` + daily systemd timer, AES-256
      encrypted, retention 14, restore-tested. Key must be copied off-machine.
- [x] Real legal corpus ✅ (2026-07-08): 9 laws (~4,000 article chunks) loaded
      from Gazeta Zyrtare via `backend/scripts/import_gzk.py`; RAG citation
      quality verified on real questions (LPK appeals, Labor Law leave).
      More laws: extend the script's LAWS list and re-run.
- [x] Verify OCR end-to-end on host ✅ (2026-07-07): tesseract 5.5.2 +
      sqi/eng/chi_sim installed; synthetic Albanian scanned image and image-only
      PDF both OCR correctly (diacritics ë/ç intact).
- [ ] Local LLM option in production: configure Ollama/vLLM endpoint, quality-test
      "Ava" against DeepSeek on Albanian legal questions. (Checked 2026-07-07:
      ollama binary present but no models/service and no GPU tooling on host —
      CPU inference would be slow; needs owner decision on model/hardware.)
- [x] Multilingual legal corpus ✅ (2026-07-16): official gazette texts in
      sq/sr/tr/bs/en (`import_gzk.py --lang`), language-aware retrieval, Ava
      cites the official text in the user's language.
- [x] Email/notification channel for approaching deadlines ✅ (2026-07-07):
      hourly reminder loop mails responsible lawyer per remind_days_before,
      Redis-deduped. Needs SMTP_* in backend/.env to activate.
- [x] Dashboard upgrade P1 ✅ (2026-07-07): "Today" agenda, A/R aging buckets,
      6-month worked-hours + billed-revenue trend, global quick timer in sidebar.
- [x] Dashboard upgrade P2 ✅ (2026-07-07): /reports analytics page with
      utilization, realization, collection, intake funnel by source,
      profitability by practice area; hours target in Settings.
- [x] Public domain + real TLS ✅ (2026-07-11): https://avokatiim.ai via
      Cloudflare Tunnel (`avokatim-tunnel.service`); :8443 stays self-signed
      for LAN only.

## Phase 3 — Multi-lawyer / law firms

- [x] Multi-user + roles (admin/lawyer/staff) inside a tenant ✅ (2026-07-07):
      Settings → Team (add member, change role, deactivate); matter assignment
      via responsible lawyer select on the matter Overview.
- [x] Finer permissions ✅ (2026-07-08): per-matter visibility (`restricted` +
      matter members, enforced across list/deadlines/ICS/agenda) and document
      approval workflow (draft → review by partner → approved/changes requested).
- [x] Data migration importer ✅ (2026-07-08): CSV import for contacts and
      matters in Settings, with downloadable templates.
- [x] Fiscal invoices ✅ (2026-07-08): firm NUI/VAT/address in Settings,
      default VAT 18% applied to invoices (vat_amount/total_with_vat shown).
- [x] Firm-level reporting ✅ (2026-07-07): per-lawyer table on /reports (open
      matters, MTD billable hours vs target, utilization); shows when >1 member.

## Competitive gaps (from 2026-07-07 full-app analysis vs Clio/Smokeball/MyCase)

Priority before the law-firm pilot:
- [x] AI deadline extraction from court documents ✅ (2026-07-07): button on any
      document with text → Ava proposes deadlines (date, legal basis,
      confidence), lawyer accepts selected ones.
- [x] Calendar sync via ICS subscription feed ✅ (2026-07-07): signed-token URL
      in Settings, works with Google/Outlook/phone.

Base competitiveness:
- [x] E-signature flow in client portal ✅ (2026-07-07): typed-name signature
      bound to document SHA-256 + IP + timestamp, audit-logged.
      ✅ (2026-07-08) Certificate of Completion PDF per signed document.
      Qualified signatures (Law 08/L-022 art. 32): integrate a licensed QTSP
      (Evrotrust or rTrust) — researched, see DECISIONS D-007; next phase.
- [x] Client portal v2 ✅ (2026-07-07): full portal UI at /portal — login,
      matters, two-way messages per matter, signature inbox.
- [x] AI-drafted client status updates ✅ (2026-07-07): button on matter AI tab,
      send straight to portal messages or copy.

Long-term differentiation:
- [~] Kosovo template library: 12 practice templates seeded (2026-07-08) —
      lawsuits (civil/labor/administrative), objection, appeal, PoA, demand
      letter, NDA, service + employment contracts, legal opinion, DD checklist.
      Still to grow with the pilot firm's own precedents (our answer to
      Smokeball's 20k form library — nobody has this for XK).
- [x] Local payment tracking ✅ (2026-07-07): paid_on + payment_reference on
      invoices, entered when marking paid. (Local processor integration later.)
- [x] PWA ✅ (2026-07-07): manifest + icons, installable. Push notifications ✅
      same day: service worker + VAPID web-push, per-device opt-in in Settings,
      wired into the deadline reminder loop.
- [x] Public intake form link ✅ (2026-07-07): /apliko/{token} public page,
      feeds intake funnel with source=web; link in Settings.

## Competitive gaps (2026-07-12 internet review — marketplace/citizen era)

Sources: 2026 legal-tech trend reports (Clio/ABA, NetDocuments, GOLT), legal
marketplace build guides (license verification, reviews), consumer legal apps
(Legaliam, Vikk AI, Start My Claim, Justivo, Legali). Canvas:
`mungesat-kunder-tregut-2026`.

P1 — trust layer (before promoting the directory publicly):
- [x] OAK bar-license verification ✅ (2026-07-12): license on profile →
      pending → superadmin approves against the public OAK registry →
      "Verified" badge; unverified lawyers get no cases. ONK matching for
      notaries added 2026-07-13.
- [x] Client reviews ✅ (2026-07-12): only citizens with a claimed case can
      review (communication/responsiveness, never legal outcome); average in
      directory + ranking.
- [x] Lawyer onboarding nudge ✅ (2026-07-12): dashboard banner when the public
      profile is inactive (first real user got stuck here). Full onboarding
      wizard `/onboarding` + welcome/nudge emails ✅ (2026-07-13).

P2 — demand growth:
- [x] Consultation booking ✅ (2026-07-12): slots on lawyer profile, citizens
      book; Stripe payment for paid consults ✅ (2026-07-13); notary bookings
      with prepared-dossier attachment ✅ (2026-07-13).
- [x] Public deadline calculator ✅ (2026-07-12): `/afatet`.
- [x] Citizen document automation ✅ (2026-07-12): `/dokumentet` interview →
      letters/complaints + notary pack (2026-07-13).
- [x] Transparent pricing ✅ (2026-07-12): consult fee on public profiles.

P3 — office differentiation:
- [ ] Passive time capture (suggest entries from activity).
- [x] Voice input for Ava ✅ (2026-07-13): faster-whisper STT + Piper sq TTS,
      SOS hands-free audio counseling + evidence recording.
- [x] Agentic intake triage ✅ (2026-07-13): Ava-intake `structure-case`
      prefills the citizen case form; deep research + clause assist + document
      AI summaries on the lawyer side.
- [ ] Public API tokens for integrations.

Growth operations (running):
- [x] Automated outreach ✅ (2026-07-14): `avokatim-outreach.timer`, up to 25
      emails/day (D-069 cap, dedicated Resend sender) to OAK lawyers,
      auto-switches to ONK notaries when done.
- [x] Notaries as second paying profession ✅ (2026-07-13): signup choice,
      `/per-noteret`, ONK verification, adapted dashboard, no marketplace.
- [x] Self-hosted analytics ✅ (2026-07-13): Umami at stats.avokatiim.ai.

## Phase 4 — More jurisdictions

- [x] **DE (Germany) ✅ (2026-08-01, D-034)** — one codebase, jurisdiction
      profiles as data (`app/jurisdictions.py`), host `de.avokatiim.ai`,
      German locale (7th), 58-law federal corpus, DE seeds (holidays,
      ZPO/StPO/KSchG deadlines, RVG tariff, templates), RDG-safe DE Ava,
      BRAV-assisted manual verification. Public launch gated by
      `docs/legal/DE-LAUNCH-GATE.md` (EU server, GDPR Art. 27 rep, EU LLM,
      German-lawyer review of AGB/Datenschutz/Impressum).
- [x] DE corpus wave 2 ✅ (2026-08-01): +20 citizen-frequency federal acts
      (BEEG, MuSchG, GewSchG, BerHG, GKG/FamGKG, UWG, SGB IV/VII/VIII/IX/X,
      WoGG, BAföG, PflVG, FeV, ZVG…) + DSGVO in German from EUR-Lex/CELLAR
      (`import_dsgvo.py`) → 79 acts / 16,435 chunks.
- [x] Landesrecht pilot ✅ (2026-08-01, D-035): `region` dimension
      (Holiday/LegalCorpusDoc/Tenant), Land holidays 2026–27 in the deadline
      engine, NRW + Bayern corpus (20 acts / ~2,900 chunks) via
      `import_de_landesrecht.py`, region-aware retrieval + Ava Bundesland
      picker.
- [ ] Landesrecht rollout: remaining 14 Länder. Blocker: their portals
      (landesrecht-bw.de, gesetze.berlin.de, hessenrecht…) are juris SPAs
      with token-authenticated internal APIs — needs a headless-browser
      adapter or a juris data agreement (see LESSONS #1). Priority by
      population: BW, NI, HE, RP, SN…
- [x] Exact calendar-month deadline arithmetic (§ 222 ZPO, §§ 187–188 BGB):
      `day_type="months"` in the engine, DE month rules converted (D-036).
- [ ] DE deepening: BRAV scraper when the portal stabilizes, German outreach
      campaign, SOS/notary legal review.
- [x] DE market-standard gaps ✅ (2026-08-01, D-037): full RVG engine
      (§ 13 table + VV as data, fee-calc APIs, /rvg public calculator),
      E-Rechnung (ZUGFeRD/Factur-X hybrid PDF/A-3b for all DE invoices,
      XML endpoint), Rechtsschutzversicherung in the case flow +
      Deckungsanfrage template, DATEV EXTF export, **local LLM for DE**
      (Ollama gemma3:27b, launch-gate item 3 closed).
- [ ] beA integration (BRAK KSW-Schnittstelle) — registration guide +
      draft email ready (`docs/legal/BEA-KSW-REGISTRATION.md`); owner sends
      the BRAK email, module (`services/bea/`, Java sidecar around the
      KSW-Toolkit) starts once test access is granted.
- [ ] GKG court-fee table for a full Prozesskostenrechner (optional D-037
      leftover; RA-MICRO standard).
- [ ] Retrieval quality: hybrid search (pgvector + Postgres full-text/BM25)
      or a stronger embedding model (e.g. multilingual-e5) with full
      re-embed — colloquial German questions sometimes miss the right §
      (e.g. DSGVO Art. 15) even though it's in the corpus.
- [ ] DE case law (BGH/BAG/BVerfG via rechtsprechung-im-internet.de) — see
      proposal in JOURNAL 2026-08-01c.
## DE advancement wave (2026-08-01 market analysis — owner request)

> Grounding: Wolters Kluwer Benchmark 2026 (63% of German firms already use
> AI; #1 blockers: DSGVO 38.9%, liability; 49.5% bill less than half their
> time; 70% name client acquisition as top concern; only 22% use intake
> tools, 20% automated time capture), BRAK (167,547 lawyers 1.1.2026, >75%
> of practices are solo), BRAK KI-Leitfaden (Dec 2024), zivilgerichtliches
> Online-Verfahren live since 15.4.2026 (18 Amtsgerichte, payment claims
> ≤ €10k + air-passenger rights, service.justiz.de, filing via beA,
> XJustiz planned), eAkte mandatory since 1.1.2026 (opt-outs to 2027),
> advocado charges lawyers a 33.92% infrastructure fee (we charge 0%).

Tier A — differentiators we can build now (no external dependency):
- [ ] **Online-Verfahren assistant**: from a matter (or citizen case),
      generate the Klageschrift for payment claims ≤ €10k / Fluggastrechte
      in the format the pilot courts accept, prefill service.justiz.de
      inputs, prepare for XJustiz structured filing when the lawyer input
      system ships. Brand-new procedure (4/2026) — no incumbent owns it yet.
- [ ] **Prozesskostenrechner** = RVG (done) + GKG court-fee table + cost
      risk per instance (who pays what if you win/lose). Public page → SEO
      magnet ("Was kostet ein Prozess?"); internal: quote per matter.
- [ ] **Recherche depth**: hybrid BM25+vector retrieval, case-law corpus
      (BGH/BAG/BVerfG via rechtsprechung-im-internet.de) with citation in
      Ava answers. Research is the #1 AI use case in DE firms (90.9%).
- [ ] **Back-office agents** (the 49.5% billable-time pain): email→Akte
      routing with suggested filing, incoming Bescheid/Urteil scan →
      deadline suggestion into the Fristen engine, invoice chasing
      (Mahnung) drafts. Extends the existing activity→time-entry suggester.
- [ ] **BRAK KI-Leitfaden compliance pack**: per-office AI-usage register,
      human-review checkpoints on AI drafts, output logging, DSGVO
      processing-record template. Sell compliance as a feature ("BRAK-
      Leitfaden-konform"), it neutralizes the #1 adoption blocker.

Tier B — growth channels:
- [ ] Marketplace positioning vs advocado/anwalt.de: "0% commission, flat
      subscription" front and center on /per-avokatet DE; Rechtstipps-style
      content pages generated from our corpus (with lawyer review workflow)
      to chase anwalt.de's SEO moat.
- [ ] Rechtsschutzversicherung deepening: per-insurer Deckungsanfrage
      submission formats (ARAG, Allianz, HUK…), coverage-status tracking on
      the case, insurer as acquisition channel.
- [ ] beA (waiting on BRAK KSW access — guide ready) + XJustiz export:
      together they complete the e-filing story the Online-Verfahren opens.

Tier C — strategic (6+ months):
- [ ] "Legal Operating System" consolidation play: IMAP/e-mail ingest,
      CalDAV calendar sync, Steuerberater handoff beyond DATEV EXTF.
- [ ] German legal fine-tune / EU-hosted LLM + eval harness ("KI, die Ihre
      Kanzlei nie verlässt") — builds on gemma3:27b local baseline.
- [ ] EU hosting + GDPR Art. 27 representative (launch-gate items 1–2) —
      precondition for any public marketing.

- [ ] GB seeds (deadline rules, holidays, templates, corpus).
- [ ] CN seeds; INTL (arbitration etc.).
- [ ] Per-jurisdiction template/document language handling.

## Phase 5 — Courtroom assistance (long-term goal)

- [ ] Hearing preparation packs: chronology, arguments, counterargument prediction
      with citations.
- [ ] Live/session assistance mode (fast retrieval over the matter + corpus,
      possibly voice; must work with a local LLM for confidentiality).

## Ideas parking lot

- Client intake form shared as a public link.
- Court calendar/e-filing integrations where Kosovo infrastructure allows.
- Fine-tuned Albanian legal embedding model when corpus is large enough.
