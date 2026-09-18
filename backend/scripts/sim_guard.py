"""Production gate for the simulation harnesses (born 2026-09-18 incident).

`full_simulation.py`, `de_simulation.py` and `notary_simulation.py` drive the
LIVE API: they sign up throwaway offices, post synthetic cases and delete
everything again at the end. Nothing stopped them from running against the
production instance, where the case endpoints fan out real email/push/SMS to
every lawyer whose profile matches — and the harness deletes the cases seconds
later. Lawyers then received "new case matching your profile" mail for cases
that never existed in the marketplace.

Seen live: ~14 real lawyers, 69 notifications (2026-09-01 and 2026-09-18);
full report: `~/openclaw-knowledge/reports/avokatim-rrjedha-emails-2026-09-18.md`.

Rule enforced here: a harness refuses to start unless

  (a) it targets a non-production base URL
      (`AVOKATIM_SIM_BASE_URL=http://127.0.0.1:8001/api`), or
  (b) the operator passes `--allow-prod` on purpose.

The API-side gates in `app/api/marketplace.py` (test-recipient block on both
notify paths + the defence-in-depth check inside `_notify_*`) stay as the
second layer; this module only closes the door on the harness side.
"""
import os
import sys

PROD_BASE = "http://127.0.0.1:8000/api"


def resolve_base(default: str = PROD_BASE) -> str:
    """Target API base URL: env override first, production as the default."""
    return (os.environ.get("AVOKATIM_SIM_BASE_URL") or default).rstrip("/")


def assert_target_allowed(base: str, *, script: str) -> None:
    """Abort with a clear message when a harness is pointed at production
    without the explicit `--allow-prod` flag."""
    if base != PROD_BASE:
        return
    if "--allow-prod" in sys.argv:
        print(f"[sim_guard] {script}: --allow-prod dhënë — xhirim mbi PRODHIMIN, "
              "njoftimet e avokatëve mbeten të bllokuara nga portat e API-t.")
        return
    print(
        f"REFUZOHET: {script} synon instancën e PRODHIMIT ({base}).\n"
        "  Ky harness krijon raste sintetike dhe i fshin ato; kundër prodhimit\n"
        "  ai njofton avokatë REALË për raste që nuk ekzistojnë.\n"
        "  Zgjidh njërën:\n"
        "    1) instancë prove:  AVOKATIM_SIM_BASE_URL=http://127.0.0.1:8001/api \\\n"
        f"                          .venv/bin/python scripts/{script}\n"
        "    2) me vetëdije kundër prodhimit:  shto --allow-prod\n"
        "  Konteksti: reports/avokatim-rrjedha-emails-2026-09-18.md",
        file=sys.stderr,
    )
    raise SystemExit(2)
