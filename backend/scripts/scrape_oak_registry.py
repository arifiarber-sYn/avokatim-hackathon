"""Collect the public OAK lawyer registry (name, region, city, phone, email)
into data/oak_registry.csv. The registry is public professional contact data
published by the Kosovo Bar Association at oak-ks.org/avokatet.

Polite scraper: sequential, 0.5s delay between pages, honest User-Agent.
Output lands in data/ which is git-ignored (personal data stays local).
"""
import csv
import re
import sys
import time
from pathlib import Path

import httpx

OUT = Path(__file__).resolve().parents[2] / "data" / "oak_registry.csv"
BASE = "https://www.oak-ks.org/avokatet"
UA = "AvokatIM registry sync (contact: arifi.arber@gmail.com)"
STEP = 21  # entries per page; pagination uses ?page=/<offset>

BLOCK_RE = re.compile(
    r"<h5>(?P<name>[^<]+)</h5>\s*"
    r"(?P<body>(?:\s*<p><strong>[^<]+</strong>[^<]*</p>)+)",
    re.S,
)
FIELD_RE = re.compile(r"<p><strong>\s*(?P<key>[^:<]+):?\s*</strong>\s*(?P<val>[^<]*)</p>")


def parse_page(html: str) -> list[dict]:
    rows = []
    for m in BLOCK_RE.finditer(html):
        fields = {
            f.group("key").strip().rstrip(":").lower(): f.group("val").strip()
            for f in FIELD_RE.finditer(m.group("body"))
        }
        rows.append({
            "name": m.group("name").strip(),
            "region": fields.get("regjioni", ""),
            "city": fields.get("qyteti", ""),
            "phone": fields.get("mob", ""),
            "email": fields.get("e-mail", "").strip().lower(),
        })
    return rows


def main() -> None:
    last_offset = int(sys.argv[1]) if len(sys.argv) > 1 else 1449
    all_rows: list[dict] = []
    with httpx.Client(headers={"User-Agent": UA}, timeout=30, follow_redirects=True) as c:
        for offset in range(0, last_offset + 1, STEP):
            url = BASE if offset == 0 else f"{BASE}?page=/{offset}"
            for attempt in range(3):
                try:
                    r = c.get(url)
                    r.raise_for_status()
                    break
                except Exception as exc:
                    print(f"  retry {attempt + 1} for {url}: {exc}")
                    time.sleep(3)
            else:
                print(f"  SKIPPED {url}")
                continue
            rows = parse_page(r.text)
            all_rows.extend(rows)
            print(f"page {offset:>5}: {len(rows)} lawyers (total {len(all_rows)})")
            time.sleep(0.5)

    # de-dup by (name, email)
    seen, unique = set(), []
    for row in all_rows:
        key = (row["name"], row["email"])
        if key not in seen:
            seen.add(key)
            unique.append(row)

    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["name", "region", "city", "phone", "email"])
        w.writeheader()
        w.writerows(unique)

    with_email = sum(1 for r in unique if "@" in r["email"])
    print(f"\nsaved {len(unique)} lawyers to {OUT} ({with_email} with email)")


main()
