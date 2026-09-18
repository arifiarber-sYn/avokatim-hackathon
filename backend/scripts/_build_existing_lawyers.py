"""Build recipients-ekzistues.csv: visible lawyers NOT yet sent the demo (18.09 15:00).

Read-only against the DB + the send ledger. Writes only the CSV in the evidence dir.
Exclusions (PO i Klloshës 18.09 15:27):
  - arifi.arber@gmail.com (Kllosha / "Bora Arifi" row)
  - zyrjaligjoreshukriu@gmail.com (Valtida Shukriu — never without permission)
  - anyone already logged `ok` for tag demo-2026-09-18 (15:00 send)
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text  # noqa: E402
from app.config import PROJECT_DIR, settings  # noqa: E402

LEDGER = PROJECT_DIR / "data" / "ops" / "demo_email_sent.csv"
OUT = PROJECT_DIR / "data" / "evidence" / "demo-2026-09-18" / "recipients-ekzistues.csv"
NEVER = {"arifi.arber@gmail.com", "zyrjaligjoreshukriu@gmail.com"}


def already_sent() -> dict[str, str]:
    done: dict[str, str] = {}
    if LEDGER.exists():
        with LEDGER.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("status") == "ok":
                    done[row["email"].strip().lower()] = row.get("tag", "")
    return done


def nice(name: str) -> str:
    # Ledgeri i 15:00 përdori emrin siç ishte në listë; këtu vetëm kapitalizimi
    # i emrave gjithë-kapital ose gjithë-vogël rregullohet për përshëndetjen.
    return name.title() if (name.isupper() or name.islower()) else name


eng = create_engine(settings.database_url)
q = """
SELECT u.email, u.full_name, lp.is_visible, u.is_active AS user_active
FROM lawyer_profiles lp JOIN users u ON u.id = lp.user_id
WHERE lp.is_visible = true
ORDER BY u.email
"""
with eng.connect() as c:
    rows = [dict(r._mapping) for r in c.execute(text(q))]

sent = already_sent()
send_list, excluded = [], []
for r in rows:
    e = r["email"].strip()
    el = e.lower()
    if el in NEVER:
        excluded.append({"email": e, "name": r["full_name"], "why": "never/Valtida ose Kllosha"})
    elif el in sent:
        excluded.append({"email": e, "name": r["full_name"], "why": f"marre me pare ({sent[el]})"})
    else:
        send_list.append({"email": e, "name": nice(r["full_name"].strip())})

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["email", "name"])
    w.writeheader()
    w.writerows(send_list)

print(json.dumps({
    "visible_total": len(rows),
    "to_send": len(send_list),
    "excluded": len(excluded),
    "recipients_csv": str(OUT),
    "send": send_list,
    "excluded_detail": excluded,
}, ensure_ascii=False, indent=2))
