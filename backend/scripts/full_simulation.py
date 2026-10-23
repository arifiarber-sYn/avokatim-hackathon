"""Full end-to-end simulation of a law firm's lifecycle on AvokatIM, played
from BOTH sides: the firm (lawyer/admin) and the client (a company).
Prints PASS/FAIL for what works and GAP for probes of missing features.
Run against the live backend:  .venv/bin/python scripts/full_simulation.py

PRODUCTION GATE: refuses to run against the production API unless --allow-prod
is passed; point it at a test instance with AVOKATIM_SIM_BASE_URL (sim_guard.py).
Cleans up the throwaway tenant at the end (keeps nothing).
"""
import asyncio
import io
import json
import sys
import time
import uuid
from datetime import date
from pathlib import Path

import httpx

sys.path.insert(0, ".")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import sim_guard  # noqa: E402

BASE = sim_guard.resolve_base()
SUFFIX = uuid.uuid4().hex[:6]
PW_FIRM = "simulimi-zyra-pw-01"
PW_CLIENT = "simulimi-klient-pw-01"

results: list[tuple[str, str, str]] = []  # (kind, name, detail)


def rec(kind: str, name: str, detail: str = "") -> None:
    print(f"{kind:8s} {name}  {detail}")
    results.append((kind, name, detail))


def check(name: str, ok: bool, detail: str = "") -> None:
    rec("PASS" if ok else "FAIL", name, detail)


def gap(name: str, present: bool, detail: str = "") -> None:
    rec("OK" if present else "GAP", name, detail)


def make_pdf(text: str) -> bytes:
    """Tiny one-page PDF with real extractable text."""
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
    """Remove every simulation artifact. Must run even when the run crashes:
    real citizens browse the live directory, so leaked 'Zyra Sim' lawyers
    would show up as fake verified offices."""
    from sqlalchemy import text as sqltext

    from app.database import SessionLocal

    async with SessionLocal() as db:
        await db.execute(sqltext(
            "DELETE FROM citizen_users WHERE email LIKE 'qytetari.sim.%@gmail.com'"))
        await db.execute(sqltext(
            "DELETE FROM tenants WHERE name LIKE 'Zyra Sim %'"))
        await db.execute(sqltext(
            "DELETE FROM platform_feedback WHERE email LIKE 'qytetari.sim.%@gmail.com'"))
        await db.commit()
    print("\ncleanup done")


async def main() -> None:
    t0 = time.time()
    async with httpx.AsyncClient(timeout=180) as c:

        # ============ FIRM SIDE: a new office signs up ============
        print("\n=== 1. ZYRA: regjistrimi dhe onboarding ===")
        r = await c.post(f"{BASE}/auth/signup", json={
            "practice_name": f"Zyra Sim {SUFFIX}", "full_name": "Av. Driton Sim",
            "email": f"driton.sim.{SUFFIX}@gmail.com", "password": PW_FIRM,
        })
        check("signup pa pranim të kushteve REFUZOHET (Ligji 06/L-082)",
              r.status_code == 400)
        r = await c.post(f"{BASE}/auth/signup", json={
            "practice_name": f"Zyra Sim {SUFFIX}", "full_name": "Av. Driton Sim",
            "email": f"driton.sim.{SUFFIX}@gmail.com", "password": PW_FIRM,
            "accept_tos": True,
        })
        check("signup i zyrës (trial 1 vit, kushtet e pranuara)", r.status_code == 201)
        h = {"Authorization": f"Bearer {r.json()['access_token']}"}

        r = await c.patch(f"{BASE}/firm", headers=h, json={
            "fiscal_number": "811111111", "vat_number": "330111111",
            "address": "Rr. Nëna Terezë 1, Prishtinë", "default_vat_rate": 18,
            "logo": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        })
        check("profili fiskal + logo", r.status_code == 200)

        r = await c.post(f"{BASE}/team/invite", headers=h, json={
            "full_name": "Av. Blerta Sim", "email": f"blerta.sim.{SUFFIX}@gmail.com",
            "role": "lawyer",
        })
        check("ftesa e kolegut me email", r.status_code == 201)

        # ============ CLIENT SIDE: a company finds the public form ============
        print("\n=== 2. KLIENTI (kompani): formulari publik ===")
        r = await c.get(f"{BASE}/intake/public-form", headers=h)
        check("linku publik i intake", r.status_code == 200)
        intake_url = r.json()["url"]
        token = intake_url.rsplit("/", 1)[-1]

        r = await c.get(f"{BASE}/public/intake/{token}")
        check("forma publike tregon emrin+logon e zyrës",
              r.status_code == 200 and r.json().get("logo") is not None,
              str(r.json())[:80])

        r = await c.post(f"{BASE}/public/intake/{token}", json={
            "client_name": f"NTP Ferro Sim {SUFFIX} SH.P.K.",
            "client_email": f"kontakt.ferro.{SUFFIX}@gmail.com",
            "client_phone": "+383 44 111 222",
            "summary": "Blerësi nuk e ka paguar faturën prej 48.000 EUR për mallin e "
                       "dorëzuar më 15.03.2026 sipas kontratës së furnizimit. Duam të "
                       "iniciojmë procedurë përmbarimore ose padi për borxhin.",
            "accept_privacy": True,
        })
        check("kompania dërgon kërkesën online (privatësia e pranuar)", r.status_code == 201)

        # ============ FIRM: intake -> conflict -> matter ============
        print("\n=== 3. ZYRA: intake, konflikti, hapja e lëndës ===")
        r = await c.get(f"{BASE}/intake", headers=h)
        intakes = r.json()
        check("intake shfaqet me burim web",
              len(intakes) == 1 and intakes[0]["source"] == "web")
        iid = intakes[0]["id"]
        has_conflict_check = intakes[0].get("conflict_result") is not None
        check("kontrolli i konfliktit u ekzekutua", has_conflict_check)

        r = await c.post(f"{BASE}/intake/{iid}/accept", headers=h)
        check("intake → lëndë me një klik", r.status_code == 200)

        r = await c.get(f"{BASE}/matters", headers=h)
        matter = r.json()[0]
        mid = matter["id"]
        check("lënda u krijua me referencë", bool(matter["reference"]), matter["reference"])
        client_id = matter["client"]["id"]

        # opposing party
        r = await c.post(f"{BASE}/contacts", headers=h, json={
            "display_name": f"Debitor Sim {SUFFIX} SH.P.K.", "kind": "company",
        })
        opp_id = r.json()["id"]
        r = await c.post(f"{BASE}/matters/{mid}/parties", headers=h, json={
            "contact_id": opp_id, "role": "opposing_party",
        })
        check("pala kundërshtare u shtua", r.status_code == 201)

        # ============ deadlines from the legal engine ============
        print("\n=== 4. ZYRA: afatet nga motori ligjor ===")
        r = await c.get(f"{BASE}/jurisdictions/XK/deadline-rules", headers=h)
        rules = r.json()
        check("rregullat XK të ngarkuara", len(rules) >= 5, f"{len(rules)} rregulla")
        rule = next((x for x in rules if "urdhërpages" in str(x.get("name", {})).lower()
                     or "kundërshtim" in str(x.get("name", {})).lower()), rules[0])
        r = await c.post(f"{BASE}/matters/{mid}/deadlines/from-rule", headers=h, json={
            "rule_id": rule["id"], "trigger_date": date.today().isoformat(),
        })
        check("afati llogaritet nga rregulli", r.status_code == 201,
              f"{rule.get('legal_basis')} → {r.json().get('due_at', '')[:10]}")
        r = await c.post(f"{BASE}/matters/{mid}/deadlines", headers=h, json={
            "title": "Seanca përgatitore", "due_at": "2026-09-10T10:00:00Z",
            "kind": "hearing",
        })
        check("seanca u shtua manualisht", r.status_code == 201)

        # ============ documents: upload, text, AI extraction ============
        print("\n=== 5. ZYRA: dokumentet + AI ===")
        pdf = make_pdf(
            "KONTRATE FURNIZIMI\n"
            f"Furnizuesi: NTP Ferro Sim {SUFFIX} SH.P.K.\n"
            f"Bleresi: Debitor Sim {SUFFIX} SH.P.K.\n"
            "Vlera: 48.000 EUR. Afati i pageses: 30 dite nga dorezimi.\n"
            "Malli u dorezua me 15.03.2026. Fatura nr. 2026-114 e papaguar.\n"
            "Pala e demtuar mund te paraqese kundershtim brenda 15 ditesh\n"
            "nga pranimi i urdherpageses, sipas nenit 156 te LPK."
        )
        r = await c.post(
            f"{BASE}/matters/{mid}/documents", headers=h,
            files={"file": ("kontrata-furnizimit.pdf", pdf, "application/pdf")},
        )
        check("ngarkimi i PDF", r.status_code == 201)
        doc_id = r.json()["id"]

        text_ok = False
        for _ in range(15):
            r = await c.get(f"{BASE}/documents/{doc_id}/text", headers=h)
            if r.status_code == 200 and len(r.json().get("text") or "") > 100:
                text_ok = True
                break
            await asyncio.sleep(2)
        check("teksti u nxor nga PDF", text_ok)

        r = await c.post(
            f"{BASE}/matters/{mid}/documents/{doc_id}/extract-deadlines", headers=h,
        )
        ai_deadlines = r.json() if r.status_code == 200 else []
        check("AI nxjerr afate nga dokumenti", r.status_code == 200 and len(ai_deadlines) > 0,
              f"{len(ai_deadlines)} propozime" if r.status_code == 200 else r.text[:120])

        # review workflow
        r = await c.get(f"{BASE}/team", headers=h)
        team = r.json()
        r = await c.post(f"{BASE}/documents/{doc_id}/request-review", headers=h,
                         json={"reviewer_id": team[0]["id"]})
        check("dokumenti dërgohet për rishikim", r.status_code == 200)
        r = await c.post(f"{BASE}/documents/{doc_id}/review", headers=h,
                         json={"decision": "approve", "note": "Në rregull"})
        check("rishikimi miratohet", r.status_code == 200)

        # ============ templates ============
        print("\n=== 6. ZYRA: shabllonet ===")
        r = await c.get(f"{BASE}/templates?jurisdiction_code=XK", headers=h)
        templates = r.json()
        check("shabllonet XK", len(templates) >= 10, f"{len(templates)} shabllone")
        tpl = next((x for x in templates if "padi" in str(x.get("name", {})).lower()), templates[0])
        r = await c.post(f"{BASE}/templates/render", headers=h, json={
            "template_id": tpl["id"], "matter_id": mid,
        })
        check("shablloni mbushet me të dhënat e lëndës (pa 400 për variabla që mungojnë)",
              r.status_code == 200 and len(r.json().get("content", "")) > 200,
              r.text[:150] if r.status_code != 200 else "")
        check("variablat që mungojnë dalin si vend bosh ______",
              r.status_code == 200 and "__________" in r.json().get("content", ""))

        r = await c.post(f"{BASE}/templates/render-to-matter", headers=h, json={
            "template_id": tpl["id"], "matter_id": mid,
            "variables": {"claim_amount": "48.000 EUR"},
        })
        check("shkresa ruhet si dokument PDF i lëndës", r.status_code == 201,
              r.text[:150] if r.status_code != 201 else r.json().get("filename", ""))

        # ============ Ava AI with citations ============
        print("\n=== 7. ZYRA: pyetje ligjore për Avën ===")
        r = await c.post(f"{BASE}/assistant/ask", headers=h, json={
            "question": "Sa është afati për kundërshtim të urdhërpagesës dhe cili nen i LPK e rregullon?",
            "matter_id": mid, "provider": "deepseek",
        })
        cits = r.json().get("message", {}).get("citations", []) if r.status_code == 200 else []
        check("Ava përgjigjet me citime nga korpusi",
              r.status_code == 200 and len(cits) > 0, f"{len(cits)} citime")

        r = await c.post(f"{BASE}/assistant/matters/{mid}/summarize", headers=h)
        check("përmbledhja AI e lëndës", r.status_code == 200,
              r.text[:150] if r.status_code != 200 else "")

        # Deep research (SSE): sub-questions → search steps → cited synthesis
        step_kinds: set[str] = set()
        dr_done = False
        dr_citations = 0
        async with c.stream(
            "POST", f"{BASE}/assistant/deep-research", headers=h,
            json={"question": "Cilat janë afatet dhe procedura e ankesës "
                              "kundër aktgjykimit të shkallës së parë?",
                  "provider": "deepseek"},
            timeout=300,
        ) as resp:
            dr_status = resp.status_code
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                ev = json.loads(line[6:])
                if ev.get("type") == "step":
                    step_kinds.add(ev.get("step"))
                elif ev.get("type") == "done":
                    dr_done = True
                    dr_citations = len(ev.get("message", {}).get("citations", []))
        check("deep research: hapat raportohen (nën-pyetje + kërkim + sintezë)",
              dr_status == 200 and {"subquestions", "search", "synthesis"} <= step_kinds,
              f"hapa: {sorted(step_kinds)}")
        check("deep research: përgjigje me citime të bashkuara",
              dr_done and dr_citations > 0, f"{dr_citations} citime")

        # AI clause assist on a draft
        r = await c.post(f"{BASE}/templates/ai-assist", headers=h, json={
            "draft": "MARRËVESHJE SHËRBIMI\nPorositësi paguan 1.000 EUR pas "
                     "përfundimit të punës. Punët kryhen sa më shpejt që të "
                     "jetë e mundur. Kontesti zgjidhet me mirëkuptim.",
            "instruction": "Forco klauzolën e afatit të pagesës dhe shto afat konkret dorëzimi.",
        })
        ai_assist = r.json() if r.status_code == 200 else {}
        check("ai-assist: teksti përmirësohet sipas udhëzimit",
              r.status_code == 200 and len(ai_assist.get("improved_text", "")) > 50,
              r.text[:150] if r.status_code != 200 else
              f"{len(ai_assist.get('changes', []))} ndryshime, "
              f"{len(ai_assist.get('risk_flags', []))} flamuj")

        # Document AI summary (cached in ai_summary)
        r = await c.post(f"{BASE}/documents/{doc_id}/summarize", headers=h)
        doc_sum = r.json() if r.status_code == 200 else {}
        check("përmbledhja AI e dokumentit (summary + pika kyçe)",
              r.status_code == 200 and len(doc_sum.get("summary", "")) > 30,
              f"{len(doc_sum.get('key_points', []))} pika, "
              f"{len(doc_sum.get('deadlines', []))} afate" if r.status_code == 200
              else r.text[:150])
        r = await c.post(f"{BASE}/documents/{doc_id}/summarize", headers=h)
        check("përmbledhja e dokumentit kthehet nga cache pa LLM",
              r.status_code == 200 and r.json().get("summary") == doc_sum.get("summary"))

        # ============ billing ============
        print("\n=== 8. ZYRA: orët, fatura me TVSH, pagesa ===")
        from datetime import UTC, datetime
        for desc, mins in [("Analiza e kontratës dhe dokumenteve", 90),
                           ("Përgatitja e propozimit për përmbarim", 120)]:
            r = await c.post(f"{BASE}/time-entries", headers=h, json={
                "matter_id": mid, "description": desc, "minutes": mins,
                "hourly_rate": 80, "started_at": datetime.now(UTC).isoformat(),
            })
        check("orët e punës u regjistruan", r.status_code == 201,
              r.text[:120] if r.status_code != 201 else "")

        r = await c.post(f"{BASE}/invoices", headers=h, json={
            "matter_id": mid, "include_unbilled_time": True,
        })
        inv = r.json()
        check("fatura nga orët e pafaturuara", r.status_code == 201,
              f"nr {inv.get('number')}")
        check("TVSH 18% e llogaritur",
              inv.get("vat_rate") == 18 and float(inv.get("total_with_vat", 0)) > float(inv.get("total", 0)),
              f"total {inv.get('total')} + TVSH = {inv.get('total_with_vat')}")

        r = await c.patch(
            f"{BASE}/invoices/{inv['id']}/status"
            "?new_status=paid&payment_reference=TRX-2026-0709",
            headers=h,
        )
        check("pagesa u shënua me referencë", r.status_code == 200,
              r.text[:100] if r.status_code != 200 else "")

        # ============ portal: the client company logs in ============
        print("\n=== 9. KLIENTI: portali ===")
        r = await c.post(f"{BASE}/portal/invite", headers=h, json={
            "contact_id": client_id, "password": PW_CLIENT,
        })
        check("portali u aktivizua për klientin", r.status_code == 200)

        r = await c.post(f"{BASE}/portal/login", json={
            "email": f"kontakt.ferro.{SUFFIX}@gmail.com", "password": PW_CLIENT,
        })
        pd = r.json()
        check("klienti kyçet dhe sheh brendin e zyrës",
              r.status_code == 200 and pd.get("firm_name", "").startswith("Zyra Sim"))
        ph = {"Authorization": f"Bearer {pd['access_token']}"}

        r = await c.get(f"{BASE}/portal/my-matters", headers=ph)
        pmatters = r.json()
        check("klienti sheh lëndën + seancat",
              len(pmatters) == 1 and len(pmatters[0].get("upcoming_hearings", [])) >= 1)

        r = await c.post(f"{BASE}/portal/matters/{mid}/messages", headers=ph,
                         json={"body": "A ka ndonjë zhvillim me borxhin?"})
        check("klienti dërgon mesazh", r.status_code == 201)
        r = await c.post(f"{BASE}/matters/{mid}/messages", headers=h,
                         json={"body": "Po, nesër dorëzojmë propozimin për përmbarim."})
        check("avokati përgjigjet", r.status_code == 201)
        r = await c.get(f"{BASE}/portal/matters/{mid}/messages", headers=ph)
        check("biseda dy-kahëshe në portal", len(r.json()) == 2)

        # ============ e-signature + certificate ============
        print("\n=== 10. NËNSHKRIMI elektronik ===")
        r = await c.post(f"{BASE}/matters/{mid}/signatures", headers=h, json={
            "document_id": doc_id, "contact_id": client_id,
            "note": "Ju lutem nënshkruajeni autorizimin.",
        })
        check("kërkesa për nënshkrim", r.status_code == 201)
        sig_id = r.json()["id"]

        r = await c.get(f"{BASE}/portal/signatures", headers=ph)
        check("klienti e sheh në portal", len(r.json()) == 1)
        r = await c.post(f"{BASE}/portal/signatures/{sig_id}/sign", headers=ph,
                         json={"signer_name": f"NTP Ferro Sim {SUFFIX} SH.P.K."})
        check("klienti nënshkruan", r.status_code == 200,
              r.text[:120] if r.status_code != 200 else "")

        r = await c.get(f"{BASE}/matters/{mid}/signatures/{sig_id}/certificate", headers=h)
        check("certifikata PDF gjenerohet",
              r.status_code == 200 and r.content[:4] == b"%PDF", f"{len(r.content)} bytes")

        # ============ reports + calendar ============
        print("\n=== 11. ZYRA: raportet, kalendari ===")
        r = await c.get(f"{BASE}/reports/dashboard", headers=h)
        d = r.json()
        check("dashboardi me KPI", r.status_code == 200 and d.get("matters_by_status"))
        r = await c.get(f"{BASE}/reports/analytics", headers=h)
        check("analitika financiare", r.status_code == 200)

        r = await c.get(f"{BASE}/calendar/feed-url", headers=h)
        ics_url = r.json()["url"].replace("https://www.avokatiim.ai", "http://127.0.0.1:8000") \
                                 .replace("https://avokatiim.ai", "http://127.0.0.1:8000") \
                                 .replace("http://127.0.0.1:3000", "http://127.0.0.1:8000")
        r = await c.get(ics_url)
        check("ICS feed me afatet", r.status_code == 200 and b"VEVENT" in r.content)

        # ============ the 2026-standard features ============
        print("\n=== 12. FATURA PDF, SHPENZIMET, FLAT-FEE ===")
        r = await c.get(f"{BASE}/invoices/{inv['id']}/pdf", headers=h)
        check("fatura shkarkohet si PDF fiskal",
              r.status_code == 200 and r.content[:4] == b"%PDF", f"{len(r.content)} bytes")

        r = await c.post(f"{BASE}/expenses", headers=h, json={
            "matter_id": mid, "description": "Taksa gjyqësore për propozimin",
            "category": "court_fee", "amount": "104.00",
            "incurred_on": date.today().isoformat(),
        })
        check("shpenzimi i lëndës regjistrohet", r.status_code == 201,
              r.text[:120] if r.status_code != 201 else "")

        r = await c.post(f"{BASE}/invoices", headers=h, json={
            "matter_id": mid, "include_unbilled_expenses": True,
            "items": [{"description": "Përfaqësimi në procedurë (flat fee)",
                       "quantity": "1", "unit_price": "500.00"}],
        })
        inv2 = r.json()
        check("fatura me shpenzime + artikull flat-fee",
              r.status_code == 201 and float(inv2.get("total", 0)) == 604.0,
              f"total {inv2.get('total')}")

        print("\n=== 13. DETYRAT, KËRKIMI, PARAPAMJA ===")
        r = await c.post(f"{BASE}/tasks", headers=h, json={
            "matter_id": mid, "title": "Përgatit propozimin për përmbarim",
            "due_date": date.today().isoformat(), "priority": "high",
        })
        check("detyra krijohet me përgjegjës dhe afat", r.status_code == 201,
              r.text[:120] if r.status_code != 201 else "")
        task_id = r.json().get("id")
        r = await c.patch(f"{BASE}/tasks/{task_id}", headers=h, json={"status": "done"})
        check("detyra shënohet e kryer", r.status_code == 200
              and r.json().get("completed_at") is not None)
        r = await c.get(f"{BASE}/tasks?mine=true&open_only=true", headers=h)
        check("'Detyrat e mia' filtrohen", r.status_code == 200)

        r = await c.get(f"{BASE}/search?q=Ferro", headers=h)
        sr = r.json() if r.status_code == 200 else {}
        check("kërkimi global gjen lëndën, kontaktin, dokumentin",
              r.status_code == 200 and len(sr.get("matters", [])) >= 1
              and len(sr.get("contacts", [])) >= 1,
              f"lëndë:{len(sr.get('matters', []))} kontakte:{len(sr.get('contacts', []))} "
              f"dok:{len(sr.get('documents', []))}")

        r = await c.get(f"{BASE}/documents/{doc_id}/preview", headers=h)
        check("parapamja inline e dokumentit",
              r.status_code == 200 and "inline" in r.headers.get("content-disposition", ""))

        print("\n=== 14. DOKUMENTET NË PORTAL ===")
        r = await c.get(f"{BASE}/portal/matters/{mid}/documents", headers=ph)
        check("para ndarjes klienti s'sheh asgjë", r.status_code == 200 and len(r.json()) == 0)
        r = await c.post(f"{BASE}/documents/{doc_id}/visibility", headers=h,
                         json={"visible": True})
        check("avokati e ndan dokumentin me klientin", r.status_code == 200)
        r = await c.get(f"{BASE}/portal/matters/{mid}/documents", headers=ph)
        check("klienti e sheh dokumentin në portal",
              r.status_code == 200 and len(r.json()) == 1)
        r = await c.get(f"{BASE}/portal/documents/{doc_id}/download", headers=ph)
        check("klienti e shkarkon dokumentin",
              r.status_code == 200 and r.content[:4] == b"%PDF")

        print("\n=== 15. AUDIT LOG + EKSPORTI ===")
        r = await c.get(f"{BASE}/audit-log", headers=h)
        check("audit log i lexueshëm nga admini",
              r.status_code == 200 and len(r.json()) > 10, f"{len(r.json())} veprime")
        r = await c.get(f"{BASE}/export/tenant", headers=h)
        check("eksporti ZIP i të gjitha të dhënave",
              r.status_code == 200 and r.content[:2] == b"PK", f"{len(r.content)} bytes")

        print("\n=== 16. MJETET E KLIENTIT (trust accounting) ===")
        r = await c.post(f"{BASE}/trust/transactions", headers=h, json={
            "matter_id": mid, "kind": "deposit", "occurred_on": date.today().isoformat(),
            "amount": "1000.00", "description": "Avans nga klienti", "reference": "TR-001",
        })
        check("depozita e klientit regjistrohet", r.status_code == 201,
              r.text[:120] if r.status_code != 201 else "")
        r = await c.post(f"{BASE}/trust/transactions", headers=h, json={
            "matter_id": mid, "kind": "withdrawal", "occurred_on": date.today().isoformat(),
            "amount": "300.00", "description": "Pagesë e taksës gjyqësore",
        })
        check("tërheqja për shpenzim regjistrohet", r.status_code == 201)
        r = await c.post(f"{BASE}/trust/transactions", headers=h, json={
            "matter_id": mid, "kind": "withdrawal", "occurred_on": date.today().isoformat(),
            "amount": "5000.00", "description": "Tërheqje mbi bilancin",
        })
        check("tërheqja mbi bilancin REFUZOHET (mbrojtja e mjeteve)", r.status_code == 400)
        r = await c.get(f"{BASE}/trust/balances", headers=h)
        balances = r.json() if r.status_code == 200 else []
        check("bilanci i mjeteve llogaritet saktë (700.00)",
              r.status_code == 200 and any(float(b["balance"]) == 700.0 for b in balances),
              str([b.get("balance") for b in balances]))

        print("\n=== 17. TARIFA E OAK ===")
        r = await c.get(f"{BASE}/fee-tariff?jurisdiction_code=XK", headers=h)
        tariff = r.json() if r.status_code == 200 else []
        check("tarifa e OAK e lexueshme si të dhëna",
              r.status_code == 200 and len(tariff) >= 15, f"{len(tariff)} zëra")
        civil_hearing = next((x for x in tariff if x["code"] == "civil.hearing.upto_10k"), None)
        check("zëri 'seancë civile deri 10.000 €' = 80.00 €",
              civil_hearing is not None and float(civil_hearing["amount"]) == 80.0)

        print("\n=== 18. SHABLLONI SI .DOCX ===")
        r = await c.get(f"{BASE}/templates?jurisdiction_code=XK", headers=h)
        tpl_id = r.json()[0]["id"]
        r = await c.post(f"{BASE}/templates/render-docx", headers=h, json={
            "template_id": tpl_id, "matter_id": mid, "variables": {},
        })
        check("shablloni shkarkohet si .docx i stiluar",
              r.status_code == 200 and r.content[:2] == b"PK"
              and "wordprocessingml" in r.headers.get("content-type", ""),
              f"{len(r.content)} bytes")

        print("\n=== 19. KANALET OPSIONALE (email-in, SMS, kartela) ===")
        # These degrade gracefully when not configured in .env
        r = await c.get(f"{BASE}/matters/{mid}/email-address", headers=h)
        check("email-i i lëndës: aktiv ose i çaktivizuar pastër",
              r.status_code in (200, 404),
              r.json().get("address", "") if r.status_code == 200 else "(IMAP i pakonfiguruar)")
        r = await c.post(f"{BASE}/invoices/{inv2['id']}/payment-link", headers=h)
        check("link pagese me kartelë: aktiv ose i çaktivizuar pastër",
              r.status_code in (200, 400),
              "(Stripe i pakonfiguruar)" if r.status_code == 400 else "OK")
        from app.services.sms import sms_enabled
        check("kanali SMS i implementuar (aktivizohet me .env)", True,
              "aktiv" if sms_enabled() else "(Twilio i pakonfiguruar)")

        # ============ Kosovo compliance: languages, privacy, AML ============
        print("\n=== 20. GJUHËT ZYRTARE (Ligji 02/L-37) ===")
        r = await c.put(f"{BASE}/contacts/{client_id}", headers=h, json={
            "kind": "company", "display_name": f"NTP Ferro Sim {SUFFIX} SH.P.K.",
            "email": f"kontakt.ferro.{SUFFIX}@gmail.com", "phone": "+383 44 111 222",
            "locale": "sr",
        })
        check("gjuha e komunikimit të klientit ruhet (sr)",
              r.status_code == 200 and r.json().get("locale") == "sr")
        r = await c.post(f"{BASE}/portal/login", json={
            "email": f"kontakt.ferro.{SUFFIX}@gmail.com", "password": PW_CLIENT,
        })
        check("portali kthen gjuhën e klientit + statusin e kushteve",
              r.status_code == 200 and r.json().get("locale") == "sr"
              and r.json().get("terms_accepted") is False)
        r = await c.get(f"{BASE}/invoices/{inv['id']}/pdf", headers=h)
        check("fatura PDF gjenerohet dygjuhësh (sq + sr)",
              r.status_code == 200 and r.content[:4] == b"%PDF", f"{len(r.content)} bytes")

        print("\n=== 21. PËLQIMET DHE PRIVATËSIA (Ligji 06/L-082) ===")
        r = await c.post(f"{BASE}/portal/accept-terms", headers=ph)
        check("klienti pranon kushtet në portal", r.status_code == 200)
        r = await c.get(f"{BASE}/contacts/{client_id}/consents", headers=h)
        kinds = [x["kind"] for x in r.json()] if r.status_code == 200 else []
        check("pëlqimi portal_tos u regjistrua me datë/IP",
              r.status_code == 200 and "portal_tos" in kinds)
        r = await c.post(f"{BASE}/contacts/{client_id}/consents", headers=h,
                         json={"kind": "sms", "granted": True})
        check("avokati regjistron pëlqimin SMS", r.status_code == 200)
        r = await c.post(f"{BASE}/contacts/{client_id}/consents", headers=h,
                         json={"kind": "sms", "granted": False})
        check("pëlqimi SMS revokohet", r.status_code == 200
              and not any(x["kind"] == "sms" and x["revoked_at"] is None
                          for x in r.json()))
        r = await c.get(f"{BASE}/contacts/{client_id}/export", headers=h)
        check("eksporti ZIP për subjektin e të dhënave",
              r.status_code == 200 and r.content[:2] == b"PK", f"{len(r.content)} bytes")
        r = await c.get(f"{BASE}/privacy/retention-review", headers=h)
        check("lista e retention-it për shqyrtim", r.status_code == 200,
              f"{len(r.json().get('matters', []))} lëndë të skaduara")
        # erasure on a scrap contact (the client has open matters — must refuse)
        r = await c.post(f"{BASE}/contacts/{client_id}/erasure", headers=h)
        check("fshirja REFUZOHET sa ka lëndë të hapura", r.status_code == 400)
        r = await c.post(f"{BASE}/contacts", headers=h,
                         json={"display_name": f"Person Skrap {SUFFIX}", "kind": "person",
                               "email": f"skrap.{SUFFIX}@gmail.com"})
        scrap_id = r.json()["id"]
        r = await c.post(f"{BASE}/contacts/{scrap_id}/erasure", headers=h)
        anon = (await c.get(f"{BASE}/contacts/{scrap_id}", headers=h)).json()
        check("kontakti anonimizohet (e drejta e fshirjes)",
              r.status_code == 200 and anon.get("anonymized_at") is not None
              and anon.get("email") is None)

        print("\n=== 22. AI E JASHTME (transferimet ndërkombëtare) ===")
        r = await c.patch(f"{BASE}/firm", headers=h, json={"allow_external_ai": False})
        check("AI e jashtme çaktivizohet nga zyra", r.status_code == 200)
        r = await c.get(f"{BASE}/assistant/providers", headers=h)
        check("asistentja raporton se AI e jashtme është e ndaluar",
              r.status_code == 200 and r.json().get("external_ai_allowed") is False)
        r = await c.patch(f"{BASE}/firm", headers=h, json={"allow_external_ai": True})
        check("AI e jashtme riaktivizohet", r.status_code == 200)

        print("\n=== 23. AML/KYC (Ligji 05/L-096) ===")
        r = await c.put(f"{BASE}/contacts/{client_id}", headers=h, json={
            "kind": "company", "display_name": f"NTP Ferro Sim {SUFFIX} SH.P.K.",
            "email": f"kontakt.ferro.{SUFFIX}@gmail.com", "locale": "sr",
            "id_doc_type": "id_card", "id_doc_number": "1234567890",
            "id_verified_on": date.today().isoformat(),
            "risk_level": "standard", "is_pep": False,
            "beneficial_owner": "Fadil Ferro (100%)",
        })
        check("KYC te kontakti (dokumenti, rreziku, pronari përfitues)",
              r.status_code == 200 and r.json().get("id_doc_type") == "id_card")
        r = await c.post(f"{BASE}/trust/transactions", headers=h, json={
            "matter_id": mid, "kind": "deposit", "occurred_on": date.today().isoformat(),
            "amount": "12000.00", "description": "Depozitë e madhe për blerje prone",
            "source_of_funds": "Shitja e banesës — kontrata nr. 456/2026",
        })
        check("depozita ≥10k me burim fondesh regjistrohet e shënjuar",
              r.status_code == 201)
        r = await c.get(f"{BASE}/aml/indicators", headers=h)
        inds = r.json().get("indicators", []) if r.status_code == 200 else []
        check("indikatorët e NjIF-K si të dhëna (6 gjuhë)",
              len(inds) >= 8 and all("sr" in i["text"] for i in inds), f"{len(inds)} indikatorë")
        r = await c.get(f"{BASE}/aml/matters/{mid}/checklist", headers=h)
        check("checklist AML sugjeron fushëveprimin (ka trust ledger)",
              r.status_code == 200 and r.json().get("suggested_in_scope") is True)
        r = await c.put(f"{BASE}/aml/matters/{mid}/checklist", headers=h, json={
            "in_scope": True, "checked": {"aml.cash_large": True},
            "notes": "Depozita 12.000 € — burimi i dokumentuar.",
        })
        check("checklist AML ruhet te lënda", r.status_code == 200)
        r = await c.post(f"{BASE}/aml/reports", headers=h, json={
            "matter_id": mid, "contact_id": client_id,
            "indicators": ["aml.cash_large"],
            "description": "Depozitë e pazakontë 12.000 € cash; burimi kërkon verifikim shtesë.",
        })
        check("raporti i brendshëm i dyshimit krijohet", r.status_code == 201)
        rep_id = r.json()["id"]
        r = await c.get(f"{BASE}/aml/reports/{rep_id}/pdf", headers=h)
        check("raporti i dyshimit eksportohet PDF për NjIF-K",
              r.status_code == 200 and r.content[:4] == b"%PDF", f"{len(r.content)} bytes")
        r = await c.post(f"{BASE}/aml/reports/{rep_id}/submit", headers=h)
        check("raporti shënohet i dërguar", r.status_code == 200
              and r.json().get("status") == "submitted")

        print("\n=== 24. TREGU PUBLIK (qytetarë ↔ avokatë) ===")
        # Repeated simulation runs share this machine's IP — clear the
        # signup rate-limit counters so the run stays deterministic.
        import redis.asyncio as aioredis
        from app.config import settings as app_settings
        rr = aioredis.from_url(app_settings.redis_url)
        for pattern in ("avokatim:rl:citizen_signup:*", "avokatim:rl:citizen_login:*",
                        "avokatim:rl:citizen_pw_forgot:*", "avokatim:rl:citizen_pw_change:*",
                        "avokatim:rl:ava_structure:*"):
            async for rkey in rr.scan_iter(pattern):
                await rr.delete(rkey)
        await rr.aclose()

        r = await c.put(f"{BASE}/marketplace/profile", headers=h, json={
            "is_visible": True, "bio": "Avokat me përvojë në të drejtën civile.",
            "practice_areas": ["civil", "commercial"], "cities": ["Prishtinë"],
            "languages": ["sq", "en"], "oak_license_no": f"SIM-{SUFFIX}",
            "consult_fee_eur": 30,
        })
        check("avokati aktivizon profilin publik (licenca OAK → në pritje)",
              r.status_code == 200 and r.json().get("is_visible") is True
              and r.json().get("verification_status") == "pending")
        r = await c.get(f"{BASE}/public/lawyers")
        directory = r.json() if r.status_code == 200 else []
        check("PA verifikim OAK avokati NUK del në drejtori",
              not any(x["firm_name"] == f"Zyra Sim {SUFFIX}" for x in directory))

        # The platform operator checks the public OAK registry and approves
        # (same effect as the /platform panel decide endpoint)
        from sqlalchemy import text as _vsql

        from app.database import SessionLocal as _VSession
        async with _VSession() as _vdb:
            await _vdb.execute(_vsql(
                "UPDATE lawyer_profiles SET verification_status='verified', "
                "verified_at=now() WHERE oak_license_no = :lic"),
                {"lic": f"SIM-{SUFFIX}"})
            await _vdb.commit()
        r = await c.get(f"{BASE}/public/lawyers")
        directory = r.json() if r.status_code == 200 else []
        sim_entry = next(
            (x for x in directory if x["firm_name"] == f"Zyra Sim {SUFFIX}"), None)
        check("pas verifikimit OAK del në drejtori me badge + çmim transparent",
              sim_entry is not None and sim_entry.get("verified") is True
              and sim_entry.get("consult_fee_eur") == 30,
              f"{len(directory)} profile")

        cit_email = f"qytetari.sim.{SUFFIX}@gmail.com"
        r = await c.post(f"{BASE}/public/citizen/signup", json={
            "full_name": "Qytetar Simulues", "email": cit_email,
            "password": "qytetari-pw-123",
        })
        check("regjistrimi i qytetarit pa pëlqim privatësie REFUZOHET",
              r.status_code == 400)
        r = await c.post(f"{BASE}/public/citizen/signup", json={
            "full_name": "Qytetar Simulues", "email": cit_email,
            "phone": "+383 44 555 666", "password": "qytetari-pw-123",
            "locale": "sq", "accept_privacy": True,
        })
        check("regjistrimi i qytetarit (llogari platformë-nivel)", r.status_code == 201)
        cit_id = r.json()["citizen"]["id"]
        ch = {"Authorization": f"Bearer {r.json()['access_token']}"}

        case_body = {
            "category": "civil",
            "description": "Qiradhënësi nuk ma kthen depozitën prej 500 EUR edhe pse "
                           "banesën e dorëzova pa dëmtime para dy muajsh.",
            "city": "Prishtinë", "urgency": "normal",
        }
        r = await c.post(f"{BASE}/public/citizen/cases", headers=ch, json=case_body)
        check("postimi i rastit pa email të verifikuar REFUZOHET", r.status_code == 403)

        from app.security import create_purpose_token
        vtoken = create_purpose_token("citizen_verify", uuid.UUID(cit_id), minutes=60)
        r = await c.post(f"{BASE}/public/citizen/verify-email", json={"token": vtoken})
        check("verifikimi i email-it të qytetarit", r.status_code == 200)

        r = await c.post(f"{BASE}/public/citizen/cases", headers=ch, json=case_body)
        check("qytetari poston rastin", r.status_code == 201)
        case_id = r.json()["id"]

        # Quality gate: junk/repetitive posts never reach the lawyers
        r = await c.post(f"{BASE}/public/citizen/cases", headers=ch, json={
            "category": "civil",
            "description": "mkan rre,mkan rre,mkan rre,mkan rre,mkan rre,mkan rre,mkan rre",
            "urgency": "normal",
        })
        check("rasti spam (përsëritje) REFUZOHET nga filtri i cilësisë",
              r.status_code == 400, f"status={r.status_code}")

        # --- citizen account: profile update, change + reset password ---
        r = await c.patch(f"{BASE}/public/citizen/me", headers=ch, json={
            "full_name": "Qytetar I Përditësuar", "phone": "+383 45 111 222",
            "locale": "en",
        })
        check("qytetari përditëson profilin (emri, telefoni, gjuha)",
              r.status_code == 200 and r.json().get("full_name") == "Qytetar I Përditësuar"
              and r.json().get("locale") == "en")
        r = await c.patch(f"{BASE}/public/citizen/me", headers=ch, json={
            "full_name": "Qytetar Simulues", "locale": "sq",
        })
        check("profili kthehet për vazhdimin e simulimit", r.status_code == 200)

        r = await c.post(f"{BASE}/public/citizen/change-password", headers=ch, json={
            "current_password": "gabim-fare", "new_password": "qytetari-pw-456",
        })
        check("ndryshimi i fjalëkalimit me fjalëkalim të gabuar REFUZOHET",
              r.status_code == 400)
        r = await c.post(f"{BASE}/public/citizen/change-password", headers=ch, json={
            "current_password": "qytetari-pw-123", "new_password": "qytetari-pw-456",
        })
        check("qytetari ndryshon fjalëkalimin", r.status_code == 200)
        r = await c.post(f"{BASE}/public/citizen/login", json={
            "email": cit_email, "password": "qytetari-pw-456",
        })
        check("kyçja me fjalëkalimin e ri funksionon", r.status_code == 200)

        r = await c.post(f"{BASE}/public/citizen/forgot-password", json={
            "email": f"nuk.ekziston.{SUFFIX}@example.com",
        })
        check("forgot-password s'zbulon nëse email-i ekziston",
              r.status_code == 200 and r.json().get("sent") is True)
        rtoken = create_purpose_token("citizen_reset", uuid.UUID(cit_id), minutes=60)
        r = await c.post(f"{BASE}/public/citizen/reset-password", json={
            "token": rtoken, "new_password": "qytetari-pw-123",
        })
        check("rivendosja e fjalëkalimit me token nga email-i", r.status_code == 200)
        r = await c.post(f"{BASE}/public/citizen/reset-password", json={
            "token": "token-i-pavlefshem", "new_password": "qytetari-pw-999",
        })
        check("token i pavlefshëm rivendosjeje REFUZOHET", r.status_code == 400)
        r = await c.post(f"{BASE}/public/citizen/login", json={
            "email": cit_email, "password": "qytetari-pw-123",
        })
        check("kyçja pas rivendosjes funksionon", r.status_code == 200)
        ch = {"Authorization": f"Bearer {r.json()['access_token']}"}

        r = await c.get(f"{BASE}/marketplace/cases", headers=h)
        browse = r.json() if r.status_code == 200 else []
        mine_in_browse = [x for x in browse if x["id"] == case_id]
        check("avokati sheh rastin me emër të maskuar",
              len(mine_in_browse) == 1
              and mine_in_browse[0]["citizen_name"] == "Qytetar S.")

        r = await c.post(f"{BASE}/marketplace/cases/{case_id}/claim", headers=h)
        check("claim: conflict check + IntakeRequest source=marketplace",
              r.status_code == 200 and r.json().get("claimed") is True)
        mk_intake_id = r.json()["intake_request_id"]
        r = await c.get(f"{BASE}/intake", headers=h)
        mk_intake = next((x for x in r.json() if x["id"] == mk_intake_id), None)
        check("intake nga tregu shfaqet me burim marketplace",
              mk_intake is not None and mk_intake["source"] == "marketplace")

        r = await c.post(f"{BASE}/public/citizen/cases/{case_id}/messages",
                         headers=ch, json={"body": "A keni nevojë për kontratën e qirasë?"})
        check("qytetari i shkruan avokatit", r.status_code == 201)
        r = await c.post(f"{BASE}/marketplace/cases/{case_id}/messages",
                         headers=h, json={"body": "Po, ma dërgoni kontratën ju lutem."})
        check("avokati i përgjigjet qytetarit", r.status_code == 201)
        r = await c.get(f"{BASE}/public/citizen/cases/{case_id}/messages", headers=ch)
        check("biseda shihet nga qytetari (2 mesazhe)",
              r.status_code == 200 and len(r.json()) == 2)

        r = await c.post(f"{BASE}/intake/{mk_intake_id}/accept", headers=h)
        check("pranimi i intake konverton rastin", r.status_code == 200)
        r = await c.get(f"{BASE}/public/citizen/cases", headers=ch)
        conv = next((x for x in r.json() if x["id"] == case_id), None)
        check("statusi i rastit bëhet converted",
              conv is not None and conv["status"] == "converted")
        r = await c.post(f"{BASE}/portal/login", json={
            "email": cit_email, "password": "qytetari-pw-123",
        })
        check("qytetari kyçet në portal me TË NJËJTIN fjalëkalim",
              r.status_code == 200 and r.json().get("access_token"))

        # Reviews: the citizen rates the service after the engagement
        check("rasti i konvertuar lejohet për vlerësim",
              conv is not None and conv.get("can_review") is True)
        r = await c.post(f"{BASE}/public/citizen/cases/{case_id}/review",
                         headers=ch, json={
                             "rating_communication": 5, "rating_speed": 4,
                             "rating_clarity": 5,
                             "comment": "Përgjigje e shpejtë dhe shpjegim i qartë.",
                         })
        check("qytetari vlerëson shërbimin (komunikim/shpejtësi/qartësi)",
              r.status_code == 201)
        r = await c.post(f"{BASE}/public/citizen/cases/{case_id}/review",
                         headers=ch, json={
                             "rating_communication": 1, "rating_speed": 1,
                             "rating_clarity": 1,
                         })
        check("vlerësimi i dytë për të njëjtin rast refuzohet (409)",
              r.status_code == 409)
        r = await c.get(f"{BASE}/public/lawyers")
        sim_entry = next(
            (x for x in r.json() if x["firm_name"] == f"Zyra Sim {SUFFIX}"), None)
        check("mesatarja e vlerësimeve del në drejtori",
              sim_entry is not None and sim_entry.get("rating") == 4.7
              and sim_entry.get("review_count") == 1,
              f"rating={sim_entry.get('rating') if sim_entry else None}")

        r = await c.get(f"{BASE}/public/stats")
        stats = r.json() if r.status_code == 200 else {}
        check("statistikat publike (qasje në drejtësi)",
              r.status_code == 200 and stats.get("lawyers_in_directory", 0) >= 1
              and stats.get("laws_in_corpus", 0) >= 9,
              f"avokatë={stats.get('lawyers_in_directory')}, ligje={stats.get('laws_in_corpus')}")

        print("\n=== 25. AVA PUBLIKE FALAS (Faza 2) ===")
        r = await c.get(f"{BASE}/public/ava/quota?session_id=sim{SUFFIX}")
        check("kuota anonime (5 pyetje/ditë)",
              r.status_code == 200 and r.json().get("limit") == 5
              and r.json().get("is_citizen") is False)
        r = await c.get(f"{BASE}/public/ava/quota?session_id=sim{SUFFIX}", headers=ch)
        check("kuota e qytetarit (20 pyetje/ditë)",
              r.status_code == 200 and r.json().get("limit") == 20
              and r.json().get("is_citizen") is True)
        r = await c.post(f"{BASE}/public/ava/ask", json={
            "question": "Sa është afati i ankesës kundër aktgjykimit në "
                        "procedurën kontestimore në Kosovë?",
            "session_id": f"sim{SUFFIX}",
        })
        ava = r.json() if r.status_code == 200 else {}
        check("Ava publike përgjigjet me citime nga korpusi",
              r.status_code == 200 and len(ava.get("answer", "")) > 50
              and len(ava.get("citations", [])) > 0,
              f"{len(ava.get('citations', []))} citime, mbeten {ava.get('remaining')}")
        r = await c.get(f"{BASE}/public/ava/quota?session_id=sim{SUFFIX}")
        check("kuota zbritet pas pyetjes",
              r.status_code == 200 and r.json().get("remaining") == 4,
              f"remaining={r.json().get('remaining')}")

        # Ava-intake: the conversation becomes a structured case draft
        r = await c.post(f"{BASE}/public/ava/structure-case", json={
            "history": [
                {"role": "user", "content": "Punëdhënësi nuk m'i ka paguar tri "
                 "pagat e fundit dhe tash më ka larguar nga puna pa paralajmërim. "
                 "Punoj në Prizren."},
                {"role": "assistant", "content": "Sipas Ligjit të Punës keni të "
                 "drejtë në pagat e papaguara dhe në afat paralajmërimi..."},
            ],
        })
        sc = r.json() if r.status_code == 200 else {}
        check("Ava strukturon rastin nga biseda (kategori + përshkrim)",
              r.status_code == 200 and sc.get("category") == "labor"
              and len(sc.get("description", "")) >= 20,
              f"category={sc.get('category')}, city={sc.get('city')}")

        # abuse protection: the LLM quality gate may already reject obvious ad
        # spam; if it slips through (fail-open), the lawyer reports it instead.
        r = await c.post(f"{BASE}/public/citizen/cases", headers=ch, json={
            "category": "other",
            "description": "Blej ilaçe të lira online pa recetë — oferta më e mirë në treg!!!",
        })
        if r.status_code == 400:
            check("reklama refuzohet nga filtri i cilësisë (LLM)", True)
            r = await c.post(f"{BASE}/public/citizen/cases", headers=ch, json={
                "category": "other",
                "description": "Kam nevojë për këshillë rreth një kontrate qiraje "
                               "që përmban kushte të cilat më duken të padrejta.",
            })
        check("rasti për testin e raportimit u krijua", r.status_code == 201,
              f"status={r.status_code}")
        spam_id = r.json()["id"]
        r = await c.post(f"{BASE}/marketplace/cases/{spam_id}/report", headers=h)
        check("avokati raporton rast abuziv (mbyllet + audit)",
              r.status_code == 200 and r.json().get("reported") is True)

        print("\n=== 26. SOS + KUFIJTË E LEAD-EVE (Faza 3/4) ===")
        rr = aioredis.from_url(app_settings.redis_url)
        for pattern in ("avokatim:rl:citizen_sos:*", "avokatim:rl:citizen_case:*"):
            async for rkey in rr.scan_iter(pattern):
                await rr.delete(rkey)
        await rr.aclose()

        r = await c.put(f"{BASE}/marketplace/profile", headers=h, json={
            "is_visible": True, "sos_on_duty": True,
            "bio": "Avokat me përvojë në të drejtën civile.",
            "practice_areas": ["civil", "commercial"], "cities": ["Prishtinë"],
            "languages": ["sq", "en"], "oak_license_no": f"SIM-{SUFFIX}",
            "consult_fee_eur": 30,
        })
        check("avokati bëhet kujdestar SOS", r.status_code == 200
              and r.json().get("sos_on_duty") is True)

        r = await c.get(f"{BASE}/marketplace/lead-quota", headers=h)
        quota_before = r.json() if r.status_code == 200 else {}
        check("kuota e lead-eve për planin trial (5/muaj)",
              r.status_code == 200 and quota_before.get("limit") == 5
              and quota_before.get("used") == 1,
              f"used={quota_before.get('used')}, mbeten={quota_before.get('remaining')}")

        r = await c.post(f"{BASE}/public/citizen/sos", headers=ch, json={
            "description": "Më ndaloi policia dhe po ma kontrollojnë veturën pa "
                           "arsyetim — kam nevojë për avokat TANI.",
            "city": "Prishtinë",
        })
        check("qytetari dërgon SOS (pa pritur verifikim emaili)",
              r.status_code == 201 and r.json().get("urgency") == "sos")
        sos_id = r.json()["id"]

        r = await c.get(f"{BASE}/marketplace/cases", headers=h)
        browse = r.json() if r.status_code == 200 else []
        check("rasti SOS del i pari në Tregun e avokatëve",
              len(browse) > 0 and browse[0]["id"] == sos_id
              and browse[0]["urgency"] == "sos")

        r = await c.post(f"{BASE}/marketplace/cases/{sos_id}/claim", headers=h)
        check("kujdestari e merr rastin SOS", r.status_code == 200
              and r.json().get("claimed") is True)
        r = await c.get(f"{BASE}/marketplace/lead-quota", headers=h)
        check("kuota zbritet pas marrjes së lead-it",
              r.status_code == 200 and r.json().get("used") == 2
              and r.json().get("remaining") == 3)

        r = await c.post(f"{BASE}/public/citizen/sos", headers=ch, json={
            "description": "Situatë e dytë urgjente për të njëjtin qytetar sot."
        })
        sos2_ok = r.status_code == 201
        r = await c.post(f"{BASE}/public/citizen/sos", headers=ch, json={
            "description": "E treta brenda ditës — duhet të bllokohet nga limiti."
        })
        check("SOS i tretë brenda 24h bllokohet (mbrojtje abuzimi)",
              sos2_ok and r.status_code == 429)

        print("\n=== 27. DHOMA VIDEO/AUDIO SOS (LiveKit) ===")
        r = await c.post(f"{BASE}/marketplace/cases/{sos_id}/call-token", headers=h)
        lk = r.json() if r.status_code == 200 else {}
        check("avokati merr token për dhomën e thirrjes",
              r.status_code == 200 and lk.get("room") == f"sos-{sos_id}",
              f"enabled={lk.get('enabled')}")
        r = await c.post(f"{BASE}/public/citizen/cases/{sos_id}/call-token", headers=ch)
        lk_cit = r.json() if r.status_code == 200 else {}
        check("qytetari merr token për TË NJËJTËN dhomë",
              r.status_code == 200 and lk_cit.get("room") == lk.get("room"))
        if lk.get("enabled") and lk.get("token"):
            rv = await c.get("http://127.0.0.1:7880/rtc/validate",
                             params={"access_token": lk["token"]})
            check("serveri LiveKit e pranon tokenin e avokatit", rv.status_code == 200)
            rv = await c.get("http://127.0.0.1:7880/rtc/validate",
                             params={"access_token": lk_cit["token"]})
            check("serveri LiveKit e pranon tokenin e qytetarit", rv.status_code == 200)
        else:
            check("LiveKit i konfiguruar (çelësat në backend/.env)", False,
                  "video e çaktivizuar — kontrollo LIVEKIT_API_KEY/SECRET")
        # the reported spam case was never claimed by the tenant → 404;
        # a claimed-then-closed case would give 400 — both deny the call
        r = await c.post(f"{BASE}/marketplace/cases/{spam_id}/call-token", headers=h)
        check("s'ka thirrje për raste jo-aktive (të mbyllura)",
              r.status_code in (400, 404), f"status={r.status_code}")

        print("\n=== 28. ABONIMI I PLATFORMËS (të hyrat pas vitit të parë falas) ===")
        from sqlalchemy import text as _sqltext

        from app.database import SessionLocal as _Session

        r = await c.get(f"{BASE}/billing/subscription", headers=h)
        sub = r.json() if r.status_code == 200 else {}
        check("gjendja e abonimit: trial, 24 €/përdorues/muaj, pa fatura",
              r.status_code == 200 and sub.get("plan") == "trial"
              and sub.get("price_eur") == 24.0 and sub.get("invoices") == [],
              f"ulëse={sub.get('seats')}")

        r = await c.post(f"{BASE}/billing/subscription/upgrade", headers=h)
        up = r.json() if r.status_code == 200 else {}
        inv = up.get("invoice") or {}
        check("upgrade vetë-shërbyes trial → plan me pagesë + fatura e parë",
              r.status_code == 200 and up.get("plan") in ("solo", "firm")
              and inv.get("status") == "open",
              f"plan={up.get('plan')}, fatura={inv.get('number')}")
        check("shuma e faturës = ulëse × çmimi",
              inv and abs(inv["amount_eur"] - inv["seats"] * inv["unit_price_eur"]) < 0.01,
              f"{inv.get('seats')} × {inv.get('unit_price_eur')} = {inv.get('amount_eur')} €")
        r = await c.post(f"{BASE}/billing/subscription/upgrade", headers=h)
        check("upgrade i dytë refuzohet (tashmë me pagesë)", r.status_code == 400)

        r = await c.get(f"{BASE}/marketplace/lead-quota", headers=h)
        check("pas upgrade: lead-e PA KUFI nga Tregu",
              r.status_code == 200 and r.json().get("limit") is None)

        # Dunning: overdue past grace pauses new claims (data stays accessible)
        async with _Session() as db:
            await db.execute(
                _sqltext("UPDATE platform_invoices SET due_on = CURRENT_DATE - 20 "
                         "WHERE id = :i"), {"i": inv["id"]})
            await db.commit()
        r = await c.get(f"{BASE}/marketplace/lead-quota", headers=h)
        check("fatura 20 ditë vonesë (> grace 14) → past_due",
              r.status_code == 200 and r.json().get("past_due") is True)

        r = await c.post(f"{BASE}/public/citizen/cases", headers=ch, json={
            "category": "commercial",
            "description": "Kontratë biznesi e pashlyer — furnitori nuk po i "
                           "përmbahet afatit të dorëzimit të mallit.",
            "city": "Prishtinë",
        })
        case2_id = r.json()["id"]
        r = await c.get(f"{BASE}/marketplace/cases", headers=h)
        row2 = next((x for x in r.json() if x["id"] == case2_id), None)
        check("rasti i ri shënohet 'përputhet me profilin' (kategori+qytet)",
              row2 is not None and row2.get("matches_profile") is True)
        r = await c.post(f"{BASE}/marketplace/cases/{case2_id}/claim", headers=h)
        check("claim bllokohet me 402 derisa fatura të paguhet",
              r.status_code == 402)

        # Operator records the bank transfer -> claiming resumes
        async with _Session() as db:
            await db.execute(
                _sqltext("UPDATE platform_invoices SET status='paid', "
                         "paid_on=CURRENT_DATE, payment_reference='transfer sim' "
                         "WHERE id = :i"), {"i": inv["id"]})
            await db.commit()
        r = await c.post(f"{BASE}/marketplace/cases/{case2_id}/claim", headers=h)
        check("pas pagesës claim funksionon prapë", r.status_code == 200
              and r.json().get("claimed") is True)

        r = await c.get(f"{BASE}/billing/subscription", headers=h)
        sub = r.json() if r.status_code == 200 else {}
        check("fatura shfaqet e paguar me referencë",
              r.status_code == 200 and sub.get("invoices")
              and sub["invoices"][0]["status"] == "paid"
              and sub["invoices"][0]["payment_reference"] == "transfer sim")

        print("\n=== 29. KASAFORTA E DËSHMIVE (SOS, hash-chain) ===")
        r = await c.post(f"{BASE}/public/citizen/evidence/start", headers=ch, json={
            "kind": "sos_audio", "mime": "audio/webm", "consent": True,
            "case_request_id": sos_id,
        })
        ev = r.json() if r.status_code == 201 else {}
        check("sesioni i dëshmisë hapet me pëlqim", r.status_code == 201, ev.get("id", ""))
        ev_id = ev.get("id")
        chunk1, chunk2 = b"SIM-AUDIO-CHUNK-1" * 40, b"SIM-AUDIO-CHUNK-2" * 40
        r = await c.post(f"{BASE}/public/citizen/evidence/{ev_id}/chunks", headers=ch,
                         data={"seq": "0"}, files={"chunk": ("c0.webm", chunk1, "audio/webm")})
        ok1 = r.status_code == 201
        r = await c.post(f"{BASE}/public/citizen/evidence/{ev_id}/chunks", headers=ch,
                         data={"seq": "1"}, files={"chunk": ("c1.webm", chunk2, "audio/webm")})
        check("copëzat ngarkohen të renditura (hash chain)", ok1 and r.status_code == 201,
              f"chain={r.json().get('chain_hash', '')[:16]}…" if r.status_code == 201 else "")
        r = await c.post(f"{BASE}/public/citizen/evidence/{ev_id}/chunks", headers=ch,
                         data={"seq": "5"}, files={"chunk": ("c5.webm", chunk1, "audio/webm")})
        check("copëza jashtë radhe REFUZOHET (integriteti)", r.status_code == 409)
        r = await c.post(f"{BASE}/public/citizen/evidence/{ev_id}/finish", headers=ch, json={})
        fin = r.json() if r.status_code == 200 else {}
        check("sesioni mbyllet me zinxhir të verifikuar",
              r.status_code == 200 and fin.get("chunk_count") == 2,
              f"status={fin.get('status')}")
        r = await c.get(f"{BASE}/public/citizen/evidence/{ev_id}/audio", headers=ch)
        check("qytetari e shkarkon audion e plotë (e dekriptuar)",
              r.status_code == 200 and r.content == chunk1 + chunk2)
        r = await c.get(f"{BASE}/public/citizen/evidence/{ev_id}/package", headers=ch)
        check("pako dëshmie PDF me regjistrin e hash-eve",
              r.status_code == 200 and r.content[:5] == b"%PDF-")
        r = await c.get(f"{BASE}/marketplace/cases/{sos_id}/evidence", headers=h)
        rows = r.json() if r.status_code == 200 else []
        check("avokati i rastit SOS e sheh dëshm",
              r.status_code == 200 and any(x["id"] == ev_id for x in rows))
        r = await c.get(f"{BASE}/marketplace/cases/{sos_id}/evidence/{ev_id}/audio", headers=h)
        check("avokati e shkarkon audion e dëshmisë", r.status_code == 200
              and r.content == chunk1 + chunk2)

        print("\n=== 30. ZËRI (STT/TTS lokal) ===")
        r = await c.get(f"{BASE}/public/voice/status")
        vs = r.json() if r.status_code == 200 else {}
        check("statusi i shërbimit të zërit", r.status_code == 200,
              f"stt={vs.get('stt')} tts={vs.get('tts')}")
        if vs.get("tts"):
            r = await c.post(f"{BASE}/public/voice/tts",
                             json={"text": "Mirëdita, unë jam Ava."})
            check("TTS shqip kthen audio WAV", r.status_code == 200
                  and r.content[:4] == b"RIFF", f"{len(r.content)} bytes")
        else:
            gap("TTS shqip (Piper sq_AL)", False, "modeli i zërit s'është aktiv")

        print("\n=== 31. VEGLAT PUBLIKE (pa llogari) ===")
        r = await c.get(f"{BASE}/public/tools/deadline-rules")
        pub_rules = r.json() if r.status_code == 200 else []
        check("rregullat e afateve publike (XK)", len(pub_rules) >= 5,
              f"{len(pub_rules)} rregulla")
        appeal = next((x for x in pub_rules if x["code"] == "civil.appeal_judgment"), None)
        r = await c.post(f"{BASE}/public/tools/deadline-calc", json={
            "rule_id": appeal["id"], "trigger_date": "2026-07-01",
        })
        calc = r.json() if r.status_code == 200 else {}
        check("kalkulatori publik llogarit afatin e ankesës",
              r.status_code == 200 and calc.get("due_date") == "2026-07-16",
              f"due={calc.get('due_date')} ({calc.get('legal_basis')})")
        r = await c.get(f"{BASE}/public/tools/documents")
        docs = r.json() if r.status_code == 200 else []
        check("shabllonet e shkresave e ankesave (7)", len(docs) >= 7,
              ", ".join(x["code"] for x in docs))
        check("çdo shabllon ka kategori",
              all(x.get("category") in
                  {"institucionet", "puna", "konsumatori", "te_pergjithshme", "noteria"}
                  for x in docs))
        r = await c.post(f"{BASE}/public/tools/documents/kerkese", json={"values": {
            "sender_name": "Qytetari Sim", "sender_address": "Rr. Sim 1, Prishtinë",
            "sender_phone": "044 000 000", "institution": "Komuna e Prishtinës",
            "subject": "Qasje në dokumente publike",
            "body": "Kërkoj kopjen e lejes së ndërtimit për parcelën 111-11.",
            "city": "Prishtinë",
        }})
        check("letra e kërkesës gjenerohet si PDF",
              r.status_code == 200 and r.content[:5] == b"%PDF-",
              f"{len(r.content)} bytes")
        r = await c.post(f"{BASE}/public/tools/documents/kerkese", json={"values": {}})
        check("gjenerimi pa fusha REFUZOHET", r.status_code == 400)
        r = await c.post(f"{BASE}/public/tools/documents/ankese_konsumatori", json={"values": {
            "sender_name": "Qytetari Sim", "sender_address": "Rr. Sim 1, Prishtinë",
            "sender_phone": "044 000 000", "business": "Elektro Sim SH.P.K., Prishtinë",
            "purchase": "Frigorifer, 15.06.2026",
            "complaint": "Frigoriferi ndaloi së punuari pas dy javësh.",
            "demand": "Kërkoj ndërrimin e produktit ose kthimin e parave.",
            "city": "Prishtinë",
        }})
        check("ankesa e konsumatorit gjenerohet si PDF",
              r.status_code == 200 and r.content[:5] == b"%PDF-",
              f"{len(r.content)} bytes")

        print("\n=== 31b. FEEDBACK DREJT PLATFORMËS ===")
        r = await c.post(f"{BASE}/public/feedback", json={
            "kind": "sugjerim", "name": "Qytetari Sim",
            "email": f"qytetari.sim.{SUFFIX}@gmail.com",
            "message": "Sugjerim simulimi: shtoni edhe shabllon për kërkesë pensioni.",
        })
        check("qytetari dërgon sugjerim te platforma", r.status_code == 201)
        r = await c.post(f"{BASE}/public/feedback", json={
            "kind": "spam", "message": "mesazh me lloj të pavlefshëm .........",
        })
        check("lloj i pavlefshëm feedback-u REFUZOHET", r.status_code == 422)
        r = await c.post(f"{BASE}/public/feedback", json={
            "kind": "problem", "message": "shkurt",
        })
        check("mesazh shumë i shkurtër REFUZOHET", r.status_code == 422)
        r = await c.get(f"{BASE}/platform/feedback", headers=h)
        check("avokati i thjeshtë S'KA qasje te feedback-u i platformës",
              r.status_code == 403)

        print("\n=== 32. REZERVIMI I KONSULTAVE ===")
        all_days = [{"day": d, "start": "00:00", "end": "23:30"} for d in range(7)]
        r = await c.put(f"{BASE}/marketplace/booking-settings", headers=h,
                        json={"enabled": True, "slots": all_days})
        check("avokati cakton disponueshmërinë javore", r.status_code == 200)
        r = await c.put(f"{BASE}/marketplace/booking-settings", headers=h,
                        json={"enabled": True,
                              "slots": [{"day": 9, "start": "25:00", "end": "09:00"}]})
        ok_invalid = r.status_code == 400
        await c.put(f"{BASE}/marketplace/booking-settings", headers=h,
                    json={"enabled": True, "slots": all_days})
        check("dritare e pavlefshme REFUZOHET", ok_invalid)
        r = await c.get(f"{BASE}/public/lawyers")
        prof = next((x for x in r.json() if x["firm_name"] == f"Zyra Sim {SUFFIX}"), None)
        check("drejtoria e shënon avokatin me rezervim aktiv",
              prof is not None and prof.get("booking") is True)
        r = await c.get(f"{BASE}/public/lawyers/{prof['id']}/slots")
        slots = r.json().get("slots", []) if r.status_code == 200 else []
        check("terminet e lira kthehen (14 ditë)", len(slots) > 100, f"{len(slots)} termine")
        r = await c.post(f"{BASE}/public/citizen/bookings", headers=ch, json={
            "profile_id": prof["id"], "starts_at": slots[0],
            "note": "Konsultë simulimi për kontratë pune.",
        })
        bk = r.json() if r.status_code == 201 else {}
        check("qytetari rezervon terminin e parë", r.status_code == 201,
              f"{bk.get('starts_at')} ({bk.get('status')})")
        # Without Stripe keys the paid-consult flow must not activate:
        # booking goes straight to 'pending' and no checkout URL is returned.
        check("pa Stripe: rezervimi mbetet 'pending' pa checkout_url",
              bk.get("status") == "pending" and not bk.get("checkout_url"))
        r = await c.post(f"{BASE}/public/citizen/bookings", headers=ch, json={
            "profile_id": prof["id"], "starts_at": slots[0],
        })
        check("termini i zënë REFUZOHET (409)", r.status_code == 409)
        r = await c.get(f"{BASE}/marketplace/bookings", headers=h)
        mine = r.json() if r.status_code == 200 else []
        check("avokati e sheh rezervimin në pritje",
              any(x["id"] == bk.get("id") and x["status"] == "pending" for x in mine))
        r = await c.post(f"{BASE}/marketplace/bookings/{bk['id']}/decide", headers=h,
                         json={"action": "confirm"})
        check("avokati e konfirmon konsultën", r.status_code == 200
              and r.json().get("status") == "confirmed")
        r = await c.get(f"{BASE}/public/citizen/bookings", headers=ch)
        check("qytetari e sheh konsultën të konfirmuar",
              any(x["id"] == bk["id"] and x["status"] == "confirmed" for x in r.json()))
        r = await c.post(f"{BASE}/public/citizen/bookings/{bk['id']}/cancel", headers=ch)
        check("qytetari mund ta anulojë", r.status_code == 200
              and r.json().get("status") == "cancelled")

    fails = [x for x in results if x[0] == "FAIL"]
    gaps = [x for x in results if x[0] == "GAP"]
    passes = [x for x in results if x[0] == "PASS"]
    oks = [x for x in results if x[0] == "OK"]
    print(f"\n===== PËRMBLEDHJA ({time.time()-t0:.0f}s) =====")
    print(f"PASS: {len(passes)}  FAIL: {len(fails)}  GAP: {len(gaps)}  OK(gap-probe): {len(oks)}")
    for k, n, d in fails:
        print(f"  FAIL: {n} {d}")
    for k, n, d in gaps:
        print(f"  GAP:  {n} {d}")


async def run() -> None:
    sim_guard.assert_target_allowed(BASE, script="full_simulation.py")
    try:
        await main()
    finally:
        await cleanup()


asyncio.run(run())
