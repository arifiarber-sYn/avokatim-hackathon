"""One-shot: personal reminder to Fatos Dervishaj (Tosi), notary.
Profile is empty after 11 days — no bio, no cities, no ONK license.
Prompted by Halim after Cursor audit."""

import smtplib
import sys
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings  # noqa: E402

TO = "fatosdervishaj@gmail.com"
SUBJECT = "Profili juaj në AvokatIM — edhe 2 minuta deri te aktivizimi"

BODY = """\
I nderuar z. Dervishaj,

Ju shkruaj nga AvokatIM — platforma e parë ligjore për Kosovën që lidh
qytetarët me avokatë dhe noterë.

Llogaria juaj është krijuar me sukses më 14 korrik, por profili juaj
publik ende nuk është plotësuar — prandaj nuk shfaqeni në drejtorinë
tonë dhe nuk merrni kërkesa nga qytetarët.

Aktivizimi zgjat rreth 2 minuta:

1. Kyçuni në https://avokatiim.ai/login
2. Hapni https://avokatiim.ai/onboarding (ose Cilësimet > Profili publik)
3. Plotësoni fushat e praktikës, qytetin ku ushtroni dhe numrin e
   licencës ONK (për noterë)
4. Aktivizoni dukshmërinë ("i dukshëm në drejtori")

Sapo të verifikohet licenca, profili juaj bëhet publik dhe filloni të
merrni kërkesa për konsultë nga qytetarët në zonën tuaj.

Tre muajt e parë janë plotësisht falas — pa kartelë, pa detyrim.

Nëse keni pyetje ose diçka nuk është e qartë, më përgjigjeni direkt
këtij emaili. Jam këtu t'ju ndihmoj.

Me respekt,
Arbër Arifi
Krijuesi i AvokatIM · https://avokatiim.ai
"""

msg = MIMEText(BODY, "plain", "utf-8")
msg["Subject"] = SUBJECT
msg["From"] = formataddr(("Arbër Arifi", settings.smtp_user))
msg["To"] = TO
msg["Reply-To"] = settings.smtp_user

with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as s:
    if settings.smtp_starttls:
        s.starttls()
    s.login(settings.smtp_user, settings.smtp_password)
    s.sendmail(settings.smtp_user, [TO], msg.as_string())

print(f"Sent to {TO}")
