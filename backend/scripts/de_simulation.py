"""End-to-end simulation of the German market-parity features (D-037) on the
DE host: a Kanzlei signs up, configures its fiscal identity, calculates RVG
fees, issues a hybrid ZUGFeRD invoice, exports DATEV, and a citizen posts a
case with Rechtsschutzversicherung which the lawyer sees badged.

Run:  .venv/bin/python scripts/de_simulation.py
Uses the live API on 127.0.0.1:8000 with Host: de.avokatiim.ai and cleans up
its own rows afterwards (emails use the .sim. test-recipient pattern).
"""
import asyncio
import sys
import uuid
from datetime import date
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import sim_guard  # noqa: E402

BASE = sim_guard.resolve_base()
DE_HOST = {"Host": "de.avokatiim.ai"}
RUN = uuid.uuid4().hex[:6]

PASS = "SimPass!2026x"
OFFICE_EMAIL = f"kanzlei.sim.{RUN}@gmail.com"
CITIZEN_EMAIL = f"buerger.sim.{RUN}@gmail.com"

ok_count = 0


def check(name: str, cond: bool, detail: str = ""):
    global ok_count
    mark = "OK " if cond else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))
    if cond:
        ok_count += 1
    else:
        sys.exit(f"ABORT: {name}")


async def main():
    async with httpx.AsyncClient(timeout=60) as c:
        print(f"\n=== DE-SIMULATION {RUN} ===")

        # 1. Office signup on the DE host
        r = await c.post(f"{BASE}/auth/signup", headers=DE_HOST, json={
            "practice_name": f"Kanzlei Sim {RUN}",
            "full_name": "Dr. Erika Simmann",
            "email": OFFICE_EMAIL,
            "password": PASS,
            "locale": "de",
            "accept_tos": True,
        })
        check("signup DE office", r.status_code == 201, str(r.status_code))
        auth = {**DE_HOST, "Authorization": f"Bearer {r.json()['access_token']}"}

        # 2. Fiscal identity + Bundesland + DATEV config
        r = await c.patch(f"{BASE}/firm", headers=auth, json={
            "address": "Maximilianstraße 2, 80539 München",
            "vat_number": "DE812345670",
            "fiscal_number": "143/123/45678",
            "bank_details": "Stadtsparkasse München · DE44 7015 0000 0000 1234 56",
            "iban": "DE44 7015 0000 0000 1234 56",
            "region": "BY",
            "datev_consultant_no": "12345",
            "datev_client_no": "678",
        })
        check("firm config (IBAN/region/DATEV)", r.status_code == 200,
              f"region={r.json().get('region')}")

        # 3. RVG calculator
        r = await c.get(f"{BASE}/fee-calc/rvg", headers=auth)
        check("RVG catalogue", r.status_code == 200 and len(r.json()["items"]) == 5)
        r = await c.post(f"{BASE}/fee-calc/rvg", headers=auth, json={
            "value_eur": 5000,
            "items": ["geschaeftsgebuehr", "verfahrensgebuehr", "termingebuehr"],
        })
        calc = r.json()
        check("RVG calc 5.000 €", r.status_code == 200 and calc["base_fee"] == "354.50",
              f"total {calc['total']} €")

        # 4. Contact + invoice from RVG lines -> hybrid ZUGFeRD PDF + XML
        r = await c.post(f"{BASE}/contacts", headers=auth, json={
            "display_name": f"Beispiel GmbH {RUN}",
            "kind": "company",
            "email": f"beispiel.sim.{RUN}@gmail.com",
            "address": "Beispielweg 2, 80331 München",
        })
        check("contact created", r.status_code in (200, 201))
        contact_id = r.json()["id"]

        r = await c.post(f"{BASE}/invoices", headers=auth, json={
            "contact_id": contact_id,
            "items": [
                {"description": f"{l['name']['de']} ({l['vv']})",
                 "quantity": "1", "unit_price": l["amount"]}
                for l in calc["lines"]
            ],
        })
        check("invoice created", r.status_code == 201, r.json().get("number"))
        inv = r.json()

        r = await c.get(f"{BASE}/invoices/{inv['id']}/pdf", headers=auth)
        check("hybrid PDF (factur-x embedded)",
              r.status_code == 200 and b"factur-x.xml" in r.content,
              f"{len(r.content)} bytes")
        r = await c.get(f"{BASE}/invoices/{inv['id']}/e-invoice.xml", headers=auth)
        check("e-invoice XML", r.status_code == 200
              and b"CrossIndustryInvoice" in r.content
              and b"DE812345670" in r.content)

        # 5. Mark sent + paid, export DATEV
        r = await c.patch(
            f"{BASE}/invoices/{inv['id']}/status", headers=auth,
            params={"new_status": "sent"},
        )
        check("invoice sent", r.status_code == 200)
        r = await c.patch(
            f"{BASE}/invoices/{inv['id']}/status", headers=auth,
            params={"new_status": "paid", "payment_reference": "SEPA-SIM"},
        )
        check("invoice paid", r.status_code == 200)

        today = date.today().isoformat()
        r = await c.get(f"{BASE}/export/datev", headers=auth,
                        params={"date_from": today, "date_to": today})
        text = r.content.decode("cp1252")
        check("DATEV EXTF export", r.status_code == 200
              and text.startswith('"EXTF";700;21;"Buchungsstapel";13;')
              and ";12345;678;" in text.split("\r\n")[0]
              and text.count(inv["number"]) >= 2,  # issue + payment rows
              f"{len(text.splitlines()) - 2} bookings")

        # 6. Deckungsanfrage template available
        r = await c.get(f"{BASE}/templates", headers=auth)
        codes = [t["code"] for t in r.json()]
        check("Deckungsanfrage template", "general.deckungsanfrage" in codes)

        # 7. Citizen posts a case with Rechtsschutz
        r = await c.post(f"{BASE}/public/citizen/signup", headers=DE_HOST, json={
            "full_name": "Bernd Bürger",
            "email": CITIZEN_EMAIL,
            "password": PASS,
            "locale": "de",
            "accept_privacy": True,
        })
        check("citizen signup", r.status_code == 201)
        citizen_token = r.json()["access_token"]

        # verify email directly in DB (simulation shortcut)
        from datetime import UTC, datetime

        from sqlalchemy import update

        from app.database import SessionLocal
        from app.models import CitizenUser

        async with SessionLocal() as db:
            await db.execute(update(CitizenUser)
                             .where(CitizenUser.email == CITIZEN_EMAIL)
                             .values(email_verified_at=datetime.now(UTC)))
            await db.commit()

        r = await c.post(f"{BASE}/public/citizen/cases", headers={
            **DE_HOST, "Authorization": f"Bearer {citizen_token}",
        }, json={
            "category": "labor",
            "description": (
                "Ich wurde am Montag fristlos gekündigt, nachdem ich seit vier "
                "Jahren im Betrieb arbeite. Eine Abmahnung gab es nie. Ich "
                "möchte gegen die Kündigung vorgehen und suche eine Anwältin "
                "für eine Kündigungsschutzklage in München."
            ),
            "city": "München",
            "urgency": "urgent",
            "has_legal_insurance": True,
            "insurer_name": "ARAG",
        })
        check("citizen case with RSV", r.status_code == 201)

        # 8. Lawyer sees the case with the insurance badge fields
        r = await c.get(f"{BASE}/marketplace/cases", headers=auth)
        mine = [x for x in r.json() if x.get("insurer_name") == "ARAG"]
        check("lawyer sees RSV badge", r.status_code == 200 and len(mine) == 1
              and mine[0]["has_legal_insurance"] is True)

        print(f"\n=== ALL {ok_count} CHECKS PASSED — cleaning up ===")

        from sqlalchemy import text as sqltext

        async with SessionLocal() as db:
            await db.execute(sqltext(
                "DELETE FROM citizen_users WHERE email = :e"), {"e": CITIZEN_EMAIL})
            await db.execute(sqltext(
                "DELETE FROM tenants WHERE name = :n"), {"n": f"Kanzlei Sim {RUN}"})
            await db.commit()
        print("cleanup done")


if __name__ == "__main__":
    sim_guard.assert_target_allowed(BASE, script="de_simulation.py")
    asyncio.run(main())
