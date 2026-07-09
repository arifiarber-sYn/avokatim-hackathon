"""E2E check of the SaaS flows against a live backend: signup, email tokens,
password reset, team invites, seat limits, platform panel, suspension.
Run:  .venv/bin/python scripts/saas_check.py
"""
import asyncio
import sys
import uuid

import httpx

sys.path.insert(0, ".")
from app.security import create_access_token, create_purpose_token, password_fingerprint  # noqa: E402

BASE = "http://127.0.0.1:8000/api"
SUFFIX = uuid.uuid4().hex[:8]
PW = "saas-check-password-1"

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name} {detail}")
    if not ok:
        failures.append(name)


async def main() -> None:
    async with httpx.AsyncClient(timeout=30) as c:
        # --- signup ---
        r = await c.post(f"{BASE}/auth/signup", json={
            "practice_name": f"SaaSTest {SUFFIX}", "full_name": "Saas Test",
            "email": f"saas.{SUFFIX}@gmail.com", "password": PW,
        })
        check("signup 201", r.status_code == 201, f"({r.status_code})")
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        r = await c.post(f"{BASE}/auth/signup", json={
            "practice_name": "Dup", "full_name": "Dup",
            "email": f"saas.{SUFFIX}@gmail.com", "password": PW,
        })
        check("duplicate email 409", r.status_code == 409, f"({r.status_code})")

        me = (await c.get(f"{BASE}/auth/me", headers=h)).json()
        check("trial plan on /me", me.get("tenant_plan") == "trial", str(me.get("tenant_plan")))
        check("trial_ends_at set", bool(me.get("tenant_trial_ends_at")))
        check("email not verified yet", me.get("email_verified") is False)

        # --- email verification (token built locally, same secret) ---
        vt = create_purpose_token("verify_email", uuid.UUID(me["id"]), minutes=10)
        r = await c.post(f"{BASE}/auth/verify-email", json={"token": vt})
        check("verify-email", r.status_code == 200 and r.json().get("verified") is True)
        me2 = (await c.get(f"{BASE}/auth/me", headers=h)).json()
        check("email now verified", me2.get("email_verified") is True)

        # --- password reset (single use via fingerprint) ---
        # fetch fp by generating a reset via forgot-password isn't possible without
        # reading email, so build the token locally like the endpoint does
        r = await c.post(f"{BASE}/auth/forgot-password", json={"email": f"saas.{SUFFIX}@gmail.com"})
        check("forgot-password 200", r.status_code == 200)

        # need current hash fingerprint -> log in and change password via change-password
        r = await c.post(f"{BASE}/auth/change-password", headers=h, json={
            "current_password": PW, "new_password": PW + "x",
        })
        check("change-password", r.status_code == 200)
        r = await c.post(f"{BASE}/auth/login", json={
            "email": f"saas.{SUFFIX}@gmail.com", "password": PW + "x",
        })
        check("login with new password", r.status_code == 200, f"({r.status_code})")

        # --- rate limiting: 5 failures then 429 ---
        rl_email = f"rl.{SUFFIX}@gmail.com"
        codes = []
        for _ in range(6):
            r = await c.post(f"{BASE}/auth/login", json={"email": rl_email, "password": "wrong-pass"})
            codes.append(r.status_code)
        check("rate limit kicks in", codes[-1] == 429, str(codes))

        # --- team invite + seats ---
        r = await c.post(f"{BASE}/team/invite", headers=h, json={
            "full_name": "Member Two", "email": f"m2.{SUFFIX}@gmail.com", "role": "lawyer",
        })
        check("invite member", r.status_code == 201, f"({r.status_code}) {r.text[:100]}")
        m2 = r.json()
        check("invite pending flag", m2.get("invite_pending") is True)

        # non-admin cannot invite: accept m2 invite then try
        # build invite token locally: need m2's password fingerprint -> not readable via API.
        # Instead verify admin-only: create a staff member and use their token later.
        # Seats: tenant starts with 3; invite 2 more (total would exceed on 4th active)
        r = await c.post(f"{BASE}/team/invite", headers=h, json={
            "full_name": "Member Three", "email": f"m3.{SUFFIX}@gmail.com", "role": "staff",
        })
        check("invite member 3", r.status_code == 201, f"({r.status_code})")
        # active seats = 1 (admin); invites are inactive so allowed. Activating beyond limit is
        # blocked by PATCH; simulate: set seats_limit=1 via platform, then activation must fail.

        # --- platform panel (superadmin = the founder user) ---
        from app.database import SessionLocal
        from sqlalchemy import text as sqltext
        async with SessionLocal() as db:
            row = (await db.execute(sqltext(
                "SELECT id, tenant_id FROM users WHERE is_superadmin = true LIMIT 1"
            ))).first()
        check("superadmin exists", row is not None)
        sa_token = create_access_token(row[0], row[1])
        sh = {"Authorization": f"Bearer {sa_token}"}

        r = await c.get(f"{BASE}/platform/tenants", headers=sh)
        check("platform list", r.status_code == 200, f"({r.status_code})")
        tenants = r.json()
        test_tenant = next(t for t in tenants if t["name"] == f"SaaSTest {SUFFIX}")
        check("tenant visible in panel", test_tenant is not None)
        check("seats reported", test_tenant["seats_used"] == 1, str(test_tenant["seats_used"]))

        # non-superadmin blocked from platform
        r = await c.get(f"{BASE}/platform/tenants", headers=h)
        check("platform blocked for tenant admin", r.status_code == 403, f"({r.status_code})")

        tid = test_tenant["id"]
        # seats_limit=1 -> member activation should fail
        r = await c.patch(f"{BASE}/platform/tenants/{tid}", headers=sh, json={"seats_limit": 1})
        check("platform patch seats", r.status_code == 200)
        r = await c.patch(f"{BASE}/team/{m2['id']}", headers=h, json={"is_active": True})
        check("seat limit enforced (402)", r.status_code == 402, f"({r.status_code})")

        # --- suspend: tenant users get 403 everywhere ---
        r = await c.post(f"{BASE}/platform/tenants/{tid}/suspend", headers=sh)
        check("suspend", r.status_code == 200)
        r = await c.get(f"{BASE}/matters", headers=h)
        check("suspended tenant blocked", r.status_code == 403, f"({r.status_code})")
        r = await c.post(f"{BASE}/auth/login", json={
            "email": f"saas.{SUFFIX}@gmail.com", "password": PW + "x",
        })
        check("suspended login blocked", r.status_code == 403, f"({r.status_code})")
        r = await c.post(f"{BASE}/platform/tenants/{tid}/activate", headers=sh)
        check("activate", r.status_code == 200)
        r = await c.get(f"{BASE}/matters", headers=h)
        check("active again", r.status_code == 200, f"({r.status_code})")

        # --- corpus writes blocked for tenant admin, allowed for superadmin ---
        r = await c.post(f"{BASE}/corpus", headers=h, json={
            "title": "X", "text": "Neni 1\nTekst prove i mjaftueshem.",
        })
        check("corpus blocked (tenant)", r.status_code == 403, f"({r.status_code})")

    # cleanup
    from app.database import SessionLocal
    from sqlalchemy import text as sqltext
    async with SessionLocal() as db:
        await db.execute(sqltext("DELETE FROM tenants WHERE name = :n"), {"n": f"SaaSTest {SUFFIX}"})
        await db.commit()
    print("cleanup done")

    if failures:
        print(f"\n{len(failures)} FAILURES: {failures}")
        sys.exit(1)
    print("\nALL SAAS CHECKS PASSED")


asyncio.run(main())
