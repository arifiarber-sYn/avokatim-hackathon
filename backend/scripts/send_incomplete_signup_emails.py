"""One-shot outreach: personal email from the owner to every real account
that started but never finished onboarding.

- Lawyers with unverified email        -> fresh verify link + next steps
- Lawyers verified but without OAK/profile -> what's missing to be listed
- Citizens with unverified email       -> fresh verify link + what they get

Skips simulation/test/disposable addresses. Marks the nudge timestamps so
the automated reminders don't double-send. Run with --dry-run to preview.
"""
import asyncio
import smtplib
import sys
from datetime import UTC, datetime
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import LawyerProfile, Tenant, User  # noqa: E402
from app.models.marketplace import CitizenUser  # noqa: E402
from app.security import create_purpose_token  # noqa: E402
from app.services.notifications import _is_test_recipient  # noqa: E402

DRY_RUN = "--dry-run" in sys.argv

# Obvious throwaway accounts that are not worth a personal email.
SKIP_EXACT = {"test@gmail.com", "test12345@gmail.com", "demo@avokatim.app",
              "arifi.arber@gmail.com", "marigonagashi.law@gmail.com"}
SKIP_DOMAINS = ("@yopmail.com",)

BASE = settings.public_base_url

SIGNATURE = """\

Me respekt,
Arbër Arifi
Krijuesi i AvokatIM · https://avokatiim.ai
"""

LAWYER_UNVERIFIED = """\
I/E nderuar {name},

Ju shkruaj personalisht — jam Arbër Arifi, krijuesi i AvokatIM. Faleminderit
që hapët llogari si zyrë ligjore: jeni ndër avokatët e parë në platformë.

Vura re që regjistrimi ka mbetur në gjysmë — email-i ende nuk është
verifikuar, prandaj llogaria nuk mund të aktivizohet plotësisht. Ja linku i
freskët (vlen 3 ditë):

{verify_url}

Pas verifikimit, te https://avokatiim.ai/onboarding i plotësoni për 2 minuta
profilin publik dhe numrin e licencës së OAK-së — dhe si një nga zyrat e
para të verifikuara merrni shenjën e përhershme "Themelues" në drejtori.

Tre muajt e parë gjithçka është falas, pa kartelë dhe pa detyrime. Nëse
diçka ju ka penguar gjatë regjistrimit, më përgjigjuni direkt — reagimi juaj
na ndihmon shumë në këtë fazë.
""" + SIGNATURE

LAWYER_NO_OAK = """\
I/E nderuar {name},

Ju shkruaj personalisht — jam Arbër Arifi, krijuesi i AvokatIM. Faleminderit
që u regjistruat dhe e aktivizuat profilin: jeni ndër avokatët e parë në
platformë.

Ka mbetur vetëm një hap që të shfaqeni në drejtorinë publike dhe t'ju vijnë
raste nga qytetarët: numri i licencës së Odës së Avokatëve (OAK). Në
drejtori shfaqen vetëm avokatët e verifikuar — kjo është garancia që u japim
qytetarëve.

1. Kyçuni në https://avokatiim.ai/login
2. Te Cilësimet -> Profili publik shtoni numrin e licencës OAK
3. Pas verifikimit merrni shenjën ✓ dhe, si një nga zyrat e para,
   shenjën e përhershme "Themelues".

Tre muajt e parë gjithçka është falas. Për çdo pyetje a sugjerim, më
përgjigjuni direkt në këtë email.
""" + SIGNATURE

CITIZEN_UNVERIFIED = """\
Përshëndetje {name},

Ju shkruaj personalisht — jam Arbër Arifi, krijuesi i AvokatIM. Faleminderit
që hapët llogari si qytetar.

Regjistrimi ka mbetur në gjysmë: email-i ende nuk është verifikuar, prandaj
nuk mund të postoni rast për avokatët. Ja linku i freskët (vlen 3 ditë):

{verify_url}

Çfarë keni me llogarinë e verifikuar — gjithçka falas:
- Postoni rastin tuaj dhe avokatët e verifikuar ju kontaktojnë
- Ava, asistentja juridike me ligjet e Kosovës, ju përgjigjet 24/7
- Vegla praktike: afatet ligjore, shkresa e ankesa gati për përdorim

Nëse diçka nuk ju funksionoi gjatë regjistrimit, më përgjigjuni direkt në
këtë email — e rregullojmë menjëherë.
""" + SIGNATURE


def _send(to: str, subject: str, body: str) -> None:
    if DRY_RUN:
        print(f"[dry-run] would send to {to}: {subject}")
        return
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Arbër Arifi", settings.smtp_user))
    msg["To"] = to
    msg["Reply-To"] = settings.smtp_user
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as s:
        if settings.smtp_starttls:
            s.starttls()
        s.login(settings.smtp_user, settings.smtp_password)
        s.sendmail(settings.smtp_user, [to], msg.as_string())
    print(f"sent to {to}: {subject}")


def _skip(email: str) -> bool:
    e = email.strip().lower()
    return (e in SKIP_EXACT or e.endswith(SKIP_DOMAINS) or _is_test_recipient(e))


async def main() -> None:
    now = datetime.now(UTC)
    async with SessionLocal() as db:
        # --- lawyers ---
        rows = (await db.execute(
            select(User, Tenant).join(Tenant, Tenant.id == User.tenant_id)
            .where(User.is_active.is_(True), Tenant.status == "active")
        )).all()
        for user, tenant in rows:
            if _skip(user.email) or user.is_superadmin:
                continue
            first_name = user.full_name.split()[0] if user.full_name else "koleg"
            profile = (await db.execute(
                select(LawyerProfile).where(LawyerProfile.user_id == user.id)
            )).scalar_one_or_none()
            if user.email_verified_at is None:
                token = create_purpose_token("verify_email", user.id, minutes=60 * 24 * 3)
                _send(user.email,
                      "AvokatIM — regjistrimi juaj ka mbetur në gjysmë",
                      LAWYER_UNVERIFIED.format(
                          name=first_name,
                          verify_url=f"{BASE}/verifiko-email?token={token}"))
            elif profile is None or profile.verification_status != "verified":
                _send(user.email,
                      "AvokatIM — një hap deri në drejtorinë publike",
                      LAWYER_NO_OAK.format(name=first_name))
            else:
                continue
            if not DRY_RUN:
                user.profile_nudge_sent_at = now

        # --- citizens ---
        citizens = (await db.execute(
            select(CitizenUser).where(
                CitizenUser.is_active.is_(True),
                CitizenUser.email_verified_at.is_(None),
            )
        )).scalars().all()
        for cit in citizens:
            if _skip(cit.email):
                continue
            token = create_purpose_token("citizen_verify", cit.id, minutes=60 * 24 * 3)
            _send(cit.email,
                  "AvokatIM — verifikoni email-in dhe llogaria juaj është gati",
                  CITIZEN_UNVERIFIED.format(
                      name=cit.full_name or "qytetar",
                      verify_url=f"{BASE}/rasti-im?verifiko={token}"))
            if not DRY_RUN:
                cit.verify_reminder_sent_at = now

        if not DRY_RUN:
            await db.commit()


asyncio.run(main())
