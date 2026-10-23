"""One-shot: personal welcome email from the owner to the first real lawyer
(Marigona Gashi), explaining the remaining onboarding steps.
Run once, then delete or keep for reference."""
import smtplib
import sys
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings  # noqa: E402

TO = "marigonagashi.law@gmail.com"
SUBJECT = "Mirë se erdhe në AvokatIM — edhe 2 minuta deri te shenja \u201cThemelues\u201d"

BODY = """\
E nderuar znj. Gashi,

Ju shkruaj personalisht — jam Arbër Arifi, krijuesi i AvokatIM. Faleminderit
që u regjistruat: jeni avokatja e parë e vërtetë në platformë dhe kjo për ne
ka vlerë të veçantë.

Llogaria juaj është krijuar dhe email-i është verifikuar me sukses. Ka mbetur
vetëm një hap që qytetarët t'ju gjejnë: profili juaj publik ende nuk është
aktivizuar, prandaj nuk shfaqeni në drejtori dhe nuk ju vijnë raste nga tregu.

Aktivizimi zgjat rreth 2 minuta:

1. Kyçuni në https://avokatiim.ai/login
2. Hapni https://avokatiim.ai/onboarding (ose Cilësimet -> Profili publik)
3. Aktivizoni dukshmërinë, zgjidhni fushat e praktikës dhe qytetet ku punoni,
   dhe shtoni numrin e licencës së OAK-së.

Pas verifikimit të licencës merrni shenjën e verifikimit dhe — si një nga
zyrat e para — shenjën e përhershme "Themelues" në drejtorinë publike.

Çfarë ju pret brenda: raste nga qytetarët sipas fushës suaj (me njoftim të
menjëhershëm), asistentja Ava me ligjet e Kosovës, menaxhimi i lëndëve dhe
afateve sipas LPK-së, dokumentet dhe faturimi. Tre muajt e parë gjithçka
është falas, pa kartelë dhe pa asnjë detyrim.

Nëse diçka nuk funksionon si prisni, ose keni çfarëdo sugjerimi — më
përgjigjuni direkt në këtë email. Reagimi juaj në këtë fazë e formëson
platformën.

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
