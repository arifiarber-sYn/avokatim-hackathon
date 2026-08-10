"""Per-project 24/7 health monitor — NO LLM anywhere in the chain (D-065).

Complements the mail watchdog (D-063): that one watches the email pipeline,
this one watches every project on the machine. Pure Python + systemctl +
HTTP + docker + Telegram Bot API. Runs from an OpenClaw cron every 6h.

For each project it checks the relevant systemd --user services and, where
one exists, an HTTP health endpoint ("up" = the socket answered, any status
code that is not a 5xx and not a refused connection). It also does a machine
sweep: `systemctl --user --failed`, disk free on /, and docker container count.

Repair policy follows the D-064 roster: restart failed services ONLY for the
"safe" projects; TotoTrading (real money) and BoraLaw (frozen) are never
touched — they are report-only.

Usage:
    python scripts/ops_roster_health.py            # check + Telegram summary
    python scripts/ops_roster_health.py --status   # print only, never send
    python scripts/ops_roster_health.py --repair    # also restart failed safe svcs
"""
import json
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402

OPENCLAW_CFG = Path.home() / ".openclaw" / "openclaw.json"
STATUS_ONLY = "--status" in sys.argv
DO_REPAIR = "--repair" in sys.argv

# name -> (services, health_url|None, repairable)
PROJECTS: dict[str, dict] = {
    "AvokatIM": {
        "services": ["avokatim.service", "avokatim-frontend.service",
                     "avokatim-tunnel.service", "openclaw-gateway.service"],
        "url": "http://127.0.0.1:8000/api/health",
        "repairable": True,
    },
    "OpsHub": {
        "services": ["opshub.service"],
        "url": "http://127.0.0.1:3010/api/health",
        "repairable": True,
    },
    "EdaS": {
        # NOTE (D-070): edas-acestep / edas-tools are on-demand GPU workers.
        # EdaS's GPU manager (~/EdaS/data/gpu_manager.json: auto_release=true,
        # idle_minutes=15) deliberately STOPS edas-acestep when idle to free the
        # RTX 5090's VRAM. Monitoring it as "must be active" produced false
        # alarms and restart-fights with the manager, so it is intentionally not
        # listed here. edas.service + edas-frontend stay always-on.
        "services": ["edas.service", "edas-frontend.service"],
        "url": "http://127.0.0.1:8002/api/health",
        "repairable": True,  # careful: two-agent rule for CODE, restart is ops-only
    },
    "NaturalBeauty": {
        "services": ["naturalbeauty-web.service", "naturalbeauty-voice.service",
                     "naturalbeauty-webtunnel.service"],
        "url": "http://127.0.0.1:3005/",
        "repairable": True,
    },
    "TotoTrading": {
        "services": ["toto-trading.service", "toto-liq-collector.service"],
        "url": "http://127.0.0.1:8001/",  # 401 = up (auth-protected)
        "repairable": False,  # real money — observe only
    },
    "sYn": {
        "services": ["syn-emulator.service"],
        "url": None,
        "repairable": False,
    },
}


def _svc_active(name: str) -> bool:
    r = subprocess.run(["systemctl", "--user", "is-active", name],
                       capture_output=True, text=True)
    return r.stdout.strip() == "active"


def _http_up(url: str | None) -> bool | None:
    """True=answered (non-5xx), False=down/5xx, None=no url."""
    if not url:
        return None
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status < 500
    except urllib.error.HTTPError as e:  # 4xx (e.g. 401/404) = process is up
        return e.code < 500
    except Exception:
        return False


def _failed_units() -> list[str]:
    r = subprocess.run(["systemctl", "--user", "--failed", "--no-legend",
                        "--plain"], capture_output=True, text=True)
    return [ln.split()[0] for ln in r.stdout.splitlines() if ln.strip()]


def _disk_free_pct() -> int:
    total, _, free = shutil.disk_usage("/")
    return round(free / total * 100)


def _docker_count() -> int:
    r = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True)
    return len([x for x in r.stdout.splitlines() if x.strip()])


def _restart(name: str) -> bool:
    r = subprocess.run(["systemctl", "--user", "restart", name],
                       capture_output=True, text=True)
    return r.returncode == 0 and _svc_active(name)


def check() -> tuple[list[str], list[str], list[str], list[str]]:
    """Returns (problem_lines, repair_lines, ok_names, unresolved_names).

    A project counts as *unresolved* only if it still has a problem AFTER any
    repair attempt: not repairable, repair not requested, a restart failed, or
    the HTTP endpoint still refuses. A fully self-healed project is NOT an error
    — this keeps the 6h cron green when a flap was fixed automatically (D-070)."""
    problems: list[str] = []
    repairs: list[str] = []
    ok: list[str] = []
    unresolved: list[str] = []
    for name, cfg in PROJECTS.items():
        down_svcs = [s for s in cfg["services"] if not _svc_active(s)]
        http = _http_up(cfg["url"])
        healthy = not down_svcs and (http is not False)
        if healthy:
            ok.append(name)
            continue
        detail = []
        if down_svcs:
            detail.append("svc jofunksionale: " + ", ".join(down_svcs))
        if http is False:
            detail.append(f"health {cfg['url']} nuk përgjigjet")
        problems.append(f"• {name}: " + "; ".join(detail))
        # repair only safe projects, only their down services
        repaired_all = False
        if DO_REPAIR and cfg["repairable"] and down_svcs:
            results = []
            for s in down_svcs:
                ok_r = _restart(s)
                results.append(ok_r)
                repairs.append(f"  ↳ {name}: restart {s} → "
                               + ("OK" if ok_r else "DËSHTOI"))
            # re-verify: services back AND http not refusing after restart
            repaired_all = all(results) and (_http_up(cfg["url"]) is not False)
        if not repaired_all:
            unresolved.append(name)
    return problems, repairs, ok, unresolved


def build_report(problems, repairs, ok, unresolved) -> str:
    failed = _failed_units()
    disk = _disk_free_pct()
    dockers = _docker_count()
    head = "🩺 Roster-health"
    lines = [head]
    if problems:
        lines.append("PROBLEME:")
        lines.extend(problems)
        if repairs:
            lines.append("Riparime (vetëm projektet e sigurta):")
            lines.extend(repairs)
        if not unresolved:
            lines.append("✅ Të gjitha u vetë-riparuan.")
        else:
            lines.append("⚠️ Ende të pazgjidhura: " + ", ".join(unresolved))
    else:
        lines.append("✅ Të gjitha projektet aktive.")
    lines.append(f"OK: {', '.join(ok) if ok else '—'}")
    lines.append(f"Makina: disk {disk}% lirë · docker {dockers} up · "
                 f"failed units {len(failed)}"
                 + (": " + ", ".join(failed) if failed else ""))
    return "\n".join(lines)


def _telegram_creds() -> tuple[str, str] | None:
    try:
        tg = json.loads(OPENCLAW_CFG.read_text())["channels"]["telegram"]
        token = tg.get("botToken") or ""
        chat = str(settings.openclaw_hook_to or (tg.get("allowFrom") or [""])[0])
        if token and chat:
            return token, chat
    except Exception:
        pass
    return None


def send_telegram(text: str) -> bool:
    creds = _telegram_creds()
    if not creds:
        return False
    token, chat = creds
    try:
        data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage", data=data)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return bool(json.loads(resp.read()).get("ok"))
    except Exception:
        return False


def main() -> int:
    problems, repairs, ok, unresolved = check()
    report = build_report(problems, repairs, ok, unresolved)
    print(report)
    if not STATUS_ONLY:
        send_telegram(report)
    # Exit non-zero ONLY on genuinely unresolved problems, so a successful
    # self-repair no longer trips the cron into a red "error" state (D-070).
    return 1 if unresolved else 0


if __name__ == "__main__":
    raise SystemExit(main())
