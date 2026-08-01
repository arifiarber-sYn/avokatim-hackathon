"""One-shot: nudge Betim Sijarina and Marigona Gashi to publish their
newly verified profiles so they appear in the public directory."""
import smtplib
import sys
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings  # noqa: E402

RECIPIENTS = [
    {
        "to": "betimsijarina@gmail.com",
        "name": "Betim",
    },
    {
        "to": "marigonagashi.law@gmail.com",
        "name": "Marigona",
    },
]

SUBJECT = "AvokatIM — profili juaj u verifikua, tani bëjeni publik"

BODY = """\
I/E nderuar {name},

Lajm i mirë: profili juaj në AvokatIM sapo u verifikua nga ana jonë dhe
tani keni shenjën ✓ të verifikimit.

Ka mbetur vetëm një klikim që të shfaqeni në drejtorinë publike dhe t'ju
vijnë raste nga qytetarët — profili juaj është ende i fshehur.

Ja çfarë duhet të bëni (1 minutë):

1. Kyçuni në https://avokatiim.ai/login
2. Shkoni te Cilësimet -> Profili publik
3. Aktivizoni opsionin "Shfaq profilin publikisht"

Pas këtij hapi, qytetarët mund t'ju gjejnë sipas fushës dhe qytetit tuaj
dhe t'ju dërgojnë raste të reja — gjithçka falas për vitin e parë.

Nëse keni pyetje, më përgjigjuni direkt në këtë email.

Me respekt,
Arbër Arifi
Krijuesi i AvokatIM · https://avokatiim.ai
"""


def _send(to: str, subject: str, body: str) -> None:
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
    print(f"✓ Sent to {to}")


for r in RECIPIENTS:
    _send(r["to"], SUBJECT, BODY.format(name=r["name"]))
