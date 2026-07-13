"""Collect the public ONK notary directory (noteria-ks.org/noteret) into
data/notaries.json, which backs the public /noteret page.

The page is a single HTML table. Emails are obfuscated with Cloudflare's
email-protection (XOR with the first byte) and are decoded here. Public
professional contact data published by the Kosovo Notary Chamber; the JSON
stays in data/ (git-ignored) like the OAK registry.
"""
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

OUT = Path(__file__).resolve().parents[2] / "data" / "notaries.json"
URL = "https://www.noteria-ks.org/noteret/"
UA = "AvokatIM directory sync (contact: arifi.arber@gmail.com)"

ROW_RE = re.compile(r"<tr class=\"row-\d+[^\"]*\"[^>]*>(.*?)</tr>", re.S)
CELL_RE = re.compile(r"<td class=\"column-(\d)\">(.*?)</td>", re.S)
CFEMAIL_RE = re.compile(r'data-cfemail="([0-9a-f]+)"')


def decode_cfemail(hexstr: str) -> str:
    data = bytes.fromhex(hexstr)
    key = data[0]
    return bytes(b ^ key for b in data[1:]).decode("utf-8")


def strip_tags(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = text.replace("&#160;", " ").replace("&nbsp;", " ").replace("&amp;", "&")
    text = re.sub(r'[”“]', '"', text)
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    r = httpx.get(URL, headers={"User-Agent": UA}, timeout=30, follow_redirects=True)
    r.raise_for_status()
    notaries = []
    for row_match in ROW_RE.finditer(r.text):
        cells = {int(n): frag for n, frag in CELL_RE.findall(row_match.group(1))}
        if not cells.get(1):
            continue
        name = strip_tags(cells[1])
        if not name or name.lower().startswith("emri"):
            continue  # header row
        email = ""
        cf = CFEMAIL_RE.search(cells.get(3, ""))
        if cf:
            try:
                email = decode_cfemail(cf.group(1)).lower()
            except (ValueError, UnicodeDecodeError):
                email = ""
        notaries.append({
            "name": name,
            "phone": strip_tags(cells.get(2, "")),
            "email": email,
            "address": strip_tags(cells.get(4, "")),
            "city": strip_tags(cells.get(5, "")),
        })

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "source": URL,
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "notaries": notaries,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    cities = sorted({n["city"] for n in notaries if n["city"]})
    with_email = sum(1 for n in notaries if n["email"])
    print(f"saved {len(notaries)} notaries ({with_email} with email) "
          f"across {len(cities)} cities to {OUT}")
    sys.exit(0 if len(notaries) > 100 else 1)


main()
