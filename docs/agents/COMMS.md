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

All templates live in `backend/app/i18n.py` in **6 languages**
(sq/sr/tr/bs/en/zh) and are sent via `send_email` in
`backend/app/services/notifications.py`, which **suppresses test/simulation
recipients** (`_is_test_recipient`).

### Lawyers / notaries (tenant accounts)

| Trigger | Key(s) | Code |
|---|---|---|
| Signup | `lawyer_verify_*` (confirm email), `lawyer_welcome_*` / `notary_welcome_*` (next steps) | `api/auth.py` |
| 1h after signup, public profile still inactive | `lawyer_profile_nudge_*` (one-shot) | `services/notifications.py` |
| License verified (auto or manual) | `verify_approved_*` — **warm thank-you letter**, + `verify_approved_founder` paragraph when the Founder badge applies | `services/license_verify.py`, `api/platform.py` |
| License rejected | `verify_rejected_*` | `api/platform.py` |
| New matching marketplace case / directed case / SOS | `case_match_*`, `case_directed_*`, `sos_alert_*` (+ SMS variants) | `api/marketplace.py` |
| New consultation booking | `booking_new_*` | `api/bookings.py` |
| Monthly subscription invoice / overdue / trial ending | `platform_invoice_*`, `platform_overdue_*`, `trial_ending_*` | `services/platform_billing.py` |
| Deadline reminders | `reminder_*` | `services/notifications.py` |
| Team invite | (invite email) | `api/team.py` |

### Citizens

| Trigger | Key(s) | Code |
|---|---|---|
| Signup | `citizen_verify_*` (confirm email) | `api/marketplace.py` |
| 1h after signup, email still unverified | `citizen_verify_reminder_*` (one-shot) | `services/notifications.py` |
| Email confirmed | `citizen_welcome_*` — **thank-you letter** (Ava, post case, directory, documents, SOS; free forever) | `api/marketplace.py` |
| Password reset | `citizen_reset_*` | `api/marketplace.py` |
| Lawyer claimed their case / new message | `case_claimed_*`, `case_message_*` | `api/marketplace.py` |
| Matter portal invite / new message / signature | `case_portal_ready_*`, `email_new_message_*`, `email_signed_*`, `email_signature_*` | `api/intake.py`, `api/portal.py`, `api/collab.py` |
| Client invoice | `email_invoice_*` | `api/billing.py` |

### Outreach (acquisition)

Daily batch of 30 introduction emails to OAK lawyers (then ONK notaries) via
`avokatim-outreach.timer` → `backend/scripts/oak_outreach_campaign.py`. Dedup +
suppression of already-registered addresses; log `data/outreach.log`.

## Lane B — Halim (OpenClaw) correspondence protocol

- `scripts/ops_inbox_triage.py` (cron every 10 min, read-only IMAP PEEK)
  classifies inbound mail; human mail → Telegram with context + a
  **final, ready-to-send draft** signed "Arbër Arifi — AvokatIM".
- The ONLY question to the owner: **"PO (dërgo) / JO (lëre)"**. "PO" → Halim
  sends via `scripts/ops_send_reply.py` and confirms; "JO" → archived; any
  other text = edit instruction → new draft → new PO/JO.
- Halim must NEVER duplicate lane A: registrations, verifications, welcomes,
  invoices and reminders are already emailed by the system — for those events
  he only informs the owner ("s'kërkohet veprim").
- Platform events reach Halim in real time via `services/ops_notify.py`
  (loopback hook). Guardrails live in `~/.openclaw/workspace/AVOKATIM-OPS.md`.

## Rules for agents (any LLM working here)

1. **New outbound email ⇒** all 6 languages in `i18n.py` + test-recipient
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
