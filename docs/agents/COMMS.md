# COMMS — the communication layer (single source of truth)

> Every email the platform sends, who sends what, and the rules for changing
> any of it. If you add/change an outbound message, update this file in the
> same commit. The operator assistant (Halim/OpenClaw) keeps a copy of the
> summary in `~/.openclaw/workspace/AVOKATIM-OPS.md` — keep them in sync.

## The three lanes

| Lane | Who acts | Human involvement |
|---|---|---|
| **A. Automatic (system)** | Backend sends templated emails on triggers | None — fully automated |
| **B. Correspondence (Halim)** | OpenClaw assistant drafts replies to human email | Owner answers **PO/JO** on Telegram, nothing else |
| **C. Owner-only** | Owner writes personally | Sensitive/legal/press matters, at his discretion |

The owner must never need to *compose* routine email. Lane A thanks, welcomes,
reminds and invoices by itself; lane B handles inbound human mail with a
ready-to-send draft and a yes/no question.

## Lane A — automatic emails (trigger → recipient → i18n key → code)

All templates live in `backend/app/i18n.py` in **7 languages**
(sq/sr/tr/bs/en/zh/de) and are sent via `send_email` in
`backend/app/services/notifications.py`, which **suppresses test/simulation
recipients** (`_is_test_recipient`).

### Lawyers / notaries (tenant accounts)

| Trigger | Key(s) | Code |
|---|---|---|
| Signup | `lawyer_verify_*` (confirm email), `lawyer_welcome_*` / `notary_welcome_*` (next steps) | `api/auth.py` |
| 1h after signup, public profile still inactive | `lawyer_profile_nudge_*` (one-shot) | `services/notifications.py` |
| License verified (auto or manual) | `verify_approved_*` — **warm thank-you letter** linking to the lawyer's own public profile (`/avokatet/{id}`) + settings, with next-steps checklist (sq), + `verify_approved_founder` paragraph when the Founder badge applies | `services/license_verify.py`, `api/platform.py` |
| License rejected | `verify_rejected_*` | `api/platform.py` |
| New matching marketplace case / directed case / SOS | `case_match_*`, `case_directed_*`, `sos_alert_*` (+ SMS variants) | `api/marketplace.py` |
| New consultation booking | `booking_new_*` | `api/bookings.py` |
| Monthly subscription invoice / overdue / trial ending | `platform_invoice_*`, `platform_overdue_*`, `trial_ending_*` | `services/platform_billing.py` |
| Deadline reminders | `reminder_*` | `services/notifications.py` |
| Team invite | (invite email) | `api/team.py` |
| Activation sequence: day 3 / 7 / 30 after signup while the tenant still has **0 matters** (skips `is_test` tenants; Redis-deduped one-shot per stage) | `onboard3_*`, `onboard7_*`, `onboard30_*` | `services/notifications.py` (`_check_activation_sequence`) |

### Citizens

| Trigger | Key(s) | Code |
|---|---|---|
| Signup | `citizen_verify_*` (confirm email) | `api/marketplace.py` |
| 1h after signup, email still unverified | `citizen_verify_reminder_*` (one-shot) | `services/notifications.py` |
| 48h after signup, verified but no case posted | `citizen_case_followup_*` (one-shot) | `services/notifications.py` |
| Email confirmed | `citizen_welcome_*` — **thank-you letter** (Ava, post case, directory, documents, SOS; free forever) | `api/marketplace.py` |
| Social signup (Google/Apple/Meta) | email arrives provider-verified → `citizen_welcome_*` + `notify_ops` fire immediately, no verify step | `api/oauth_citizen.py` |
| Password reset | `citizen_reset_*` | `api/marketplace.py` |
| Lawyer claimed their case / new message | `case_claimed_*`, `case_message_*` | `api/marketplace.py` |
| 48h after a claimed case concluded, no review yet | `case_review_request_*` (one-shot, link to `/rasti-im`) | `services/notifications.py` |
| Matter portal invite / new message / signature | `case_portal_ready_*`, `email_new_message_*`, `email_signed_*`, `email_signature_*` | `api/intake.py`, `api/portal.py`, `api/collab.py` |
| Client invoice | `email_invoice_*` | `api/billing.py` |

### Outreach (acquisition)

**Kosovo (XK)** — daily batch of **25** introduction emails (lowered from 60
on 2026-08-05, audit D-069) with randomized 20-60s spacing, to OAK lawyers
(then ONK notaries) via `avokatim-outreach.timer` →
`backend/scripts/oak_outreach_campaign.py`. Dedup (including within-batch,
the Vuksani fix) + suppression of registered addresses + `List-Unsubscribe`
header; honours the halim_guard kill switch and writes to the action audit
log. Log `data/outreach.log`. Both letters end with a mobile P.S. (open
avokatiim.ai directly in Chrome/Safari, not inside the mail app) — the
Vuksani lesson (D-063).

**Agjenti ↔ Halimi (2026-09-19, korrigjuar të njëjtën ditë):** kanali që sheh
pronari është **chat-i main i Halimit (http://127.0.0.1:18789/chat/main)** —
mesazhet futen aty me `~/scripts/halim_events.py wake --text "[cursor-fable5 /
AvokatIM] …"` (`/hooks/wake`, agentId main). Handoff-et
(`handoff_hap`/`handoff.py`) mbeten si dosja e strukturuar async (Halim Live
:8795 NUK shikohet nga pronari); `notify_ops` vetëm ping Telegram. Protokolli
i plotë: AGENTS.md §4c.

**Demo one-off (XK, 2026-09-18, owner PO 14:10/15:27):** "Si funksionon
AvokatIM në 4 hapa" — HTML me 3 ilustrime inline (CID) + tekst, sq — te
avokatët me profil të dukshëm në Treg, 2 valë (23 + 7 = **30 ok / 0 fail**),
tag `demo-2026-09-18`. Skripti `backend/scripts/send_demo_email.py`
(halim_guard + `_is_test_recipient` + dedup për tag); ledger
`data/ops/demo_email_sent.csv` — kontrolloje para çdo ri-dërgimi, bashkë me
`data/reactivation_sent.csv` (mbivendosje marrësish të mundshme të njëjtën
ditë). Evidenca: `data/evidence/demo-2026-09-18/`.

**Activation one-off — segment #1 (XK, 2026-09-18, owner PO 15:50):** "Profili
juaj në AvokatIM — një hap larg dukshmërisë" — email i SHKURTËR veprues te
avokatët e DUKSHËM por të PAVERIFIKUAR (`lawyer_profiles.is_visible = true
AND verification_status <> 'verified'`), me ftesë për të plotësuar profilin
(`/settings#public-profile`). Marrësit nga DB (jo nga lista e fushatës) +
përjashtimet e pronarit (adresa e tij, Valtida Shukriu): **7 dërguar / 0
dështime**, tag `paverifikuar-2026-09-18`. Skripti
`backend/scripts/send_paverifikuar_email.py` (halim_guard +
`_is_test_recipient` + dedup për tag); ledger `data/ops/paverifikuar_sent.csv`.
Evidenca: `data/evidence/paverifikuar-2026-09-18/`. **Kujdes:** të 7 kishin
marrë edhe emailin-demo po atë ditë (3 prej tyre edhe ri-aktivizimin) →
mbivendosje e njohur; kontrollo TË TRE ledger-ët para ri-dërgimit.

**Re-activation one-off (XK, 2026-09-18, owner PO):** 23 personal emails to
active 0-matter accounts (subject "{office} — llogaria juaj në AvokatIM ju
pret", 15-minute live-demo offer, sq), sent via `services/notifications.
send_email` with 2s spacing. Dedup log `data/reactivation_sent.csv` — check
it before ANY repeat send. Replies are normal Lane B traffic (Halim briefed
via notify_ops). Accounts older than 36 days are outside the automatic
activation sequence, so no double-touch.

**Sending identity (D-069):** both campaigns now send through
`backend/scripts/outreach_sender.py` — Resend API from `mail.avokatiim.ai`
once the domain is verified (setup: `OUTREACH-SENDER-SETUP.md`), with the
personal Gmail as SMTP fallback until then. Replies always flow to
`arifi.arber@gmail.com` (Reply-To), so triage/opt-out are unchanged. On the
dedicated domain a warm-up cap applies: 10/day week 1, 20/day week 2, then 25.

**Germany (DE), lawyers — PAUSED, hard-gated** (2026-08-05, D-062 + D-069):
the daily batch of 15 "Gründungspartner" emails to individual lawyers
(`de_outreach_campaign.py`, harvest in `data/de_lawyers.csv`) is on hold —
no timer exists, and since D-069 the script itself **refuses real sends
unless `DE_TRACK_B_ENABLE=1`** is set (UWG §7 grey zone; `--dry-run` always
works). The primary German track is selling/licensing the platform to
companies (below). Re-enable only on the owner's explicit decision.

**Germany (DE), companies — Track A, PO/JO gated** (2026-08-05, D-062): the
main German channel. ~12 researched buyer candidates (insurers, vendors,
consolidators, publishers) live in `data/de_companies.csv`, built from the
research dossier `docs/pitch/hulumtimi-blersit-de.md`.
`backend/scripts/de_company_outreach.py --propose N` generates a personalized
cover letter (German/English per target) + the full offer as PDF and hands the
draft to Halim via `notify_ops` (`lead-m&a`); **nothing is sent without an
explicit "PO" from the owner on Telegram** — Halim then sends with
`ops_send_reply.py --attach <offer.pdf>`. State:
`data/de_company_outreach_log.csv` — statuses proposed → sent/closed, set by
Halim after the PO/JO outcome via `--mark <domain> sent|closed` (D-063);
`--followups` drafts a single 10-day nudge for SENT letters only (again
PO/JO). Replies from target domains are classified `company` by the triage
("LEAD M&A"), escalated first, never answered autonomously, and recorded in
`data/de_company_replies.txt` (stops nudges). First letter sent 2026-08-05:
Septeo (info@stp.one), owner's PO, offer PDF attached.

**Opt-outs (both campaigns)** — a reply that is essentially "STOP" /
"abmelden" / "unsubscribe" / "mos më shkruani" is auto-classified by
`ops_inbox_triage.py` (class `optout`), appended to `data/de_suppress.txt`
and thereby suppressed in BOTH the DE and XK campaigns forever. Halim never
replies to opt-outs and never maintains the list by hand.

One-off manual sends live in `backend/scripts/` and are kept for the record,
e.g. `send_visibility_nudge.py` (2026-07-31: asked the two newly verified
lawyers to flip their public-profile switch). Such scripts are run once by
the owner/agent and never wired to a timer.

## Lane B — Halim (OpenClaw) correspondence protocol

- **Inbox hygiene (2026-09-24, sekretari handoff)**: `backend/scripts/ops_inbox_hygiene.py`
  buckets unseen mail for the morning line. Bulk/platform senders (e.g.
  `streaks@chess.com`, `hello@chess.com`) are classified `reklama` via the
  `_NOISE` keyword list; the "tjera + display name → personale" promotion is
  guarded by `_BULK_LOCAL` (streaks/hello/welcome/alerts/receipts/…)
  so a display name alone no longer promotes a bulk sender to
  "kërkojnë vëmendje" (was: chess.com notifications counted as personal,
  polluting the morning line and email_allowlist T2).
- **Inbox hygiene fix-up (2026-09-27, sekretari handoff)**: `_local_part()`
  returned the *domain* (`rsplit("@", 1)[-1]`) instead of the local part, so the
  `_BULK_LOCAL` guard above never matched — `hello@` / `streaks@` senders were
  still promoted to "personale" (e.g. `Hack Apertus Team
  <hello@ailights.org>`). Fixed to `[0]`; the guard now works as intended.
- **Inbox hygiene fix-up (2026-10-06, sekretari handoff)**: bulk ESPs with a
  *numeric* subdomain prefix escaped the literal `startswith` check —
  `Cloudflare <em@em1.cloudflare.com>` (marketing) has prefix `em1.`, not
  `em.`, so it was promoted to `personale` and inflated `needs_attention`.
  New `_is_bulk_domain_prefix()` strips trailing digits from the leading label
  and retries against `_BULK_DOMAIN_PREFIX`, so `em1./em2./em3. → em.`,
  `mail2. → mail.`, etc. all classify as bulk. Human senders unchanged.
- **Inbox hygiene fix-up (2026-10-08, sekretari handoff)**: Meta/Facebook bulk
  notifications escaped every heuristic — `Facebook Friend Suggestions
  <friendsuggestion@facebookmail.com>` has no `_NOISE` keyword and no ESP
  prefix, so it was promoted to `personale` and inflated `needs_attention`.
  Added `facebookmail.com` to `_BULK_DOMAIN` and `friendsuggestion` to
  `_BULK_LOCAL`. Human senders unchanged.
- **Inbox hygiene fix-up (2026-10-13, sekretari handoff)**: Alibaba marketplace
  notifications escaped every heuristic — `feedback@service.alibaba.com`
  ("New seller message…") has no `_NOISE` keyword and an unknown local part, so
  it was promoted to `personale` (the only 1/1 "kërkojnë vëmendje" that morning).
  Added `alibaba` to `_NOISE`. Human senders unchanged (verified: a plain
  `Arben <arben@example.com>` mail still classifies `personale`).
- **Inbox hygiene fix-up (2026-10-14, sekretari handoffs 2026-10-13T191200Z +
  2026-10-14T062139Z)**: Meta hackathon bulk mail escaped every heuristic —
  `AI at Meta <update@digital.metamail.com>` ("It's go time: Apply…") has local
  part `update` (not in `_BULK_LOCAL`) and domain `digital.metamail.com` (a
  subdomain, so the exact-match `_BULK_DOMAIN` test missed it), so it was
  promoted to `personale` and inflated `needs_attention` (1/1). Added `metamail`
  to `_NOISE` (substring token, robust to metamail subdomains). Verified: bulk
  → `reklama`/T0, plain human senders still `personale`.
- **Inbox hygiene fix-up (2026-10-15, sekretari handoff 20261015T174128Z)**:
  Namecheap registrar bulk notice escaped every heuristic —
  `Namecheap Support <support@namecheap.com>` ("Upcoming price changes on your
  .com domain") has local part `support` (not in `_BULK_LOCAL`) and domain
  `namecheap.com` (not in `_BULK_DOMAIN`), so the display name promoted it to
  `personale` and inflated `needs_attention`. Two fixes: `namecheap` added to
  `_NOISE` (all namecheap mail → `reklama`/T0) and `support` added to
  `_BULK_LOCAL` (generic role-mailbox class, so any vendor's `support@` is no
  longer read as a human — `_FINANCE` still wins first for bank senders).
  Verified: namecheap → `reklama`; `Raiffeisen <support@raiffeisen.at>` stays
  `financiare`; plain human sender still `personale`.
- **Inbox hygiene fix-up (2026-10-16, sekretari handoff 20261016T070129Z)**:
  Hugging Face platform notifications escaped every heuristic —
  `Hugging Face <website@huggingface.co>` (login/access notices, a bulk
  no-reply sender; `email_allowlist.py check --korsia personal` → REFUZOHET)
  has local part `website` (not in `_BULK_LOCAL`) and domain `huggingface.co`
  (not in `_BULK_DOMAIN`), so all 5 of 5 that morning were promoted to
  `personale` and inflated `needs_attention`. Two fixes: `huggingface` added to
  `_NOISE` (substring token, robust to HF subdomains → `reklama`/T0) and
  `website` added to `_BULK_LOCAL` (generic org-role mailbox, so a vendor's
  `website@` is no longer read as a human). Verified: HF → `reklama`; plain
  human sender still `personale`.
- `scripts/ops_inbox_triage.py` (cron every 10 min, read-only IMAP PEEK)
  classifies inbound mail; human mail → Telegram with context + a
  **final, ready-to-send draft** signed "Arbër Arifi — AvokatIM".
- **Firm-link boundary (2026-09-07, VENDIM I HALIMIT — incidenti Solar72)**:
  `_classify` returns `human` ONLY for mail mechanically linked to the firm —
  matter `+token@` aliases or senders our outreach campaigns contacted first
  (`data/oak_outreach_log.csv` / `de_outreach_log.csv`). Every other sender is
  the new class **`unknown`** → draft-for-approval, NEVER an autonomous reply.
  Root cause fixed here: the old default (`return "human"` for any stranger)
  routed the owner's private business partners (Rene Schuster / Oliver Triggs,
  Solar72) into the autonomous lane — 5 replies sent without PO, 05–07.09,
  one of them to a mistyped address (`triggoliver@` instead of
  `triggsoliver@`). The cron payload adds two more layers: allowlist refusal
  is now BLOCKING for sends (no longer observe-only), and a turn running on
  the fallback model (qwen) must never send email — draft only.
- The ONLY question to the owner: **"PO (dërgo) / JO (lëre)"**. "PO" → Halim
  sends via `scripts/ops_send_reply.py` and confirms; "JO" → archived; any
  other text = edit instruction → new draft → new PO/JO.
- Halim must NEVER duplicate lane A: registrations, verifications, welcomes,
  invoices and reminders are already emailed by the system — for those events
  he only informs the owner ("s'kërkohet veprim").
- Platform events reach Halim in real time via `services/ops_notify.py`
  (loopback hook). Guardrails live in `~/.openclaw/workspace/AVOKATIM-OPS.md`.
- **Audit trail (D-063)**: every `ops_send_reply.py` send is automatically
  ledgered in `data/ops/replies_log.csv`; the morning digest reports
  `replies_sent_24h` so the owner sees everything sent in his name. An
  LLM-free watchdog (`avokatim-watchdog.timer`, every 30 min) alarms the
  owner directly on Telegram when inbound mail sits unprocessed >60 min or
  the triage cron fails 3× in a row — detection never shares a failure mode
  with processing.
- **Personal lane (D-064)**: `arifi.arber@gmail.com` is the owner's single
  personal + operational account, not an AvokatIM-only address. Non-AvokatIM
  mail (bank, TikTok, private) is NEVER answered autonomously — Halim drafts,
  signs "Arbër" (not AvokatIM/Ava Legal), and asks PO/JO on Telegram. Halim
  now also manages the box (`scripts/ops_mailbox.py`: mark-read/archive/
  label) with a firewall protecting matter `+token@` aliases. Full protocol:
  `~/.openclaw/workspace/GMAIL-OPS.md`.

## Rules for agents (any LLM working here)

1. **New outbound email ⇒** all 7 languages in `i18n.py` + test-recipient
   suppression + a row in the tables above + (if operationally relevant) a
   `notify_ops` event so Halim stays aware.
2. **Tone of automated letters**: warm, personal, concrete next steps, signed
   "Arbër Arifi — AvokatIM" for milestone letters (verified, welcome) and
   "— AvokatIM" / "— Ekipi i AvokatIM" for transactional ones.
3. **Never email test/simulation recipients** — `_is_test_recipient` already
   guards `send_email`; keep new paths behind it.
4. **One-shot semantics for reminders** (a sent-at column), never repeated.
5. Milestone moments (first X of anything, founder badges) deserve a special
   paragraph — citizens and professionals both get thanked automatically;
   the owner is only informed.
