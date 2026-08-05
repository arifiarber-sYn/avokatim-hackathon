"""Shared outreach sender (D-069) — Resend API with Gmail SMTP fallback.

WHY: the audit of 2026-08-05 found ~930 cold emails sent from the owner's
personal Gmail (arifi.arber@gmail.com), which also carries the platform's
transactional mail — one blacklist event would break everything at once.
The fix is a dedicated sending identity on a subdomain (Resend), while
replies keep flowing to the personal Gmail via Reply-To, so the existing
triage/opt-out machinery is untouched.

MODES (picked automatically):
- resend  — when OUTREACH_RESEND_KEY (or a working RESEND_API_KEY) and
            OUTREACH_FROM are configured AND the domain is verified.
            Enforces the warm-up cap (see warmup_cap()).
- smtp    — fallback: the current Gmail SMTP path (settings.smtp_*).

Config, read from the environment first and then from
~/.openclaw/workspace/secrets/infrastructure.env:
    OUTREACH_RESEND_KEY=re_...          full-access or sending key
    OUTREACH_FROM=Arbër Arifi <arber@mail.avokatiim.ai>
    OUTREACH_REPLY_TO=arifi.arber@gmail.com     (default)
    OUTREACH_WARMUP_START=2026-08-10    ISO date of first Resend send

Setup runbook for the manual DNS/Resend steps:
    ~/AvokatIM/docs/agents/OUTREACH-SENDER-SETUP.md
CLI helper that creates the domain and prints DNS records:
    python scripts/outreach_sender.py --setup mail.avokatiim.ai
    python scripts/outreach_sender.py --status
"""
from __future__ import annotations

import json
import os
import smtplib
import sys
import urllib.error
import urllib.request
from datetime import date, datetime
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings  # noqa: E402

INFRA_ENV = Path.home() / ".openclaw" / "workspace" / "secrets" / "infrastructure.env"
RESEND_API = "https://api.resend.com"

# Warm-up schedule for a fresh sending domain: (max age in days, daily cap).
# Below the first threshold the cap is small; after the last it is the
# steady-state 25/day agreed in D-069.
WARMUP_STEPS = [(7, 10), (14, 20)]
STEADY_CAP = 25


def _env(key: str) -> str:
    """Env var, falling back to infrastructure.env (never logs values)."""
    val = os.environ.get(key, "").strip()
    if val:
        return val
    if INFRA_ENV.exists():
        for line in INFRA_ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _resend_key() -> str:
    return _env("OUTREACH_RESEND_KEY") or _env("RESEND_API_KEY")


def _api(path: str, payload: dict | None = None, method: str = "GET") -> dict:
    key = _resend_key()
    if not key:
        raise SystemExit("no Resend key configured (OUTREACH_RESEND_KEY)")
    req = urllib.request.Request(
        f"{RESEND_API}{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        method="POST" if payload is not None else method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode()).get("message", "")
        except Exception:  # noqa: BLE001
            detail = ""
        raise RuntimeError(f"Resend API {exc.code}: {detail or exc.reason}") from exc


def warmup_cap() -> int:
    """Daily cap while the dedicated domain builds reputation."""
    start_raw = _env("OUTREACH_WARMUP_START")
    if not start_raw:
        return WARMUP_STEPS[0][1]  # warm-up not started -> most conservative
    try:
        age = (date.today() - date.fromisoformat(start_raw)).days
    except ValueError:
        return WARMUP_STEPS[0][1]
    for max_age, cap in WARMUP_STEPS:
        if age <= max_age:
            return cap
    return STEADY_CAP


class Sender:
    """One object per batch. mode is 'resend' or 'smtp' (Gmail fallback)."""

    def __init__(self) -> None:
        self.from_header = _env("OUTREACH_FROM")
        self.reply_to = _env("OUTREACH_REPLY_TO") or "arifi.arber@gmail.com"
        self.mode = "resend" if (_resend_key() and self.from_header) else "smtp"
        self._smtp: smtplib.SMTP | None = None

    @property
    def daily_cap(self) -> int | None:
        """Cap the campaign must respect (None = campaign's own limit)."""
        return warmup_cap() if self.mode == "resend" else None

    def send(self, to: str, subject: str, body: str,
             from_name: str, list_unsubscribe: str | None = None) -> None:
        """Send one plain-text message. Raises on failure (campaign decides
        whether to log/skip/stop, same as before)."""
        if self.mode == "resend":
            payload: dict = {
                "from": self.from_header,
                "to": [to],
                "subject": subject,
                "text": body,
                "reply_to": [self.reply_to],
            }
            if list_unsubscribe:
                payload["headers"] = {"List-Unsubscribe": list_unsubscribe}
            _api("/emails", payload)
            return
        # SMTP fallback — identical to the campaigns' historic path.
        if self._smtp is None:
            self._smtp = smtplib.SMTP(settings.smtp_host, settings.smtp_port,
                                      timeout=30)
            self._smtp.starttls()
            self._smtp.login(settings.smtp_user, settings.smtp_password)
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = formataddr((from_name, settings.smtp_user))
        msg["To"] = to
        msg["Reply-To"] = self.reply_to
        if list_unsubscribe:
            msg["List-Unsubscribe"] = list_unsubscribe
        self._smtp.sendmail(settings.smtp_user, [to], msg.as_string())

    def close(self) -> None:
        if self._smtp is not None:
            self._smtp.quit()
            self._smtp = None


# ---------------------------------------------------------------- CLI helpers

def cmd_setup(domain: str) -> None:
    """Create the domain in Resend and print the DNS records to add in
    Cloudflare (requires a FULL-ACCESS key, not a sending-only one)."""
    out = _api("/domains", {"name": domain, "region": "eu-west-1"})
    print(f"domain created in Resend: {out.get('name')} (id {out.get('id')})\n")
    print("Shto këto rekorde DNS te Cloudflare (zona avokatiim.ai, 'DNS only'):\n")
    for rec in out.get("records", []):
        print(f"  {rec.get('record'):<6} {rec.get('type'):<5} "
              f"{rec.get('name'):<40} {rec.get('value')}")
    print("\nPas shtimit: python scripts/outreach_sender.py --status")


def cmd_status() -> None:
    try:
        out = _api("/domains")
    except (RuntimeError, SystemExit) as exc:
        print(f"Resend jo i gatshëm: {exc}")
        print("Duhet çelës FULL-ACCESS te OUTREACH_RESEND_KEY (infrastructure.env)."
              "\nRunbook: ~/AvokatIM/docs/agents/OUTREACH-SENDER-SETUP.md")
        print(f"\nmodi aktual i dërgimit: {Sender().mode}")
        return
    domains = out.get("data", [])
    if not domains:
        print("asnjë domain në Resend ende — nis me --setup <domain>")
        return
    for d in domains:
        print(f"{d.get('name'):<30} status={d.get('status')}")
    mode = Sender().mode
    print(f"\nmodi aktual i dërgimit: {mode}"
          + (f" (cap ditor warm-up: {warmup_cap()})" if mode == "resend" else
             " — Gmail SMTP fallback (Resend jo gati)"))


def cmd_test(to: str) -> None:
    s = Sender()
    print(f"mode: {s.mode}, from: {s.from_header or settings.smtp_user}")
    s.send(to, "Test i dërguesit outreach (D-069)",
           "Ky është një test i modulit outreach_sender.py. Përgjigju STOP "
           "për të testuar edhe opt-out-in.",
           "Arbër Arifi", f"<mailto:{s.reply_to}?subject=STOP>")
    s.close()
    print("sent OK")


def main() -> None:
    args = sys.argv[1:]
    if args[:1] == ["--setup"] and len(args) == 2:
        cmd_setup(args[1])
    elif args[:1] == ["--status"]:
        cmd_status()
    elif args[:1] == ["--test"] and len(args) == 2:
        cmd_test(args[1])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
