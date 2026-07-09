"""Cross-tenant isolation check: creates two throwaway tenants via /auth/signup,
puts data in tenant A, and verifies tenant B cannot see or touch any of it.
Run against a live backend:  .venv/bin/python scripts/isolation_check.py
Cleans up both tenants at the end.
"""
import asyncio
import sys
import uuid

import httpx

BASE = "http://127.0.0.1:8000/api"
SUFFIX = uuid.uuid4().hex[:8]
PASSWORD = "isolation-check-pw-123"

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name} {detail}")
    if not ok:
        failures.append(name)


async def main() -> None:
    async with httpx.AsyncClient(timeout=30) as c:
        # --- two fresh tenants ---
        tokens = {}
        for label in ("a", "b"):
            r = await c.post(f"{BASE}/auth/signup", json={
                "practice_name": f"IsoTest {label.upper()} {SUFFIX}",
                "full_name": f"Iso {label.upper()}",
                "email": f"iso.{label}.{SUFFIX}@gmail.com",
                "password": PASSWORD,
            })
            r.raise_for_status()
            tokens[label] = r.json()["access_token"]
        ha = {"Authorization": f"Bearer {tokens['a']}"}
        hb = {"Authorization": f"Bearer {tokens['b']}"}

        # --- tenant A creates data ---
        contact = (await c.post(f"{BASE}/contacts", headers=ha, json={
            "display_name": f"Klient Iso {SUFFIX}", "kind": "person",
            "email": f"klient.iso.{SUFFIX}@gmail.com",
        })).json()
        matter = (await c.post(f"{BASE}/matters", headers=ha, json={
            "title": "Lëndë izolimi", "practice_area": "civil",
            "client_id": contact["id"],
        })).json()
        deadline = (await c.post(f"{BASE}/matters/{matter['id']}/deadlines", headers=ha, json={
            "title": "Afat izolimi", "due_at": "2027-01-15T10:00:00Z",
        })).json()
        invoice = (await c.post(f"{BASE}/invoices", headers=ha, json={
            "matter_id": matter["id"],
        })).json()
        msg = (await c.post(f"{BASE}/matters/{matter['id']}/messages", headers=ha, json={
            "body": "Mesazh izolimi",
        })).json()

        mid, cid = matter["id"], contact["id"]

        # --- tenant B must NOT reach any of it ---
        r = await c.get(f"{BASE}/matters/{mid}", headers=hb)
        check("matter blocked", r.status_code == 404, f"({r.status_code})")

        r = await c.get(f"{BASE}/contacts", headers=hb)
        ids = [x["id"] for x in r.json()] if r.status_code == 200 else []
        check("contact not listed", cid not in ids)

        r = await c.get(f"{BASE}/matters", headers=hb)
        ids = [x["id"] for x in r.json()] if r.status_code == 200 else []
        check("matter not listed", mid not in ids)

        r = await c.get(f"{BASE}/matters/{mid}/documents", headers=hb)
        check("documents blocked", r.status_code in (403, 404), f"({r.status_code})")

        r = await c.get(f"{BASE}/matters/{mid}/messages", headers=hb)
        check("messages blocked", r.status_code in (403, 404), f"({r.status_code})")

        r = await c.get(f"{BASE}/matters/{mid}/deadlines", headers=hb)
        check("deadlines blocked", r.status_code in (403, 404), f"({r.status_code})")

        r = await c.get(f"{BASE}/invoices", headers=hb)
        inv_ids = [x["id"] for x in r.json()] if r.status_code == 200 else []
        check("invoice not listed", invoice.get("id") not in inv_ids)

        r = await c.get(f"{BASE}/matters/{mid}/members", headers=hb)
        check("members blocked", r.status_code in (403, 404), f"({r.status_code})")

        # B's ICS feed must not contain A's deadline
        feed_url = (await c.get(f"{BASE}/calendar/feed-url", headers=hb)).json()["url"]
        ics = (await c.get(feed_url.replace("https://boraarifi.ai", "http://127.0.0.1:8000")
                           .replace("http://127.0.0.1:3000", "http://127.0.0.1:8000"))).text
        check("ICS isolated", str(deadline.get("id")) not in ics and "Afat izolimi" not in ics)

        # Corpus writes are platform-only now
        r = await c.post(f"{BASE}/corpus", headers=hb, json={
            "title": "Ligj i rremë", "text": "Neni 1\nTekst i mjaftueshëm për provë.",
        })
        check("corpus write blocked", r.status_code == 403, f"({r.status_code})")

        # Team ops: B cannot touch A's matter members
        r = await c.put(f"{BASE}/matters/{mid}/members", headers=hb, json={
            "restricted": False, "member_ids": [],
        })
        check("member update blocked", r.status_code in (403, 404), f"({r.status_code})")

        # Message posting cross-tenant
        r = await c.post(f"{BASE}/matters/{mid}/messages", headers=hb, json={"body": "hack"})
        check("message post blocked", r.status_code in (403, 404), f"({r.status_code})")

        assert msg  # created OK for A

    # --- cleanup: remove both throwaway tenants entirely ---
    sys.path.insert(0, ".")
    from sqlalchemy import text
    from app.database import SessionLocal

    async with SessionLocal() as db:
        await db.execute(
            text("DELETE FROM tenants WHERE name LIKE :p"), {"p": f"IsoTest % {SUFFIX}"}
        )
        await db.commit()
    print("cleanup done")

    if failures:
        print(f"\n{len(failures)} FAILURES: {failures}")
        sys.exit(1)
    print("\nALL ISOLATION CHECKS PASSED")


asyncio.run(main())
