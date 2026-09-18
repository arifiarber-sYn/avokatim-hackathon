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
