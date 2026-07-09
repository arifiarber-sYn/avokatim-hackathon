"""Demo tenant seeder: creates (or fully resets) the tenant "Zyra Demo" with
realistic Kosovo-law data so a client demo never starts from an empty screen.

Run:    .venv/bin/python scripts/seed_demo.py           (create/reset)
        .venv/bin/python scripts/seed_demo.py --delete  (remove the demo tenant)

Login (lawyer):  demo@boralaw.app        / Demo2026!bora
Login (portal):  klienti.demo@boralaw.app / Demo2026!klient
"""
import asyncio
import io
import sys
from datetime import UTC, date, datetime, timedelta

import httpx

sys.path.insert(0, ".")

BASE = "http://127.0.0.1:8000/api"
TENANT_NAME = "Zyra Demo"
LAWYER_EMAIL = "demo@boralaw.app"
LAWYER_PW = "Demo2026!bora"
CLIENT_EMAIL = "klienti.demo@boralaw.app"
CLIENT_PW = "Demo2026!klient"


def make_pdf(text: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as pdfcanvas

    buf = io.BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=A4)
    y = 800
    for line in text.splitlines():
        c.drawString(50, y, line)
        y -= 18
        if y < 60:
            c.showPage()
            y = 800
    c.save()
    return buf.getvalue()


async def delete_demo_tenant() -> None:
    from sqlalchemy import text as sqltext

    from app.database import SessionLocal

    async with SessionLocal() as db:
        await db.execute(sqltext("DELETE FROM tenants WHERE name = :n"), {"n": TENANT_NAME})
        await db.commit()
    print(f"Tenant '{TENANT_NAME}' u fshi.")


async def verify_demo_email() -> None:
    """Mark the demo user's email as verified so no banner shows in the demo."""
    from sqlalchemy import text as sqltext

    from app.database import SessionLocal

    async with SessionLocal() as db:
        await db.execute(
            sqltext("UPDATE users SET email_verified_at = now() WHERE email = :e"),
            {"e": LAWYER_EMAIL},
        )
        await db.commit()


async def seed() -> None:
    today = date.today()
    async with httpx.AsyncClient(timeout=180) as c:
        r = await c.post(f"{BASE}/auth/signup", json={
            "practice_name": TENANT_NAME, "full_name": "Av. Bora Arifi",
            "email": LAWYER_EMAIL, "password": LAWYER_PW,
        })
        r.raise_for_status()
        h = {"Authorization": f"Bearer {r.json()['access_token']}"}
        print("✓ tenant + avokatja kryesore")

        await c.patch(f"{BASE}/firm", headers=h, json={
            "fiscal_number": "811234567", "vat_number": "330123456",
            "address": "Rr. Nëna Terezë 28, 10000 Prishtinë",
            "bank_details": "NLB Banka · XK05 1701 0010 0000 0001",
            "default_vat_rate": 18,
        })
        print("✓ profili fiskal + IBAN")

        # ---------- contacts ----------
        async def contact(payload: dict) -> str:
            r = await c.post(f"{BASE}/contacts", headers=h, json=payload)
            return r.json()["id"]

        ferronikeli = await contact({
            "kind": "organization", "display_name": "NTP Ferronikeli SH.P.K.",
            "email": CLIENT_EMAIL, "phone": "+383 44 123 456",
            "address": "Zona Industriale, Drenas", "national_id": "810011223",
        })
        krasniqi = await contact({
            "display_name": "Arben Krasniqi", "email": "arben.krasniqi@shembull.com",
            "phone": "+383 44 234 567", "address": "Rr. UÇK 15, Prishtinë",
        })
        gashi = await contact({
            "display_name": "Mimoza Gashi", "phone": "+383 45 345 678",
            "address": "Rr. Ilaz Kodra, Prishtinë",
        })
        buildko = await contact({
            "kind": "organization", "display_name": "BuildKo SH.P.K.",
            "phone": "+383 38 555 100", "address": "Magjistralja Prishtinë–Ferizaj",
        })
        etc_market = await contact({
            "kind": "organization", "display_name": "ETC Market SH.A.",
        })
        berisha = await contact({"display_name": "Fatmir Berisha"})
        hoxha = await contact({"display_name": "Vlora Hoxha", "phone": "+383 49 456 789"})
        print("✓ 7 kontakte")

        # ---------- matters in different stages ----------
        async def matter(payload: dict, status: str | None = None) -> str:
            r = await c.post(f"{BASE}/matters", headers=h, json=payload)
            mid = r.json()["id"]
            if status:
                await c.patch(f"{BASE}/matters/{mid}", headers=h, json={"status": status})
            return mid

        m_borxhi = await matter({
            "title": "Përmbarimi i borxhit 48.000 € — kontrata e furnizimit",
            "practice_area": "commercial", "client_id": ferronikeli,
            "court_name": "Gjykata Themelore në Prishtinë — Dep. për Çështje Ekonomike",
            "court_case_number": "PPP.nr.412/2026",
            "opened_on": (today - timedelta(days=45)).isoformat(),
            "description": "Blerësi BuildKo SH.P.K. nuk e ka paguar faturën 2026-114 "
                           "prej 48.000 € për mallin e dorëzuar sipas kontratës së furnizimit. "
                           "Urdhërpagesa është pranuar; pritet kundërshtimi.",
        })
        m_kontesti = await matter({
            "title": "Kontest pune — kthimi në vendin e punës",
            "practice_area": "labor", "client_id": krasniqi,
            "court_name": "Gjykata Themelore në Prishtinë",
            "court_case_number": "C.nr.1889/2026",
            "opened_on": (today - timedelta(days=120)).isoformat(),
            "description": "Ndërprerja e kontratës së punës pa bazë ligjore nga ETC Market SH.A. "
                           "Kërkohet kthimi në punë dhe pagat e humbura.",
        })
        m_shkurorezimi = await matter({
            "title": "Shkurorëzim me marrëveshje + ndarja e pasurisë",
            "practice_area": "family", "client_id": gashi,
            "court_name": "Gjykata Themelore në Prishtinë",
            "opened_on": (today - timedelta(days=30)).isoformat(),
            "description": "Shkurorëzim me pëlqim të ndërsjellë; kontestuese mbetet banesa "
                           "e përbashkët në Prishtinë.",
        })
        m_prona = await matter({
            "title": "Vërtetimi i pronësisë — parcela 1024/3 Gërmi",
            "practice_area": "civil", "client_id": berisha,
            "court_name": "Gjykata Themelore në Prishtinë",
            "court_case_number": "C.nr.771/2025",
            "opened_on": (today - timedelta(days=300)).isoformat(),
            "description": "Padi për vërtetim pronësie në bazë të mbajtjes (usucapio) "
                           "për parcelën kadastrale 1024/3 në Gërmi.",
        })
        m_kontrata = await matter({
            "title": "Hartimi i kontratës së qirasë komerciale",
            "practice_area": "commercial", "client_id": ferronikeli,
            "opened_on": (today - timedelta(days=10)).isoformat(),
            "description": "Hartimi dhe negocimi i kontratës 5-vjeçare të qirasë për "
                           "hapësirën komerciale 800 m² në Fushë Kosovë.",
        })
        m_kundervajtja = await matter({
            "title": "Mbrojtja në procedurë kundërvajtëse — dogana",
            "practice_area": "administrative", "client_id": ferronikeli,
            "opened_on": (today - timedelta(days=200)).isoformat(),
            "description": "Kundërshtim i gjobës doganore 12.500 € për deklarim të gabuar tarifor.",
        }, status="on_hold")
        m_trashegimia = await matter({
            "title": "Procedura trashëgimore — familja Hoxha",
            "practice_area": "civil", "client_id": hoxha,
            "opened_on": (today - timedelta(days=400)).isoformat(),
        }, status="closed")
        m_penale = await matter({
            "title": "Mbrojtja penale — aksident trafiku",
            "practice_area": "criminal", "client_id": berisha,
            "court_name": "Gjykata Themelore në Prishtinë — Dep. Penal",
            "court_case_number": "P.nr.556/2026",
            "opened_on": (today - timedelta(days=60)).isoformat(),
            "description": "Mbrojtja e të pandehurit për veprën penale rrezikim i trafikut publik "
                           "(neni 370 KPRK).",
        })
        print("✓ 8 lëndë në faza të ndryshme")

        # opposing parties
        for mid, opp in [(m_borxhi, buildko), (m_kontesti, etc_market)]:
            await c.post(f"{BASE}/matters/{mid}/parties", headers=h,
                         json={"contact_id": opp, "role": "opposing_party"})

        # ---------- deadlines: from legal rules + hearings ----------
        r = await c.get(f"{BASE}/jurisdictions/XK/deadline-rules", headers=h)
        rules = r.json()

        def rule(needle: str) -> dict | None:
            return next(
                (x for x in rules
                 if needle in str(x.get("name", {})).lower()
                 or needle in str(x.get("legal_basis", "")).lower()),
                None,
            )

        r_kundershtimi = rule("urdhërpages") or rule("kundërshtim")
        if r_kundershtimi:
            await c.post(f"{BASE}/matters/{m_borxhi}/deadlines/from-rule", headers=h, json={
                "rule_id": r_kundershtimi["id"],
                "trigger_date": (today - timedelta(days=5)).isoformat(),
            })
        r_ankesa = rule("ankes")
        if r_ankesa:
            await c.post(f"{BASE}/matters/{m_kontesti}/deadlines/from-rule", headers=h, json={
                "rule_id": r_ankesa["id"],
                "trigger_date": (today - timedelta(days=3)).isoformat(),
            })

        async def hearing(mid: str, title: str, days_ahead: int, hour: int = 10) -> None:
            due = datetime.now(UTC).replace(hour=hour, minute=0, second=0, microsecond=0) \
                  + timedelta(days=days_ahead)
            await c.post(f"{BASE}/matters/{mid}/deadlines", headers=h, json={
                "title": title, "due_at": due.isoformat(), "kind": "hearing",
            })

        await hearing(m_kontesti, "Seanca kryesore — dëgjimi i dëshmitarëve", 7)
        await hearing(m_prona, "Seanca përgatitore", 14, hour=9)
        await hearing(m_penale, "Shqyrtimi fillestar", 3, hour=13)
        await c.post(f"{BASE}/matters/{m_shkurorezimi}/deadlines", headers=h, json={
            "title": "Dorëzimi i propozimit të përbashkët",
            "due_at": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
            "kind": "deadline", "legal_basis": "LFK neni 68",
        })
        print("✓ afate nga rregullat + 3 seanca")

        # ---------- documents ----------
        docs: dict[str, str] = {}
        for mid, fname, text in [
            (m_borxhi, "kontrata-e-furnizimit.pdf",
             "KONTRATE FURNIZIMI\n"
             "Furnizuesi: NTP Ferronikeli SH.P.K., Drenas\n"
             "Bleresi: BuildKo SH.P.K.\n"
             "Vlera: 48.000 EUR. Afati i pageses: 30 dite nga dorezimi i mallit.\n"
             "Malli u dorezua me 15.05.2026. Fatura nr. 2026-114 e papaguar.\n"
             "Kundershtimi i urdherpageses mund te paraqitet brenda 15 ditesh\n"
             "nga pranimi, sipas nenit 156 te LPK."),
            (m_borxhi, "urdherpagesa-ppp-412-2026.pdf",
             "GJYKATA THEMELORE NE PRISHTINE\n"
             "Departamenti per Ceshtje Ekonomike\n"
             "PPP.nr.412/2026 — URDHERPAGESE\n"
             "Detyrohet BuildKo SH.P.K. te paguaje 48.000 EUR me kamate ligjore.\n"
             "Keshille juridike: kundershtimi brenda 15 ditesh nga pranimi."),
            (m_kontesti, "vendimi-i-nderprerjes.pdf",
             "ETC Market SH.A. — VENDIM\n"
             "Nderpritet marredhenia e punes me Arben Krasniqi nga 01.03.2026\n"
             "per shkak te riorganizimit. Ankesa brenda 15 ditesh."),
            (m_prona, "certifikata-kadastrale-1024-3.pdf",
             "AGJENCIA KADASTRALE E KOSOVES\n"
             "Certifikate per parcelen 1024/3, ZK Germi, siperfaqja 450 m2."),
        ]:
            r = await c.post(
                f"{BASE}/matters/{mid}/documents", headers=h,
                files={"file": (fname, make_pdf(text), "application/pdf")},
            )
            docs[fname] = r.json()["id"]
        print("✓ 4 dokumente PDF me tekst")

        # share the contract with the client in the portal
        await c.post(f"{BASE}/documents/{docs['kontrata-e-furnizimit.pdf']}/visibility",
                     headers=h, json={"visible": True})

        # a generated document saved to the matter
        r = await c.get(f"{BASE}/templates?jurisdiction_code=XK", headers=h)
        templates = r.json()
        tpl = next((x for x in templates if "padi" in str(x.get("name", {})).lower()),
                   templates[0] if templates else None)
        if tpl:
            await c.post(f"{BASE}/templates/render-to-matter", headers=h, json={
                "template_id": tpl["id"], "matter_id": m_kontesti,
                "variables": {"claim_amount": "6 paga mujore (4.200 €)"},
            })
            print("✓ shkresë e gjeneruar → dokument i lëndës")

        # ---------- tasks ----------
        for payload in [
            {"matter_id": m_borxhi, "title": "Përgatit propozimin për përmbarim",
             "due_date": (today + timedelta(days=2)).isoformat(), "priority": "high"},
            {"matter_id": m_kontesti, "title": "Sigurimi i listës së dëshmitarëve",
             "due_date": (today + timedelta(days=4)).isoformat(), "priority": "normal"},
            {"matter_id": m_penale, "title": "Kërko qasje në shkresat e lëndës",
             "due_date": (today + timedelta(days=1)).isoformat(), "priority": "urgent"},
            {"title": "Rinovimi i licencës së Odës së Avokatëve",
             "due_date": (today + timedelta(days=20)).isoformat(), "priority": "low"},
        ]:
            await c.post(f"{BASE}/tasks", headers=h, json=payload)
        print("✓ 4 detyra")

        # ---------- time entries + expenses ----------
        entries = [
            (m_borxhi, "Analiza e kontratës dhe përgatitja e propozimit për urdhërpagesë", 120, 8),
            (m_borxhi, "Komunikimi me klientin dhe përmbaruesin", 45, 3),
            (m_kontesti, "Hartimi i padisë për kthim në punë", 180, 20),
            (m_kontesti, "Përgatitja për seancën kryesore", 90, 1),
            (m_shkurorezimi, "Konsultimi fillestar dhe hartimi i marrëveshjes", 60, 6),
            (m_prona, "Studimi i dokumentacionit kadastral", 75, 15),
        ]
        for mid, desc, minutes, days_ago in entries:
            await c.post(f"{BASE}/time-entries", headers=h, json={
                "matter_id": mid, "description": desc, "minutes": minutes,
                "hourly_rate": 80,
                "started_at": (datetime.now(UTC) - timedelta(days=days_ago)).isoformat(),
            })
        for mid, desc, cat, amount, days_ago in [
            (m_borxhi, "Taksa gjyqësore për propozimin përmbarimor", "court_fee", "104.00", 6),
            (m_borxhi, "Tarifa e përmbaruesit privat", "bailiff", "250.00", 2),
            (m_prona, "Eksperti i gjeodezisë — matja e parcelës", "expert", "180.00", 12),
        ]:
            await c.post(f"{BASE}/expenses", headers=h, json={
                "matter_id": mid, "description": desc, "category": cat,
                "amount": amount, "incurred_on": (today - timedelta(days=days_ago)).isoformat(),
            })
        print("✓ 6 orë pune + 3 shpenzime")

        # ---------- invoices: one paid, one draft ----------
        r = await c.post(f"{BASE}/invoices", headers=h, json={
            "matter_id": m_kontesti, "include_unbilled_time": True,
            "notes": "Faza e parë: padia dhe përgatitja e seancës.",
        })
        inv_paid = r.json()
        await c.patch(
            f"{BASE}/invoices/{inv_paid['id']}/status?new_status=sent", headers=h)
        await c.patch(
            f"{BASE}/invoices/{inv_paid['id']}/status"
            "?new_status=paid&payment_reference=NLB-TRX-2026-4471", headers=h)

        r = await c.post(f"{BASE}/invoices", headers=h, json={
            "matter_id": m_borxhi, "include_unbilled_time": True,
            "include_unbilled_expenses": True,
            "items": [{"description": "Përfaqësimi në procedurën përmbarimore (flat fee)",
                       "quantity": "1", "unit_price": "500.00"}],
        })
        inv_draft = r.json()
        print(f"✓ 2 fatura: {inv_paid.get('number')} e paguar · {inv_draft.get('number')} draft")

        # ---------- portal client ----------
        await c.post(f"{BASE}/portal/invite", headers=h, json={
            "contact_id": ferronikeli, "password": CLIENT_PW,
        })
        r = await c.post(f"{BASE}/portal/login", json={
            "email": CLIENT_EMAIL, "password": CLIENT_PW,
        })
        ph = {"Authorization": f"Bearer {r.json()['access_token']}"}
        await c.post(f"{BASE}/portal/matters/{m_borxhi}/messages", headers=ph,
                     json={"body": "Përshëndetje! A ka ndonjë zhvillim me borxhin e BuildKo?"})
        await c.post(f"{BASE}/matters/{m_borxhi}/messages", headers=h,
                     json={"body": "Po — urdhërpagesa është lëshuar. Nëse s'ka kundërshtim "
                                   "brenda 15 ditësh, kalojmë te përmbaruesi."})
        await c.post(f"{BASE}/matters/{m_borxhi}/signatures", headers=h, json={
            "document_id": docs["kontrata-e-furnizimit.pdf"], "contact_id": ferronikeli,
            "note": "Ju lutem konfirmoni autorizimin për procedurën përmbarimore.",
        })
        print("✓ portali: mesazhe dy-kahëshe + kërkesë nënshkrimi në pritje")

    await verify_demo_email()
    print(f"""
================= ZYRA DEMO GATI =================
 Avokatja:  {LAWYER_EMAIL} / {LAWYER_PW}
 Portali:   {CLIENT_EMAIL} / {CLIENT_PW}
 Rivendosja pas demos:  .venv/bin/python scripts/seed_demo.py
==================================================""")


async def main() -> None:
    if "--delete" in sys.argv:
        await delete_demo_tenant()
        return
    await delete_demo_tenant()
    await seed()


asyncio.run(main())
