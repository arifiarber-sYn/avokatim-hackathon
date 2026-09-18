"""End-to-end simulation of the second paying profession: a notary office.
Signup with profession=notary -> profile + ONK license -> verification ->
public /noteret listing with booking -> citizen books with a prepared
dossier (PDF draft) -> the notary downloads it and confirms.
Run against the live backend:  .venv/bin/python scripts/notary_simulation.py
Cleans up the throwaway tenant + citizen at the end.
"""
import asyncio
import base64
import io
import sys
import time
import uuid
from pathlib import Path

import httpx

sys.path.insert(0, ".")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import sim_guard  # noqa: E402

BASE = sim_guard.resolve_base()
SUFFIX = uuid.uuid4().hex[:6]
PW = "simulimi-noteri-pw-01"

results: list[tuple[str, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    kind = "PASS" if ok else "FAIL"
    print(f"{kind:6s} {name}  {detail}")
    results.append((kind, name))


def make_pdf(text: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as pdfcanvas

    buf = io.BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=A4)
    y = 800
    for line in text.splitlines():
        c.drawString(50, y, line)
        y -= 18
    c.save()
    return buf.getvalue()


async def cleanup() -> None:
    from sqlalchemy import text as sqltext

    from app.database import SessionLocal

    async with SessionLocal() as db:
        await db.execute(sqltext(
            "DELETE FROM citizen_users WHERE email LIKE 'qytetari.sim.%@gmail.com'"))
        await db.execute(sqltext(
            "DELETE FROM tenants WHERE name LIKE 'Zyra Noteriale Sim %'"))
        await db.commit()
    print("\ncleanup done")


async def main() -> None:
    t0 = time.time()
    async with httpx.AsyncClient(timeout=120) as c:
        # Rate limits are per-IP; clear counters so reruns stay deterministic
        import redis.asyncio as aioredis

        from app.config import settings as app_settings
        rr = aioredis.from_url(app_settings.redis_url)
        for pattern in ("avokatim:rl:citizen_signup:*", "avokatim:rl:citizen_login:*",
                        "avokatim:rl:citizen_booking:*"):
            async for rkey in rr.scan_iter(pattern):
                await rr.delete(rkey)
        await rr.aclose()

        print("=== 1. REGJISTRIMI I ZYRËS NOTERIALE ===")
        r = await c.post(f"{BASE}/auth/signup", json={
            "practice_name": f"Zyra Noteriale Sim {SUFFIX}",
            "full_name": "Noteri Simulues",
            "email": f"noteri.sim.{SUFFIX}@gmail.com",
            "password": PW, "locale": "sq",
            "profession": "notary", "accept_tos": True,
        })
        check("signup me profession=notary", r.status_code == 201)
        h = {"Authorization": f"Bearer {r.json()['access_token']}"}

        r = await c.get(f"{BASE}/auth/me", headers=h)
        check("/auth/me kthen tenant_profession=notary",
              r.status_code == 200 and r.json().get("tenant_profession") == "notary")

        print("\n=== 2. PROFILI + LICENCA ONK + TERMINET ===")
        r = await c.put(f"{BASE}/marketplace/profile", headers=h, json={
            "is_visible": True, "bio": "Zyrë noteriale në qendër.",
            "practice_areas": [], "cities": ["Prishtinë"],
            "languages": ["sq"], "oak_license_no": f"ONK-SIM-{SUFFIX}",
        })
        check("profili me licencë ONK (në pritje të verifikimit)",
              r.status_code == 200 and r.json().get("verification_status") == "pending")
        r = await c.put(f"{BASE}/marketplace/booking-settings", headers=h, json={
            "enabled": True,
            "slots": [{"day": d, "start": "09:00", "end": "15:00"} for d in range(7)],
        })
        check("orari i termineve u vendos", r.status_code == 200)

        r = await c.get(f"{BASE}/public/tools/notaries")
        names = [n["name"] for n in r.json().get("notaries", [])]
        check("PA verifikim noteri NUK del në /noteret",
              "Noteri Simulues" not in names, f"{len(names)} noterë")

        # Operator approves (same effect as the /platform decide endpoint)
        from sqlalchemy import text as _vsql

        from app.database import SessionLocal as _VSession
        async with _VSession() as _vdb:
            await _vdb.execute(_vsql(
                "UPDATE lawyer_profiles SET verification_status='verified', "
                "verified_at=now() WHERE oak_license_no = :lic"),
                {"lic": f"ONK-SIM-{SUFFIX}"})
            await _vdb.commit()

        r = await c.get(f"{BASE}/public/tools/notaries")
        entry = next((n for n in r.json().get("notaries", [])
                      if n["name"] == "Noteri Simulues"), None)
        check("pas verifikimit del në /noteret me badge + booking",
              entry is not None and entry.get("registered") is True
              and entry.get("booking") is True and entry.get("profile_id"))
        profile_id = entry["profile_id"] if entry else None

        r = await c.get(f"{BASE}/public/lawyers")
        check("noteri NUK del në drejtorinë e avokatëve",
              not any(x["full_name"] == "Noteri Simulues" for x in r.json()))

        print("\n=== 3. GARDHI LIGJOR: PA TREG RASTESH ===")
        r = await c.post(f"{BASE}/marketplace/cases/{uuid.uuid4()}/claim", headers=h)
        check("tentimi për të marrë rast nga tregu REFUZOHET (403)",
              r.status_code == 403, r.text[:80])

        print("\n=== 4. QYTETARI REZERVON TERMIN ME DOSJE ===")
        cit_email = f"qytetari.sim.{SUFFIX}@gmail.com"
        r = await c.post(f"{BASE}/public/citizen/signup", json={
            "full_name": "Qytetar Simulues", "email": cit_email,
            "password": "qytetari-pw-123", "locale": "sq", "accept_privacy": True,
        })
        check("regjistrimi i qytetarit", r.status_code == 201)
        cit_id = r.json()["citizen"]["id"]
        ch = {"Authorization": f"Bearer {r.json()['access_token']}"}

        from app.security import create_purpose_token
        vtoken = create_purpose_token("citizen_verify", uuid.UUID(cit_id), minutes=60)
        r = await c.post(f"{BASE}/public/citizen/verify-email", json={"token": vtoken})
        check("verifikimi i email-it të qytetarit", r.status_code == 200)

        r = await c.get(f"{BASE}/public/lawyers/{profile_id}/slots")
        slots = r.json().get("slots", []) if r.status_code == 200 else []
        check("terminet e lira publikohen", len(slots) > 0, f"{len(slots)} termine")

        draft = make_pdf("KONTRATE PER SHITBLERJEN E VETURES\nDraft nga /dokumentet")
        r = await c.post(f"{BASE}/public/citizen/bookings", headers=ch, json={
            "profile_id": profile_id, "starts_at": slots[0],
            "note": "Shitblerje veture — kam draftin gati.",
            "attachment_name": "kontrata-draft.pdf",
            "attachment_b64": base64.b64encode(draft).decode(),
        })
        check("rezervimi me dosje paraprake (PDF)", r.status_code == 201
              and r.json().get("attachment_name") == "kontrata-draft.pdf")
        booking_id = r.json()["id"]

        print("\n=== 5. NOTERI E SHEH DOSJEN DHE KONFIRMON ===")
        r = await c.get(f"{BASE}/marketplace/bookings", headers=h)
        mine = next((b for b in r.json() if b["id"] == booking_id), None)
        check("termini shfaqet te noteri me emrin e dosjes",
              mine is not None and mine.get("attachment_name") == "kontrata-draft.pdf")
        r = await c.get(f"{BASE}/marketplace/bookings/{booking_id}/attachment", headers=h)
        check("noteri shkarkon draftin PDF",
              r.status_code == 200 and r.content[:4] == b"%PDF", f"{len(r.content)} bytes")
        r = await c.post(f"{BASE}/marketplace/bookings/{booking_id}/decide",
                         headers=h, json={"action": "confirm"})
        check("noteri konfirmon terminin", r.status_code == 200
              and r.json().get("status") == "confirmed")

        print("\n=== 6. AVA ME LIGJIN E NOTERISË ===")
        r = await c.post(f"{BASE}/assistant/ask", headers=h, json={
            "question": "Sa është tarifa noteriale për një kontratë shitblerjeje "
                        "banese me vlerë 50000 euro?",
        })
        answer = (r.json().get("message") or {}).get("content", "") if r.status_code == 200 else ""
        ok = len(answer) > 50
        check("Ava i përgjigjet pyetjes noteriale", ok,
              (answer[:100] + "…") if ok else r.text[:100])

    failed = [n for k, n in results if k == "FAIL"]
    print(f"\n{'='*60}\n{len(results)} kontrolle, {len(failed)} FAIL, "
          f"{time.time()-t0:.1f}s")
    for n in failed:
        print(f"  FAIL: {n}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    sim_guard.assert_target_allowed(BASE, script="notary_simulation.py")
    try:
        asyncio.run(main())
    finally:
        asyncio.run(cleanup())
