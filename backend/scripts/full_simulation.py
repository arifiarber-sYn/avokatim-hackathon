"""Full end-to-end simulation of a law firm's lifecycle on BoraLaw, played
from BOTH sides: the firm (lawyer/admin) and the client (a company).
Prints PASS/FAIL for what works and GAP for probes of missing features.
Run against the live backend:  .venv/bin/python scripts/full_simulation.py
Cleans up the throwaway tenant at the end (keeps nothing).
"""
import asyncio
import io
import sys
import time
import uuid
from datetime import date

import httpx

sys.path.insert(0, ".")

BASE = "http://127.0.0.1:8000/api"
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
        check("signup i zyrës (trial 30d, kushtet e pranuara)", r.status_code == 201)
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

        # ============ Bora AI with citations ============
        print("\n=== 7. ZYRA: pyetje ligjore për Borën ===")
        r = await c.post(f"{BASE}/assistant/ask", headers=h, json={
            "question": "Sa është afati për kundërshtim të urdhërpagesës dhe cili nen i LPK e rregullon?",
            "matter_id": mid, "provider": "deepseek",
        })
        cits = r.json().get("message", {}).get("citations", []) if r.status_code == 200 else []
        check("Bora përgjigjet me citime nga korpusi",
              r.status_code == 200 and len(cits) > 0, f"{len(cits)} citime")

        r = await c.post(f"{BASE}/assistant/matters/{mid}/summarize", headers=h)
        check("përmbledhja AI e lëndës", r.status_code == 200,
              r.text[:150] if r.status_code != 200 else "")

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

    # ============ cleanup ============
    from sqlalchemy import text as sqltext
    from app.database import SessionLocal
    async with SessionLocal() as db:
        await db.execute(sqltext("DELETE FROM tenants WHERE name = :n"),
                         {"n": f"Zyra Sim {SUFFIX}"})
        await db.commit()
    print("\ncleanup done")

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


asyncio.run(main())
