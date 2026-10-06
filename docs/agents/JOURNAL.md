## 2026-10-06 — ops_inbox_hygiene: prefiks ESP numerik (em1.) nuk shpëtonte filtrin (Halim; handoff sekretari 20261006-021113)

- **Problemi:** `_BULK_DOMAIN_PREFIX` krahasonte me `startswith` literal, ndaj domain-i
  `em1.cloudflare.com` (prefiks `em1.`) nuk kapet nga `em.` → sender-a marketing
  `Cloudflare <em@em1.cloudflare.com>` promovohej në `personale` dhe frynte
  `needs_attention`. Përsëritje e katërt e të njëjtit model (chess.com 24.09,
  engage.canva 05.10, tani em1.cloudflare 06.10).
- **Ndryshimi:** `_is_bulk_domain_prefix()` e re — provon `startswith` literal, pastaj
  heq shifrat nga label-i i parë (`rstrip("0123456789")`) dhe riprovon; `em1./em2./em3. → em.`,
  `mail2. → mail.`. `_final_bucket` tani e thërret këtë. Vetëm klasifikim; skripti mbetet read-only.
- **Provat:** import i drejtpërdrejtë → `em1.cloudflare.com -> tjera`, `engage.canva.com -> tjera`,
  `mail2.mailchimp.com -> tjera`; `gmail.com`/`somefirm.com -> personale` (pa regres); `py_compile` OK.
- **Pse:** ndal sinjalin e rremë në rreshtin e triazhit (RAPORTIMI.md, D-142).

## 2026-10-05 — ops_inbox_hygiene: heuristika e domain-it bulk (Halim; handoff-e sekretari 20261005-085100 / 2026-10-05T103156Z)

- **Problemi:** `_final_bucket` promovonte në `personale` çdo sender "tjera" me display-name
  kur lokal-pjesa s'ishte në `_BULK_LOCAL`. Sender-a marketing/ESP me lokal-pjesë të panjohur
  (p.sh. `canvadesignschool@engage.canva.com`) binin në `personale` → sinjal i rremë
  "kërkon vëmendje". Përsëritje e tretë (edhe chess.com 2026-09-24).
- **Ndryshimi:** shtuar `_BULK_DOMAIN` (domain-e ESP të njohura) + `_BULK_DOMAIN_PREFIX`
  (`engage.`, `email.`, `mail.`, `news.`, `marketing.`, `notify.`, `info.`, `em.`, `e2.`, `cmail`)
  + `_domain()`; `_final_bucket` tani kërkon që AS lokal-pjesa AS domain-i të mos jenë bulk.
  Vetëm logjikë klasifikimi; skripti mbetet read-only.
- **Provat:** test njësi `python3 -c` → `engage.canva.com -> tjera` (jo `personale`),
  `gmail.com -> personale`, `news@someco.org -> reklama`; xhirim i gjallë `--max 300`:
  buckets `personale: 0`, `reklama: 9`, `tjera: 1`, t_counts {t0:10, t1:20, t2:0}.
- **Pse:** ndal sinjalin e rremë në rreshtin e triazhit (burimi: RAPORTIMI.md, D-142).

## 2026-10-05 — ops_inbox_hygiene: mapimi bucket→T bëhet machine-readable (Halim; handoff 2026-10-05T012027Z)

- **Problemi:** rreshti i ledger-it të triazhit (t0..t3) nxirrej nga kujtesa e modelit;
  bucket-i `platforma` u klasifikua gabimisht T3 (03.10), T0 (04.10) e T0 (05.10) — rast i
  tretë edhe pas rregullit vetëm-dokument në `sekretari/AGENTS.md` (handoff 20261004-190032).
- **Ndryshimi:** `backend/scripts/ops_inbox_hygiene.py` tani eksporton `bucket_to_t`
  (BUCKET_TO_T) + `t_counts` ({t0: reklama+tjera, t1: platforma, t2: 0,
  t_allowlist_pending: financiare+personale, matter}) në JSON-in e snapshot-it. Vetëm fusha
  të shtuara; skripti mbetet read-only. U përditësua edhe rregulli te `sekretari/AGENTS.md`
  (lexo `t_counts`, mos e nxirr mapimin nga kujtesa).
- **Provat:** `python3 -m py_compile` OK; `ops_inbox_hygiene.py --max 5` → buckets
  {reklama:2, platforma:3}, t_counts {t0:2, t1:3, t2:0, t_allowlist_pending:0}.
- **Pse:** heq varësinë e ledger-it nga kujtesa e modelit (burimi kanonik: `RAPORTIMI.md` §Mapimi, D-142).
## 2026-10-03 — ops_watchdog: placeholder-i i tokenit Telegram zgjidhet nga mjedisi (Halim; PO i Kllosha-s 20:43)

- **Problemi:** `channels.telegram.botToken` në `~/.openclaw/openclaw.json` është placeholder `${TELEGRAM_BOT_TOKEN}`.
  Gateway-i e zgjidh nga mjedisi (len=46), por `ops_watchdog._telegram_creds()` lexonte **literalin** (len=21)
  → `api.telegram/getMe` kthente **HTTP 404** → alarmet e watchdog-ut binin në **email në heshtje** (~20 alarma, uid 17023–17049).
- **Ndryshimi:** `_zgjero_env()` zgjeron `${VAR}`/`$VAR` nga `os.environ`; `_telegram_creds()` e përdor për tokenin.
  Skedarë: `backend/scripts/ops_watchdog.py` (+ `import os`/`re`), `backend/tests/test_ops_mail_reliability.py` (+2 teste).
- **Provat:** placeholder → len 46 · `_telegram_creds()` → chat 5958503553, token_len 46 · **live `getMe` → HTTP 200** (`HalimKlloshaBot`) · `pytest tests/test_ops_mail_reliability.py` → **13/13** (venv-i i projektit).
- **Kufijtë:** ndryshim vetëm në lexuesin e kredencialeve; pa prekje kontejnerësh/units; tokeni nuk del nga makina (as në log, as në commit).

## 2026-09-29 — Roster-health: EdaS në PAUZË → ndal çaktivizimin automatik të cron-it (Halim)

- **Problemi (i zbuluar nga alarmi i automations, D-138):** automation-i
  `avokatim-roster-health` (14a674c6) u çaktivizua vetë pas **10 dështimeve
  radhazi**. Shkaku: `scripts/ops_roster_health.py` vëzhgonte
  `edas.service`/`edas-frontend.service`, të cilat **nuk ekzistojnë më si
  units** në këtë host (EdAS në PAUZË; edhe monitori i flotës i hoqi më 21.09).
  Çdo kontroll → `unresolved: EdaS` → `exit 1` → cron "error" ×10 → auto-disable.
- **Rregullimi:** `EdaS` në `PROJECTS` mori flag-un `"paused": True`; `check()`
  i kalon projektet e pauzuara (shtohen te OK, pa alarm, pa restart). Kthimi:
  hiq `paused` (ose vendos `False`) kur EdAS rikthehet si shërbim.
- **Verified:** `.venv/bin/python scripts/ops_roster_health.py --status` →
  "✅ Të gjitha projektet aktive", `exit 0`; automation-i u riaktivizua
  (`openclaw automations enable 14a674c6-…`).
- **Left open:** EdAS mbetet i pauzuar — nëse rikthehet, rivendos units + hiq
  `paused`, përndryshe mbetet i pamonitoruar me qëllim.

## 2026-09-24 — PAUZA e trakës DE (urdhër i Klloshës; koordinim Halim + agjenti-cursor)

- **Urdhri (Kllosha, Cursor 08:39):** "pauzone avokatin gjerman por avokati i
  kosovës duhet vazhduar punën" — në relacion me H-15 (rekomandimi PO i Halimit
  23.09). Verdikti: **H-15 PEZULL** — GEX44 + Prighter (219 €/muaj) NUK blihen.
- **Matja e konsumit DE para pauzës (agjenti-cursor):** DB `legal_corpus` DE =
  16,906 docs / 284,452 chunks / ~940 MB (XK: 3,086 / 68,990 / ~267 MB);
  `avokatim-corpus.timer` çdo natë 01:30 (23.09→24.09: 10 vendime të reja, 12 s,
  244 MB peak + embeddings në GPU); pyetjet DE → DeepSeek (trafik beta ≈ 0);
  serveri H-15 i papaguar — 0 kosto e re.
- **Ekzekutimi:** `systemctl --user disable --now avokatim-corpus.timer`
  (i kthyeshëm me `enable --now`; njësitë mbeten në disk). **Të dhënat DE NUK
  fshihen.** Banner PAUZE te `docs/legal/DE-LAUNCH-GATE.md` (commit `073078f`,
  Halimi) + `docs/legal/EU-SERVER-PLAN.md` (ky commit). Sentineli s'e vëzhgon
  corpus-timer-in (vetëm avokatim.service/tunnel/frontend + kontejnerët) — pa
  alarm të rremë.
- **XK zero prekje:** backend/frontend/tunnel aktivë; outreach (vetëm noterë XK),
  backup, watchdog, secscan, notify-watch — të gjithë timers aktivë.
- **Kushti i rifillimit (Halimi):** përdorues realë DE pa stack-un e përshtatshëm
  → porta rihapet me PO të ri të Klloshës. Handoff-et: `20260924-064328`.

## 2026-09-18 — Segmenti #1 i aktivizimit: email te 7 avokatet e dukhmë e te paverifikuar (Halim, PO 15:50)
- Objektivi (plani i Halimit, `~/.openclaw/workspace/memory/plans/2026-09-18-avokatim-aktivizim.md`):
  kthimi i bazës në vlerë reale — verifikimi = porta e vlerës (faqja `/avokatet`
  shfaq vetëm të verifikuarit). Segmenti #1: të dukhmët pa verifikim, 20 → 27.
- **Marrësit nga DB** (`lawyer_profiles.is_visible = true AND verification_status
  <> 'verified'` → 7), join `users` për email+emër; përjashtimet e pronarit nuk u
  prekën. Lista: `data/evidence/paverifikuar-2026-09-18/recipients-paverifikuar.csv`.
- **Dërguar 7/7, 0 dështime** (Gmail SMTP, i njëjti identitet si demo-ja) me
  `backend/scripts/send_paverifikuar_email.py` (NEW: halim_guard + `_is_test_recipient`
  + dedup për tag + ledger-row). Ledger `data/ops/paverifikuar_sent.csv`, tag
  `paverifikuar-2026-09-18`. Subjekti: "Profili juaj në AvokatIM — një hap larg
  dukshmërisë".
- Guard: `allow / act_and_notify`; audit `email paverifikimi derguar` ok.
  Baseline matjeje: **20** të verifikuar+e dukhmë (`baseline-meta.json`); objektiv 27.
- **Mësim:** para çdo dërgimi të ri kontrollo TË TRE ledger-ët (`reactivation_sent.csv`,
  `demo_email_sent.csv`, `paverifikuar_sent.csv`): të 7 kishin marrë demo-n po
  atë ditë, 3 prej tyre edhe ri-aktivizimin (deri në 3 email-e/ditë). Treguar
  pronarit në raport.

## 2026-09-19 — Kanali agjent ↔ Halim u standardizua (chat-i main i Halimit — aty ku sheh Kllosha)
- Kërkesë e Klloshës: "si komunikon Cursor-i me Halimin te TotoTrading, që e
  shoh unë — implemento të njëjtin këtu". Provë e parë E GABUAR: handoff-et
  shfaqen te Halim Live :8795, por Kllosha NUK e shikon atë panel — ai lexon
  dhe ndërvepron te **http://127.0.0.1:18789/chat/main** (gateway-i OpenClaw).
- Kanali i saktë (u verifikua live, mesazh + përgjigje e Halimit në chat/main
  brenda 30 sek): `openclaw agent --session-key "agent:main:main" -m
  "[cursor-fable5 / AvokatIM] …"` — turn i vërtetë në sesionin main; ose
  `halim_events.py wake` për event më të lehtë. **AGENTS.md §4c** (korrigjuar):
  1) mesazh në chat/main = kanali primar që sheh pronari; 2) handoff-et
  (`handoff_hap`/`handoff.py`) = dosja e strukturuar async (referohu me id në
  mesazh); 3) `notify_ops` = vetëm ping Telegram (sesion i izoluar — pronari
  s'e sheh në chat/main). Hapi 0 i sesionit: `handoff_list(to=cursor-fable5)`.
- Përmes kanalit të ri Halimi u përgjigj menjëherë: "gjëja e dytë" që pret
  PO-në e Klloshës është **Toto** (vendimi mbi ekspozimin live pas
  walk-forward-it pa edge), jo diçka e AvokatIM. Për prezentimin e dytë
  Halimi u pajtua me rekomandimin tim: dërgimi të martën 22.09 paradite,
  tag `prezentim2-2026-09-22`, 21 marrës — dërgimi pret "dërgoji" nga Kllosha.

## 2026-09-18 — Mbyllje administrative: fushata e demo-email-it (sesion paralel) u dokumentua dhe u commit-ua
- Sesioni paralel i pasdites (PO i Klloshës 14:10 dhe 15:27) dërgoi email-in
  "Si funksionon AvokatIM në 4 hapa — një demonstrim i shkurtër" (HTML me 3
  ilustrime inline CID + alternativë tekst, sq) te avokatët me profil të
  dukshëm në Treg, në dy valë: 15:00 → 23 ok; pastaj 7 ok te të mbeturit
  (`_build_existing_lawyers.py`, përjashtime: Kllosha, Valtida Shukriu, kushdo
  tashmë `ok` në ledger). Total **30 ok / 0 fail**, tag `demo-2026-09-18`.
- Siguria e skriptit `send_demo_email.py`: kontroll halim_guard para SMTP-së,
  refuzim i marrësve test (`_is_test_recipient`), dedup për tag në ledger-in
  `data/ops/demo_email_sent.csv`, ledger-row për çdo marrës. Evidenca e plotë
  (HTML/PNG mockups, listat, rezultatet JSON) te `data/evidence/demo-2026-09-18/`.
- Ai sesion i la 3 skriptet ndihmëse të pa-commit-uara dhe pa JOURNAL/COMMS —
  u mbyllën këtu (rreshti COMMS u shtua; skriptet u commit-uan). Kujdes për
  dërgime të ardhshme: disa marrës morën të njëjtën ditë edhe email-in e
  ri-aktivizimit — kontrollo TË DY ledger-ët para çdo dërgimi të ri
  (`data/reactivation_sent.csv` + `data/ops/demo_email_sent.csv`).

## 2026-09-18 — PO i pronarit: fushata Lane B u dërgua; Buzuku u zgjidh; riparimi me grounding burimor (+13pp në gate-in XK)
- Pronari dha PO ("po vazhdo") për tri vendimet e hapura të auditimit.
- **Fushata e ri-aktivizimit (Lane B)**: 23 email-e personale u dërguan me
  `send_email` te llogaritë aktive me 0 lëndë (jo-test, pas pezullimit të
  dublikatës) — log dedup `data/reactivation_sent.csv`; Halimi u njoftua me
  `notify_ops` (përgjigjet trajtohen si Lane B normale). Llogaritë >36 ditë
  nuk kapen nga sekuenca automatike 3/7/30, s'ka dërgim të dyfishtë.
- **Dublikata "Avokatura Buzuku"**: u mbajt `e202a0af` (av.labinotbuzuku@gmail.com —
  email i verifikuar, 7 veprime auditimi); `e3f008dc` (buzukulabinot@gmail.com,
  i pa-verifikuar, 1 veprim) u pezullua me shënim te `billing_notes`.
- **Riparimi i citimeve me grounding burimor** (`_repair_sources` te
  `citation_check.py`): raundi i riparimit tani merr TEKSTIN REAL të nenit të
  cituar (chunk-u i seksionit) + "citati gjendet në të vërtetë te neni X"
  (kërkim me fjalë të rralla + `_quote_coverage` ≥0.6 mbi doc-ët e ligjit) —
  modeli korrigjon numrin në vend që ta fshijë pohimin.
- **Aliaset e emrave të lakuar** (`XK_STATUTE_NAME_REFS` + `_norm_law_name`):
  "nenit 71 të Ligjit të Punës" / "Kodit të Procedurës Penale të Kosovës" tani
  zgjidhen te ligji i saktë (normalizim: diakritikë, lakime ligjit/kodit→ligj/kod,
  stopwords; prova me prefikse zvogëluese + riparashtim i kokës "ligj" që
  regex-i i ekstraktimit ia heq). +2 teste (399 pytest total, të gjitha kalojnë).
- **Gate-i XK (run 5 → 6)**: 73.1% → 81.8% (grounding) → **82.8%** (aliaset;
  24/29 ✓+≈, 3 law_found, 2 unverified). #18 (Ligji i Punës) tani 4/4 ✓.
  Mbetjet janë halucinacione të vërteta të modelit (p.sh. #3: neni 371/374 LMD
  me numërim të vjetër jugosllav — neni ekziston, përmbajtja e cituar jo) që
  verifikuesi i kap saktë. DE mbetet 100% PASS. Riparimi mbetet OFF by default
  (latencë 24–117s shtesë/rast); gate-i 95% për XK mbetet i hapur si synim —
  hapi tjetër me leverage: citime të ankoruara në retrieval (modeli lejohet të
  citojë vetëm nenet që i ktheu RAG-u).

## 2026-09-18 — Njoftimet e rasteve provë u bllokuan në të dyja rrugët (Halim, PO i Klloshës)
- Konteksti: ankesa e Av. Valtida Shukriu (18.09 11:32) — 5 email-e "Rast i ri"
  brenda 2 orëve për 0 raste në Treg. Diagnoza (raporti
  `avokatim-rrjedha-emails-2026-09-18.md`) nxori shkakun: `full_simulation.py`
  xhironte mbi API-n live dhe `citizen_create_case`/`citizen_sos` njoftonin
  12–14 avokatë REALË për raste sintetike që fshiheshin menjëherë (69 njoftime
  më 18.09; i njëjti model më 01.09).
- Zbatimi (3 shtresa): (1) porta në kërkesë — `_is_test_recipient(citizen.email)`
  para fan-out-it të matching-ut dhe të SOS-it; (2) mbrojtje në thellësi brenda
  `_notify_matching_lawyers` / `_notify_on_duty_lawyers` (rast i fshirë ose
  qytetar test → log + kthim pa njoftim); (3) `scripts/sim_guard.py` — harness-i
  refuzon bazën e prodhimit pa `--allow-prod` (mjedis prove me
  `AVOKATIM_SIM_BASE_URL`); i njëjti portë edhe te `de_/notary_simulation.py`.
- Provat: `full_simulation.py --allow-prod` mbi prodhim → 188 PASS / 0 FAIL,
  **0 njoftime të reja** (2342 → 2342; 69 → 69 për "përputhet me profilin"),
  ndërsa `audit_logs` regjistroi 3 raste + 2 SOS të sim-it; testi i portës së
  thellë (thirrje direkte e `_notify_*`) → delta 0; pytest 395 testet (1 dështim
  flaky i `test_voice`, kalon në riprovim); `/api/health` 200, frontend 200.
- Watchdog-u i postës (`avokatim-watchdog`): audituar — nuk prek fare
  kontejnerë/DB (as `pg_isready`); ndalja e `avokatim-db` vinte nga ExecStop i
  `avokatim.service` (`docker compose stop` ndal TË GJITHË stakun). U riaktivizua
  pasi u provua; shënimi te docstring-u i skriptit.
- Përgjigjja për avokaten u dërgua nga `ops_send_reply.py` (In-Reply-To i
  mesazhit të saj), audituar te `halim_guard`.


- Vazhdimi i planit "Zbatimi i 10 avancimeve" — u mbyllën 8 avancimet e mbetura
  (4–10 + pjesa produkt e #3). Vendimi arkitekturor: **D-067** (shtresa e besimit).
- **Faza 2 — besimi i Ava-s**:
  - Verifier v2 (`services/citation_check.py`): verifikim në nivel citati —
    citatet e thonjëzuara i atribuohen citimit (fjali e njëjtë + `pos` nga
    regex) dhe krahasohen fuzzy (difflib ≥0.85 pas normalizimit) me chunk-ët
    burimorë → statuse verified/approx/law_found/unverified me
    doc_id/chunk_id. Regex-i shqip u shtrëngua ("Ligjit" i lakuar s'kapet më
    si kod; emrat e ligjeve kërkohen me fallback shkurtimi të query-t).
  - Raund riparimi (`repair_citations` + SSE `citation_fix`): 1 re-prompt
    përmes `app/llm/` kur ka unverified; OFF by default
    (`citation_repair_enabled`) — latenca në DeepSeek XK ~2–4 min/rast.
  - Citime të klikueshme: badge-t ✓/≈ hapin modal burimi
    (`citation-source-modal.tsx`; `GET /corpus/chunk/{id}` +
    `/corpus/doc/{id}/first-chunk`); `GET /corpus/search` i ri (hibrid, edhe
    për MCP).
  - "Pyet lëndën": `matter_mode=full` në assistant → `matter_documents_full`
    (gjithë dokumentet e lëndës brenda buxhetit të karaktereve), toggle në
    panelin e assistant-it të lëndës.
  - Eval gate: `scripts/eval_citations.py` + `eval/golden_xk.jsonl` /
    `golden_de.jsonl` (20+20 pyetje), gate (verified+approx)/total ≥95%;
    rresht i ri në playbook-un e AGENTS.md §4. Mësim operacional: eval-i
    duhet nisur me `systemd-run --user` (proceset e shkëputura nga sesioni
    i agjentit vriteshin heshturazi) dhe me sesion të ri DB për rast (një
    lidhje e vrarë mos t'i helmojë rastet e mbetura).
- **Faza 3 — vlera për avokatin**:
  - 3 workflows ekspert si DATA (`seeds/workflow_defs.py`, XK): W-Ankesa,
    W-Konformiteti, W-Provat; `services/workflows.py` + SSE
    `POST /matters/{id}/workflows/{kind}`; rezultati me raport verifikimi
    citimesh, ruhet si Matter note + audit log; 3 butona në faqen e lëndës.
  - AI Auditor natën: `run_file_quality_audit` në `proactive.py` (lëndë pa
    palë kundërshtare / pa dokumente / fatura draft >7 ditë / pa aktivitet
    >30 ditë) — gjetjet në briefing-un e mëngjesit + notification center.
  - MCP server (`scripts/mcp_server.py`, stdio): 6 vegla mbi api_tokens
    (kerko_korpusin, lexo_lenden, lista_e_lendeve, afatet_e_lendes,
    kerko_dokumentet, drafto_memo — vetëm drafto_memo shkruan, kërkon
    read_write); i regjistruar në `~/.cursor/mcp.json`; smoke test OK pas
    restart-it të backend-it.
- **Faza 4 — rritja**:
  - Sekuenca e aktivizimit 3/7/30 (`_check_activation_sequence`): email për
    tenant-ët me 0 lëndë, ×7 gjuhë në i18n.py, dedup me Redis, suppression
    i test-marrësve, rresht në COMMS.md.
  - Checklist onboarding-u në dashboard (obc*: krijo lëndën / ngarko
    dokument / provo Ava-n) mbi `reports/dashboard.onboarding`.
  - Higjiena: kolona `tenants.is_test` (migrimi `c8d9e0f1a2b3`), 9 tenant-ë
    prove të shënjuar, të përjashtuar nga sekuenca + të dukshëm në
    /platform. Draft-et Lane B: 24 llogari të fjetura →
    `data/reaktivizimi-lane-b-2026-09-18.md` — **asgjë s'dërgohet pa PO**.
  - Padia e vogël (`/dokumentet/padia-e-vogel`): wizard 3-hapësh → padi
    zyrtare PDF (template si data `XK_SMALL_CLAIM_TEMPLATE`, LPK 484–491,
    kufiri 500 € i verifikuar në korpus — neni 485.1), taksa 60 €
    (UA 03/2025), gjykata kompetente sipas komunës (`XK_BASIC_COURTS`,
    37 komuna → 7 gjykata + degët), udhëzim dorëzimi + CTA marketplace;
    endpoint-e të reja `GET /small-claims/meta`,
    `POST /small-claims/generate` (rate-limited); ×7 gjuhë; testuar
    end-to-end në browser.
- Verifikimi: pytest **397/397** (27 teste të reja: verifier v2, workflows,
  MCP, padia e vogël, renditja e dokumenteve), isolation_check ALL PASS,
  saas_check ALL PASS, **full_simulation 188/188 PASS**, build frontend OK +
  asset 200, health OK; workflow "appeal" i provuar live me tenant provizor
  (SSE plan→step→result→done, nota u ruajt).
- **Rezultatet e eval gate-it** (4 runs; DE 1 run):
  - **DE: PASS 79/79 = 100%.**
  - **XK: FAIL ~65–73%** (3 runs të plota; gate 95%). Gjatë runs u gjetën
    dhe u rregulluan 3 defekte reale: (1) `_find_docs("KPP")` kapte një
    AKTGJYKIM ("KPPP. nr.284/23") në vend të kodit → alias map
    `XK_STATUTE_REFS` në seeds (KPP→08/L-032/04/L-123, KP/KPRK→06/L-074,
    LPK, LMD, LP, LKA, LFK, LSHT) + renditje bazë > amendament > aktgjykim
    (`_doc_rank`); (2) rasti #12 dështonte me DeepSeek 400 — chunks
    patologjikë të ligjeve të buxhetit (deri 1.6M karaktere tabela anekse)
    e hidhnin prompt-in në 2M tokena → cap mbrojtës 12k karaktere/hit në
    `rag.search_corpus`; (3) prompt-i i Ava-s u shtrëngua: thonjëza vetëm
    për tekst të kopjuar nga materialet, cito kodet AKTUALE (06/L-074,
    08/L-032), jo kodet e UNMIK-ut.
  - Dështimet e mbetura XK janë halucinacione reale që gate-i i kap saktë:
    modeli citon numërimin e LMD-së së VJETËR jugosllave (p.sh. "neni 173/
    174" të ligjit '78 me tekst që në 04/L-077 i takon nenit 154/155) dhe
    raundi i riparimit s'i heq gjithmonë. Follow-up në ROADMAP: riparimi të
    marrë edhe tekstet burimore të neneve, jo vetëm listën e dështimeve.
- Mësime operacionale (LESSONS): (1) evals të gjata NIS me `systemd-run
  --user` — proceset e shkëputura nga sesioni i agjentit vriten heshtazi;
  (2) `systemctl --user restart avokatim` NDAL edhe kontejnerët (Postgres!)
  dhe, kur stop-i kalon timeout-in (SIGABRT), ndez responder-in e
  incidenteve të Halimit që mund ta rindezë stack-un sërish më vonë — mos
  planifiko restart me eval/simulim në vazhdim.
- Vendime të hapura për pronarin: (a) PO për draft-et Lane B; (b) dublikata
  Buzuku; (c) ndezja default e riparimit të citimeve pas shqyrtimit të
  latencës.

## 2026-09-18 — Zbatimi i avancimeve, Faza 1: siguria (Cursor / Fable 5)
- Konteksti: pronari miratoi zbatimin e 10 avancimeve nga auditimi i sotëm
  (plani "Zbatimi i 10 avancimeve"). Kjo është Faza 1 (avancimet 1–2).
- **Patch-et e varësive** (gjetja SEC-1): pip — aiohttp 3.14.3, cryptography
  50.0.1, pypdf 6.19, setuptools 84, pip 26.2.1, torch 2.14.0+cu130 (2.12.1
  e kapte setuptools<82, prandaj ngritja ishte e detyruar; CUDA + embeddings
  verifikuar pas ngritjes), weasyprint 70 (advisory i ri, i dalë pas skanimit
  të 14.09). `pip-audit`: **No known vulnerabilities found**. npm: `npm audit
  fix` → 0 vulnerabilitete, Next 16.3.5. Dyshemetë u ngritën në
  requirements.txt (cryptography>=50, pypdf>=6.15, weasyprint>=70).
- **Alarmi i heshtur i skanimit** (gjetja SEC-2): gateway-i OpenClaw tani
  host-on shumë agjentë dhe kthen 400 pa `agentId`. `ops_notify` u rregullua
  (payload + `openclaw_hook_agent_id` në config, default "main" = Halimi).
  Verifikuar live: dërgim provë `sent: True` + run i plotë i
  `security_scan.sh` → "halim notified: True", raporti i pastër.
- **Migrimi RLS** (gjetja SEC-3): revizion i ri `b7c8d9e0f1a2` që ri-ekzekuton
  zbulimin + politikën DEFAULT-OPEN të valës origjinale (a1b2c3d4e5f6) mbi çdo
  tabelë me tenant_id — mbulon 5 tabelat e pambuluara (email_suggestions,
  deadline_suggestions, notifications, passkey_credentials, api_tokens);
  downgrade-i prek vetëm të pesë. `isolation_check.py`: **ALL PASS**.
- Verifikimi: pytest 370/370 pas ngritjeve, build frontend OK, restart
  backend+frontend, health OK, asset 200, daemon-reload i njësive.

## 2026-09-18 — Auditim i plotë i sistemit + krahasim me top-10 + analiza HagaDosja (Cursor / Fable 5)
- Kërkesa e pronarit: auditim i plotë, gjetja e boshllëqeve, krahasim me liderët
  e fushës (top-10 AI-juridikë + praktik-menaxhimi) dhe analiza e platformës
  AVOKATI (~/HagaDosja/AI-Avokati) për adaptime. Raporti i plotë: canvas
  `auditimi-avokatim-2026-09-18` (dosja e Cursor-it) — përmbledhje këtu.
- Gjetjet kryesore (read-only, asnjë ndryshim produkt-kodi):
  - **KRITIKE — vulnerabilitete të papatchuara**: skanimi javor 14.09 gjeti
    20 vulns pip (aiohttp/cryptography/pypdf/setuptools/torch/pip) + 5 npm
    (1 critical, vargu i advisory-ve Next.js). Dhe **alarmi dështoi në heshtje**
    (ops_notify 400 te hook-u i Halimit) — raporti mbeti vetëm në log.
  - **KRITIKE — aktivizimi XK**: 33 tenant-ë, vetëm 1 përdorues real
    (Avokat D. Sejdiu); trafiku publik 160→33 vizitorë/javë pas fundit të
    fushatës OAK (1,590 kontakte, campaign complete, konvertim ~2%).
  - **E rëndësishme — RLS mungon në 5 tabela** (isolation_check FAIL):
    email_suggestions, deadline_suggestions, notifications,
    passkey_credentials, api_tokens — duhet migrim me politika RLS.
  - **E rëndësishme — avokatim-watchdog.service failed** (dështime
    intermitente exit 1 pa gjurmë; manualisht kalon; njësia ka edhe ndryshim
    në disk pa daemon-reload).
  - Të vogla: 2,830 chunks DE pa embeddings (backlog i batch-it të natës);
    dublikatë tenant-i "Avokatura Buzuku" ×2 + tenant-ë prove në prodhim;
    STATE.md i pasinkronizuar (header 05.08).
- Verifikimi kundër stack-ut live: pytest **370/370**, full_simulation
  **188/188 PASS** (886s), saas_check **ALL PASS pas riparimit** (shih më
  poshtë), health OK, backup i sotëm 943 MB, DB në head, 0 orphan records.
- **Fix i vetëm i bërë (veglat e verifikimit, jo produkti)**: `saas_check.py`
  kishte 2 drift-e — (1) signup pa `accept_tos` (kërkohet që kur u shtua ToS
  gate) dhe (2) vazhdonte me token-in e vjetër pas change-password, por
  ndryshimi i fjalëkalimit tani revokon sesionet e vjetra. U shtuan
  `accept_tos: True` + rifreskimi i token-it pas ri-login-it.
- Krahasimi top-10 (Harvey/Legora/CoCounsel/Protégé/Vincent/Luminance/Eve/
  Supio/Eudia/Garfield, rifreskuar me web 18.09) + adaptimet nga AVOKATI
  (verifier me bllokim citimesh 97.5% pass-rate, golden-set eval, workflows
  W1–W5, MCP server, citime të klikueshme): backlog i bashkuar me 10 avancime
  të prioritizuara — regjistruar në ROADMAP (seksioni i ri 2026-09-18).
- Left open (vendime/punë të propozuara, JO të nisura): patch-et e sigurisë,
  migrimi RLS, fushata e ri-aktivizimit XK (kërkon PO për Lane B), verifier
  v2 + eval gate + workflows (zbatimi pas zgjedhjes së pronarit).

## 2026-09-16 — Pastrim/optimizim i workspace-it + formalizimi i guard-hook-ut të postës (Cursor / Fable 5)
- Konteksti: kërkesë e pronarit për pastrim/optimizim të workspace-it në Cursor.
  Gjendja e gjetur: 2 skedarë të Halimit pezull në git që prej ~2 javësh,
  cache Python-i të shpërndarë, komente të vjetruara `docs/agent/` (njëjës)
  te pre-commit, pa `.cursorindexingignore`.
- Done — formalizimi i punës pezull të Halimit (korsia e postës):
  - **`ops_inbox_check.py`** (i ri, i pa-track-uar deri sot): sensor read-only
    i inbox-it me kursor `last_uid` — u commit-ua siç ishte. KUJDES: docstring-u
    referon `ops_inbox_ack.py` që ENDE NUK EKZISTON (avancimi i kursorit) —
    hap i ardhshëm i Halimit, jo i imi.
  - **`ops_send_reply.py`**: hook-u i guard-it (Halim D-139) ishte KOD I VDEKUR —
    `_guard_check` definohej pas bllokut `__main__` dhe s'thirrej kurrë. U lidh
    si hap i parë para çdo pune SMTP. Verifikuar live: guard-i kthen
    `allow:true` për sekretari/email_avokatim/send_reply (rrjedha s'bllokohet),
    dhe suppression-i i test-marrësve refuzon si më parë.
- Done — pastrim/optimizim:
  - `.pytest_cache` (rrënjë + backend) dhe të gjitha `__pycache__` në pemën e
    repos (jashtë .venv/data/node_modules) u fshinë; `git gc` → .git 12M→4.5M.
  - **`.cursorindexingignore`** (i ri): përjashton nga indeksi semantik i
    Cursor-it arkivin e vjetruar `docs/agent/` (njëjës — burim konteksti të
    ndenjur për agjentët; docs/agents/ është e vërteta), `package-lock.json`
    dhe log-et. `docs/agent/` NUK u fshi — është arkiv i qëllimshëm (header-i
    i vet e shënon DEPRECATED).
  - pre-commit (burim + kopja e instaluar u sinkronizuan): komentet thoshin
    ende `docs/agent/`; kodi ishte i saktë (`docs/agents/`) që më 01.09.
  - Dosja e Cursor-it `~/.cursor/projects/home-kllosha-BoraLaw` = 6.8M
    (kryesisht transkripte agjentësh që duhen ruajtur) — asgjë për të fshirë.
- Verifikimi: 370/370 teste, health OK, dërgim provë me marrës testi → refuzim
  i pastër pas kalimit të guard-it.

## 2026-09-07 — Kufiri i email-it: klasa "unknown" + enforcement (Cursor / Fable 5, VENDIM I HALIMIT)
- Konteksti: incidenti Solar72 — sekretari iu përgjigj AUTONOMISHT partnerëve
  privatë të pronarit (Rene Schuster, Oliver Triggs) **5 herë pa PO, 05–07.09**,
  përfshirë një dërgim në adresë të shkruar GABIM (`triggoliver@` pa "s" —
  rrjedhje e mundshme konfidencialiteti, asnjë bounce) dhe zotime takimesh
  (telefonatë "nesër", takim në Vjenë) në emër të pronarit. Të 5 turnet
  xhironin mbi modelin fallback (qwen). Auditimi i plotë me dëshmi:
  `~/halim-lab/eksperimente/auditimi-2026-09-07/INCIDENTI-SOLAR72-EMAIL.md`.
- Shkaku rrënjësor: `_classify` kthente `human` si DEFAULT për çdo dërgues të
  panjohur → korsia autonome (a) e payload-it. Doktrina e shkruar (D-064,
  Lane B këtu) gjithmonë thoshte "personal KURRË autonom" — payload-i kishte
  deviuar prej saj.
- Done (me PO eksplicite të Halimit, pikat 1–4): **`_classify` kthen `human`
  VETËM me lidhje mekanike me firmën** (alias lende ose ledger outreach-i,
  `_outreach_contacts()`); klasa e re **`unknown` = draft-për-miratim**;
  payload-i i cron-it: korsia (c) personal → draft-only, gate ndalues i
  `email_allowlist` para çdo dërgimi, rregulli "fallback → kurrë dërgim".
  Testet 370/370 (3 teste u përditësuan në kontratën e re — dërguesit
  "human" të testeve tani shënohen si kontakte outreach-i); skill_vet ALLOW.
- Halimi mbajti për vete: accept-in e harness_shield (bërë), doktrinën D-154
  ("AvokatIM s'përzien punët" — fjala e Kllosha-s) dhe korrigjimin e OPS.

## 2026-09-01 — Porta DE itemet 1–3: matja TTFT me streaming + plani i serverit BE (Cursor / Fable 5)
- Konteksti: pas valës së avancimeve, nga plani mbetën vetëm hapat e pronarit.
  Dy prej tyre përgatiten dot pa vendim: të dhënat për kriterin e latencës
  (item 3) dhe krahasimi i ofruesve BE (itemet 1–2, premtuar në plan).
- Done: **`scripts/eval_de_ttft.py`** — eval i ri i latencës streaming
  (time-to-first-token) mbi të njëjtat 20 pyetje + ndërtim prompti si
  `eval_de_quality.py` (importon CASES/CITATION_CASES prej tij), me warmup
  (cold-start-i i modelit është veti deploy-i, jo e pyetjes). Rezultati me
  `qwen3-abliterated:30b-a3b`: **TTFT p50 2.47s / p95 6.64s** (17/20 nën 5s;
  outliers 11.5s/6.4s nga GPU e përbashkët), full-response p95 12.71s.
  JSON te `data/eval_de_ttft_2026-09-01.json`. Gate doc item 3 u përditësua
  me matjen + vendimin e mbetur (a: rikuadrim kriteri si TTFT + ri-matje në
  server të dedikuar; b: GPU e dedikuar këtu).
- Done: **`docs/legal/EU-SERVER-PLAN.md`** — dokument vendimmarrës për
  itemet 1–2 (çmime të verifikuara në ueb 01.09): Hetzner GEX44 184 €/muaj
  (rekomandim; modeli DE 18 GB futet në 20 GB VRAM me ctx 16K — prompt max
  ~1.850 tokena pas riindeksimit) vs GEX130/131; Art. 27: Prighter Growth
  35 €/muaj (rekomandim) vs Engage/rep4eu/DataRep; plan migrimi 6-hapësh
  (provizionim → stack → provë restore → eval → cutover me tunel → rollback);
  kosto totale 219 €/muaj. Itemet 1+3 mbyllen bashkë (GPU e dedikuar heq
  outliers-at). Gate doc itemet 1–2 tani referojnë planin.
- Done: H-15 te `hapa-kllosha.md` (PKM e Halimit) — PO/JO për GEX44+Prighter.
- Left open: vendimi i pronarit (H-15); pas PO-së migrimi kryhet nga agjenti.

## 2026-09-01 — Vala e avancimeve DE+XK: hibrid për dokumentet, API tokens, Landesrecht BB+SN (Cursor / Fable 5)
- Kërkesa: zbatimi i planit "Avancimet AvokatIM DE+XK" (7 faza). Auditimi
  fillestar zbuloi se Fazat 2–5 dhe shumica e 6–7 ishin **tashmë të zbatuara**
  më 01–02.08 (D-040…D-050) — ROADMAP-i s'i kishte shënuar kutitë (burimi i
  konfuzionit). U verifikuan me teste (39/39) + faqet live, dhe ROADMAP-i u
  saktësua me data + D-numra që kjo të mos përsëritet.
- Done (Faza 1, boshllëku real): retrieval-i hibrid u shtri te **dokumentet e
  lëndëve** — migrimi `e4f5a6b7c8d9` (`document_chunks.tsv` 'simple' + GIN,
  backfill), populimi te `index_document_chunks`, `search_matter_documents`
  tani RRF mbi këmbën kosinus + plainto FTS (recetë si D-042, pa cap
  judgments). Teste të reja te `test_rag_chunking.py`.
- Done (Faza 6, boshllëku real): **Public API tokens** (D-066) — modeli
  `ApiToken` (hash-only, shown-once), migrimi `f5a6b7c8d9e0`, router
  `/api/api-tokens`, dega `avk_` te `deps.py` (scope read = vetëm
  GET/HEAD/OPTIONS, enforcim qendror; RLS + tenant checks si JWT; 2FA nuk
  aplikohet për qasje makine), max 10 aktivë/user, audit log në krijim e
  revokim. UI: `ApiTokensSection` te Settings → Siguria, çelësat `apiTok*`
  në të 7 gjuhët. Smoke live: create 201 → GET 200 → POST 403 (read-only) →
  pas revokimit 401.
- Done (Faza 7, boshllëku real): **Landesrecht BB + SN** — dy portale
  klasike server-rendered (jo juris SPA): adapterë të rinj `bravors`
  (bravors.brandenburg.de/gesetze/{slug}; markup i çrregullt — h3/h4/h6,
  me/pa anchor; rregulli i qëndrueshëm: çdo h3–h6 që nis me &sect;) dhe
  `revosax` (revosax.sachsen.de/vorschrift_gesamt/{id}.html; id-të nga
  sitemap.xml, seksionet nga atributi title i <section>). Importuar 9 akte
  BB + 10 SN (police, ndërtim, shkollë, kita, dyqane, festa, DS, komunal,
  shtyp, rrugë) → **4/16 Länder live (BY, NW, BB, SN)**; 12 të mbetura
  juris SPA (LESSONS #1, pa ndryshim). Kërkimi verifikuar live: pyetja
  saksone e orarit të dyqaneve kthen SächsLadÖffG § 3.
- Verified: pytest 370→389 (para valës 370, tani me testet e reja) — suita e
  plotë 370/370 para docs; `full_simulation.py` 187 PASS / 1 FAIL (citimet e
  Ava-s publike — luhatje LLM, riprova direkte ktheu 956 karaktere + 6 citime
  të sakta); health OK; frontend build + restart + asset 200; backend restart.
- Docs: ROADMAP kutitë e vjetruara u mbyllën me data (Tier A/B, hybrid, GKG,
  case law, time capture, API tokens, Landesrecht 4/16); STATE (Landesrecht
  39 akte, hibrid matter-docs, XK 2,532 vendime, D-066); DECISIONS D-066.
- Left open: (a) 12 Länder juris SPA — kërkojnë adapter headless ose
  marrëveshje juris; (b) hapat e pronarit të pandryshuar: porta DE 1–4, beA
  email, sipgate/openlegaldata/Outlook sideload (D-059).

## 2026-09-01 — Roster-health: sYn pa emulator + mbrojtja e .env.bak (Cursor / Fable 5)
- Done: u formalizua ndryshimi i gjetur i pa-commit-uar në `scripts/ops_roster_health.py`
  — `syn-emulator.service` doli nga lista e monitorimit të sYn (shërbimi u
  çaktivizua më 2026-08-30 me vendim të Kllosha-s; testet e sYn bëhen në
  telefona realë), përndryshe roster-health do të raportonte sYn "down" çdo 6h.
  sYn mbetet në roster me `services: []` (vetëm vend-mbajtës, pa kontroll aktiv).
- Done: `backend/.env.bak-health-20260831` (backup i .env me sekrete, krijuar
  nga puna e mirëmbajtjes 31.08) NUK ishte i git-ignoruar — rrezik commit-i
  aksidental. U shtuan `backend/.env.bak*` + `.env.bak*` te `.gitignore`.
- Done: u rregullua porta e pre-commit-it (`scripts/git-hooks/pre-commit` +
  kopja e instaluar në `.git/hooks/`): `DOCS_DIR` default ishte ende
  `docs/agent/` (njëjës, i vjetruar nga D-066) → bllokonte commit-e me docs
  legjitime te `docs/agents/` dhe i shtynte agjentët drejt `--no-verify`
  (siç ndodhi te 4f23726). Tani default = `docs/agents/`.
- Verified: `pytest tests/test_ops_roster_health.py` 5/5 OK; `ops_roster_health.py
  --status` → të gjitha projektet aktive; `git check-ignore` konfirmon backup-in
  të ignoruar; commit-i kaloi portën normalisht (pa `--no-verify`). Vërejtje
  anësore për vëzhgim: disku 38% i lirë (nga 68% më 05.08) dhe 2 failed units
  kozmetike (drkonqi-coredump-pickup, halim-drill).
- Left open: asgjë për këtë temë.

## 2026-09-01 — fix(watchdog): cron_run_receipts table (OpenClaw 2026.8.1 rename) (Halim)
- Done: `backend/scripts/ops_watchdog.py` kërkonte tabelën e vjetër `cron_run_logs` në `~/.openclaw/state/openclaw.sqlite`; pas update-it të OpenClaw 2026.8.1 tabela u riemërua `cron_run_receipts` (skemë e re: status, error_text, started_at_ms, finished_at_ms) → çdo xhirim i watchdog-ut hidhte `no such table: cron_run_logs`, të cilin e trajtonte si alarm → dërgoi 8 email të rreme "[WATCHDOG] posta ka ngecur" (31.08–01.09, ~çdo 3h) ndërsa triage-i punonte normalisht (xhirime çdo 2 min, të gjitha OK, job 2609be05).
- Done: query i `check_cron_errors()` u përditësua te `cron_run_receipts` (status, error_text, started_at_ms); testet `tests/test_ops_mail_reliability.py` u përditësuan me skemën e re. Verified: 11/11 teste kalojnë; `ops_watchdog.py --status` → findings OK.
- Done: inbox i pastruar — 14 të palexuar: 8 alarme të rreme WATCHDOG + 2 DMARC + 1 newsletter + 1 OAK auto-verifikim (Elvira Heta Vata, pa veprim) u arkivuan; Brave Search API billing update + Kling AI rinovim (8 shtator, visa *7294) u shënuan të lexuar (informuese).
- Left open: asnjë; watchdog tani alarmon vetëm për gjendje reale.

## 2026-08-26 — DE launch-gate item 3: reindex i jurisprudencës u mbyll + eval i ri (Halim)
- Done: batch-i i jurisprudencës (13,091 dokumente) u ri-indeksua — korpusi DE 100% pa chunk gjigantë (0 mbetur, max 2399); 4 dokumentet e fundit me burim 404 në portal u ri-chunk-uan nga teksti i ruajtur në DB pa humbje. Hapi (1) i launch-gate item 3 = MBYLLUR.
- Done: eval v1 (13:35) — max_prompt_tokens ra nga 15.3K në **1845** (ri-indeksimi eliminoi bllokuesin b), por FAIL: 1 statut i shpikur (§568c) + p95 17.2s.
- Done: SYSTEM_PROMPT — gjermanishtja në listën e gjuhëve + disiplinë citimesh (mos shpik nënndarje §; cito vetëm nga materialet) + rregull: pyetje me §/BGB/ZPO/StGB/KSchG → gjithmonë gjermanisht.
- Done: eval — zbulim i shqipes në kontrollin 'clean German' (fjalë shqipe + 'ë'); LIMIT 4→6 (ri-indeksimi çliroi kontekstin; limit=6 nxjerr §568 që mungonte → §568c u zhduk); 'will' hiqet nga anglishtja (fjalë e vlefshme gjermane — FP).
- Verified (eval v3): 20/20 jo-bosh · 19/20 citime · 0 statute të shpikura · gjermanisht 19/20 (1 FP 'will') · p95 14.5s (kërkohet ≤5s) ❌ · max prompt 2721 ✅. Eval v4 në xhirim për konfirmim të 20/20 gjermanisht.
- Left open: latenca p95 — i vetmi bllokues i mbetur; kërkon vendim (kriter më realist ose model më i shpejtë). DE qëndron në DeepSeek deri atëherë.

## 2026-08-25 — DE launch-gate item 3: corpus re-index, phase 2 (Halim, iniciativa 13:30)
- Done: korpusi DE **law** u pastrua 100% nga chunk-et gjigantë (>2400): batch federal 69/71 akte ri-indeksuar (`import_de_laws.py --force`, commit-i i mekanizmit ishte 8e16295; RuStAG u zgjidh me slug `stag`, DSGVO me importer-in e vet — 2 "not in gii-toc" të mbetur u mbyllën), 17 akte Landesrecht (NW+BY) + DSGVO (284 chunks). Para: 1954+280+38+2 gjigantë → pas: **0** në DE law (79 federale + 20 Landesrecht, verifikuar me SQL).
- Done: `import_de_rechtsprechung.py` mori `--force` (modeli i import_de_laws: DELETE + ri-import, 404-tolerant) + helper i ri `corpus_common.existing_reference_ids()`; skript i ri i synuar `reindex_de_judgments_giant.py` (prek VETËM ~13,096 dokumentet me chunk gjigantë, resumable, `--limit`/`--sleep`, log i plotë) — test 5/5 OK.
- In progress: batch-i i jurisprudencës (13,091 dokumente, ~16.6k chunk gjigantë) nisi në background 13:40 → `/tmp/reindex_de_judgments.log`; pritet disa orë; verifikim pas përfundimit (0 mbetur) + commit i skripteve.
- Left open / next: verifikim i batch-it të jurisprudencës + ri-ekzekuto `eval_de_quality.py` (hap 3); latenca p95 19.3s vs ≤5s mbetet e hapur (hap 2). DE qëndron në DeepSeek deri atëherë.

## 2026-08-23 — DE launch-gate item 3: formal re-validation of qwen3.8:27b (Halim, deepseek-v4-flash)
- Done: shkruar `backend/scripts/eval_de_quality.py` (P-07): 20 pyetje juridike gjermane (14 NL + 6 §-citime) me RAG REAL (`search_corpus` limit=6/4, language=de), prompt assembly identik me prodhimin (`_build_ask_messages`), kriteret e DE-LLM-REVALIDATION-PLAN.md (jo-bosh, citim ref+§, gjermanisht e pastër, pa statute të shpikura, p95 latencë, prompt ≤80% ctx).
- Verified (raundi 3, `qwen3.8:27b`, ctx 16384, RAG limit=4): **1. jo-bosh 20/20 · 2. citim ref+§ 19/20 · 3. gjermanisht e pastër 20/20 · 4. 0 statute të shpikura · 5. p95 = 19.3s (kërkohet ≤5s) ❌ · (b) max prompt_tokens 15314 > 13107 ❌** → **VERDICT: FAIL — item 3 mbetet i HAPUR; DE qëndron në DeepSeek** (`llm_provider=None`).
- Gjetjet: (1) `qwen3.8:27b-agent` (ctx 98304) është JOPRAKTIK këtu — KV cache s'futet në VRAM të ndarë (29/32 GB të zëna) → shtresa në CPU → 97% CPU / 5% GPU, minuta për përgjigje; (2) korpusi ka chunk-e gjigantë (paragrafë të vetëm > CHUNK_SIZE që s'u ndanë) → prompt deri 15.3K tokena edhe me limit=4; (3) me limit=6 raundi 1 dha 1 statut të shpikur ("§ 564b", korpusi ka vetëm § 564) dhe max 15515 tokena; me limit=4 retrieval humb § 517 ZPO për pyetjen e Berufung (dështim retrieval, jo modeli); (4) `qwen3:14b` (ctx 40960) matur pjesërisht: cilësi më e dobët (2/4 citime) + latencë më e lartë (22–46s) → jo alternativë.
- Left open / next: për ta kaluar item 3 duhen (a) rregullim i chunk-ing-ut të korpusit DE (ndarje e paragrafëve gjigantë) +/ose truncate në ndërtimin e kontekstit; (b) kriter latence më realist ose GPU e lirë/dedikuar për DE; pastaj ri-validim. Rezultatet e plota: `backend/data/eval_de_quality_2026-08-23.json` (git-ignored).
- Done: përditësuar `backend/tests/test_ops_roster_health.py` me firmën e re — `check()` kthen 4 vlera (problems, repairs, ok, unresolved) dhe `build_report()` pranon argumentin `unresolved` (ndryshim i D-070: projektet e vetë-shëruara nuk janë më error).
- Verified: 5/5 teste kalojnë (më parë 4 dështonin, para-ekzistues — auditimi i outreach-it G1-G3/O1-O7 i Fable 5).
- Left open: asnjë; bounce-i i testit x@example.com (RFC 2606) injorohet.

## 2026-08-23 — DE launch-gate item 3 follow-up: corpus chunking fix (Halim, iniciativa 13:30)
- Done: rregulluar `backend/app/services/rag.py::chunk_text` — paragrafët e vetëm më të gjatë se CHUNK_SIZE (1200) tani ndahen përmes `_split_paragraph` (kufij fjalish me regex të sigurt për shkurtesat gjermane "Art. 1"/"Abs. 2"/"z. B.", pastaj hard-cap në CHUNK_SIZE për fjali gjigante). Ky ishte shkaku i max prompt 15.3K tokena në eval-in e mëngjesit: korpusi DE ka paragrafë ligjorë gjigantë që s'ndaheshin kurrë.
- Done: 3 teste të reja në `tests/test_rag_chunking.py` (paragraf gjigant ndahet; fjali >CHUNK_SIZE pa kufij ndahet hard me ruajtje të plotësisë; shkurtesat nuk priten).
- Verified: `pytest tests/ -q` → 358 passed (para-ekzistuese + të reja), 15s.
- Left open / next: (1) ri-indeksimi i korpusit DE ekzistues (chunk-et e vjetra në DB mbeten gjigantë — duhet re-chunk + ri-embedding i dokumenteve DE); (2) latenca p95 19.3s vs ≤5s — GPU e lirë ose kriter i rishikuar; pastaj ri-ekzekuto `eval_de_quality.py`. DE mbetet në DeepSeek deri atëherë.

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

## 2026-08-20 — Forcimi mbrojtës i outreach-it: auditimi G1–G3/O1–O7 (Cursor/Fable 5)
- Done: **O1 shkaku rrënjësor** — `outreach_sender.py` lexonte
  `workspace/secrets/infrastructure.env` (shteg i HEQUR nga D-077) → Resend
  s'gjendej kurrë dhe cold outreach binte HESHTUR në Gmail-in personal që nga
  5 gushti; u rregullua te `~/.securevault/secrets/` → **mode=resend live**
  (cap 25). Plus FAIL-CLOSED: modi `smtp` refuzon dërgim të ftohtë pa
  `ALLOW_SMTP_FALLBACK=1`. **O4** — `pending_rows()` me dedup brenda batch-it
  te `de_outreach_campaign.py` (fix-i Vuksani i XK, tani edhe DE) + test.
  **O3** — njësitë `avokatim-outreach-de.{timer,service}` U FSHINË (ishin
  disabled; skripti mbetet me portën `DE_TRACK_B_ENABLE=1`). **O7** — STATE/
  ROADMAP sync (30→25/ditë, statusi real i dërguesit). **G2** — klasa hardline
  `mail-adhoc` te `~/scripts/halim_guard.py` (s-nail/mailx/msmtp/sendmail
  bllokohen mekanikisht). **G1/O2** — verifikuar pa veprim (heartbeat një
  shteg; ledger + List-Unsubscribe në vend). **G3** — PO/JO e vjetruar e
  korsisë personale → D-070 te playbook-et e workspace.
- Verified: outreach tests 16/16; suita e plotë backend 351 pass (4 dështime
  PARA-EKZISTUESE te `test_ops_roster_health.py` — të paprekura nga kjo punë,
  "too many values to unpack": skripti ndryshoi firmën, testi jo); `Sender().mode
  == "resend"` live; fail-closed i provuar (refuzim pa override).
- Left open: 4 testet e roster-health duan rregullim (pronari i asaj vegle);
  shënim ndershmërie — gjatë provës së override-it u dërgua 1 email test real
  te `x@example.com` (RFC 2606, pa marrës real; bounce kthehet në inbox).

## 2026-08-15 — Committed: verification reminder (2h nudge) — work i mbetur (sesioni Cursor D-082)
- Done: `_send_verification_reminder` (auth.py) + çelësat i18n — 2h pas
  regjistrimit dërgon NJË kujtesë me token të ri nëse emaili s'u konfirmua
  (Gmail spam-folder false negatives). Ishte LIVE në prodhim nga pema e
  punës, pa commit — u sigurua në historik nga Halim.
- Verified: sintaksë OK. U rinis avokatim.service me këtë kod LIVE tashmë.
- Left open: asnjë.

## 2026-08-15 — Fix: auto-verify NameError + corpus duplicate -> 409 (Halim)
- Done: (1) `app/api/marketplace.py` — `_auto_verify_or_notify` thirrte
  `try_auto_verify` pa import; çdo onboarding submit dështonte me NameError dhe
  binte te fallback manual (ndodhi 2x sot për regjistrimet e reja). Shtoi
  importin. (2) `app/api/corpus.py` — guard-i IntegrityError mbështillte vetëm
  `commit()`, por INSERT-i ndodh te `flush()`; duplikatet iknin si 500 në vend
  të 409-së së projektuar. Guard-i tani rrethon `flush()`.
- Verified: py_compile OK; 11 teste corpus/rag kalojnë; avokatim.service u
  rinis (20:18) dhe /api/health + /api/public/voice/status OK; issue-t e
  Glitchtip 5/9 u shënuan resolved.
- Left open: mbyllja e procesit të vjetër zgjati ~45s (TimeoutStopUSec=45s +
  abort) — vlen hetuar shkaku i stop-it jo-graceful. Punë e pa-commituar nga
  sesioni i mëparshëm: auth.py/_send_verification_reminder + i18n.

## 2026-08-15 — Whisper STT: lease GPU në arbitrin qendror të flotës (openclaw-knowledge D-083) (Cursor / Fable 5)
- Done: modeli Whisper STT është qiramarrës GPU interaktiv (~1.6 GB VRAM kur rezident).
  E regjistrova te arbitri i përbashkët `~/scripts/gpu_arbiter.py` si `interactive`
  (prioriteti më i lartë) për KOHËZGJATJEN e modelit rezident CUDA: `acquire` kur ngarkohet
  CUDA te `_load_whisper`, `release` kur cikli idle i shkarkon (`_idle_unload_loop`) te
  `backend/app/services/voice.py`. Helper i ri: `backend/app/services/gpu_lease.py`.
- Verified: `py_compile` OK. Kostoja mbahet jashtë hot-path-it të transkriptimit (lidhur me
  rezidencën, jo per-thirrje). Best-effort & këshillues: çdo dështim (arbitër mungon/gabim)
  gëlltitet — STT s'varet e s'prishet nga kjo shtresë. Arbitri: flock + prioritete
  interactive<music<batch (recetë `~/scripts/GPU-ARBITER.md`).
- Left open / next: asgjë — integrimi hyn në fuqi në restart-in e ardhshëm të backend-it.

## 2026-08-15 — DE local LLM: gemma3:27b → qwen3.8:27b (openclaw-knowledge D-082) (Cursor / Opus 4.8)
- Done: konsolidimi fleet-wide i modeleve (openclaw-knowledge D-082) fshiu `gemma3:27b`; migrova
  baseline-in lokal DE te **`qwen3.8:27b`** (`backend/.env: LOCAL_LLM_MODEL`), shtova
  `reasoning_effort=low` në `backend/app/llm/local.py` (qwen3.8 është "thinking"; gemma3 nuk ishte),
  dhe **rihapa item 3 të `docs/legal/DE-LAUNCH-GATE.md`** për ri-validim formal.
- Verified: PA dëm runtime — AvokatIM live përdor `LLM_PROVIDER=deepseek`; profili DE mbetet
  `llm_provider=None` (demo), pra modeli lokal s'thirret aktualisht. Validim informal i qwen3.8 për
  gjermanisht: shootout-i DE i D-081 (pa përgjigje boshe, citim korrekt Art. 17 DSGVO).
- Left open / next: PARA lansimit publik DE — (a) ri-validim formal i cilësisë gjermanishte të
  qwen3.8:27b me RAG real; (b) sizing i kontekstit (endpoint-i OpenAI i Ollama-s s'pranon `num_ctx`
  në body → mund të duhet variant Modelfile me `num_ctx` më të madh si `qwen3.8:27b-agent`);
  (c) pastaj `PROFILES["DE"].llm_provider="local"`. NUK preka punën e pakommit-uar të agjentit tjetër.
- Follow-up (auditim, po atë ditë): `jurisdictions.py` kishte ende një koment që thoshte
  "gemma3:27b stays installed and validated" — u përditësua në qwen3.8:27b + gate item 3 REOPENED.
  (Referencat në `docs/pitch/*` mbeten për vendim wording nga pronari.)

## 2026-08-10 — ops_roster_health: green kur vetë-riparon + hiq edas-acestep (D-070) (Cursor / Fable 5)
- Done: `ops_roster_health.py` del me kod jo-zero VETËM për probleme të PAZGJIDHURA (vetë-riparimi
  s'është më "error"); shtova riverifikim pas restart-it (`repaired_all`) + rreshtat "u vetë-riparuan"/
  "ende të pazgjidhura". Hoqa `edas-acestep.service` (dhe la vetëm edas.service + edas-frontend) nga
  lista e monitoruar sepse GPU manager-i i EdaS (`~/EdaS/data/gpu_manager.json`: auto_release, idle 15m)
  e ndal QËLLIMISHT për të liruar VRAM-in e RTX 5090 → alarme false + luftë rinisjeje.
- Verified: `--status` = "Të gjitha projektet aktive", exit 0; `--repair` para heqjes = "u vetë-riparuan", exit 0.
- Left open / next: rrënja e vërtetë (acestep flap) është sjellje normale idle-release; s'kërkon veprim.
  Konteksti i plotë (autonomi D-070 pa limite) te openclaw-knowledge DECISIONS D-070 / LESSONS L-08.

## 2026-08-05 — Auditimi outreach + Gmail: throttle, pajtueshmëri, dërgues i dedikuar (D-069) (Cursor / Fable 5)

- Done: heartbeat-i i cron-it u kalua në rrugë absolute (`~/AvokatIM/data/ops/` —
  bug-u i alarmeve false çdo 3h); XK outreach 60→25/ditë me jitter 20–60s + dedup
  brenda batch-it (fix-i Vuksani) + `List-Unsubscribe`; DE Track B i mbyllur fort
  (refuzon pa `DE_TRACK_B_ENABLE=1`, UWG §7); të dy fushatat respektojnë
  kill-switch-in e halim_guard dhe shkruajnë audit; modul i ri
  `scripts/outreach_sender.py` (Resend nga `mail.avokatiim.ai` + fallback Gmail
  SMTP + warm-up 10/20/25) i integruar në të dy fushatat; prompt-i i cron-it
  triage me rregulla sipas klase (personale/company = PO/JO); rregull i fortë
  "dërgim vetëm me ops_send_reply.py" te GMAIL-OPS/AVOKATIM-OPS; COMMS.md i
  sinkronizuar me realitetin.
- Verified: watchdog "OK" pas fix-it; dry-run të dy fushatat (batch 25/15, mode
  smtp); opt-out end-to-end (STOP → `_classify` → `de_suppress.txt` → skip në të
  dy fushatat); guard-i Track B refuzon pa flag; py_compile OK.
- Left open / next: 2 hapa manualë të Kllosha-s për Resend + DNS —
  `docs/agents/OUTREACH-SENDER-SETUP.md`; pas verifikimit fushatat kalojnë vetë
  në mode `resend` me warm-up.

## 2026-08-05 — Fuqizimi i plotë i Halimit: kredencialet, skills, monitorim 24/7 (D-065) (Cursor / Fable 5)

- Done: (F1) `secrets/CREDENTIALS.md` (chmod 600) = harta e vetme e çdo
  kredenciali (41 loginat e Firefox + `.env`-të + tokenat) me rregullin
  "vetëm në makinë, kurrë jashtë"; lidhur me workspace `AGENTS.md`
  (session-start); fjalëkalimi i llogarisë Mozilla u shtua te `secrets/README.md`.
  (F2) 8 skills të kuruara u aktivizuan në `openclaw.json` (healthcheck,
  skill-creator, weather, session-logs, summarize, blogwatcher, nano-pdf,
  mcporter) + rindezje gateway-i; dokumentuar te `TOOLS.md`. (F3) OpenCode
  (`opencode-ai`) i instaluar dhe i lidhur me çelësin ekzistues DeepSeek
  (`~/.config/opencode/opencode.json`); skill `coding-agent` = ready;
  guardrails te `CODING-OPS.md` (autonom vetëm AvokatIM/OpsHub/NaturalBeauty,
  EdaS dy-agjentësh, KURRË TotoTrading/BoraLaw). (F4) `scripts/ops_roster_health.py`
  (pa LLM) + cron `avokatim-roster-health` (çdo 6h, `--repair` vetëm projektet e
  sigurta) + cron `halim-heartbeat` (çdo 30 min); `ops_watchdog.py` tani alarmon
  për heartbeat të vjetruar (>70 min) → skedulues i vdekur kapet nga jashtë;
  raporti i mëngjesit u rikrijua me bllokun e shëndetit të projekteve.
- Verified: `opencode run` → OPENCODE_DEEPSEEK_OK; `openclaw skills list` tregon
  8+coding-agent ready/needs-setup; `openclaw cron list` tregon 5 punë;
  `ops_roster_health.py --status` → të gjitha projektet aktive (disk 68%, docker 8);
  `ops_watchdog.py --status` OK; pytest: 16 (mail reliability+mailbox) + 5
  (roster-health) = kaluan.
- Left open / next: skills me CLI (summarize/blogwatcher/nano-pdf/mcporter)
  instalojnë binarin në përdorimin e parë; shtesat me pagesë (voice/WhatsApp/X)
  mbeten për vendim të mëvonshëm.

## 2026-08-05 — Harmonizimi i plotë i Halimit: mailbox + makina (D-064) (Cursor / Fable 5)

- Done: Halimi merr menaxhim të plotë të arifi.arber@gmail.com dhe një rol të
  qartë mbi gjithë makinën. (F1) `scripts/ops_mailbox.py` — unread-count,
  search, read (PEEK), mark-read, archive (Gmail `-X-GM-LABELS \Inbox`),
  label; mur zjarri që refuzon të prekë flag-un e çdo mesazhi drejtuar një
  alias-i lënde `+token@` (që `email_ingest.py` t'i marrë i pari). (F2)