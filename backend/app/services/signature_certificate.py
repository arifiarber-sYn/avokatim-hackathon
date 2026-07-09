"""Signature certificate: a PDF proof sheet for a completed e-signature
(similar to DocuSign's "Certificate of Completion"). It binds the signer's
typed name, the exact document version (SHA-256), IP address and timestamp.

Legal note: this documents a *simple* electronic signature under Law
No. 08/L-022 on Electronic Identification and Trust Services in Electronic
Transactions. Qualified e-signatures (equivalent to handwritten, Art. 32)
require a licensed trust-service provider — in Kosovo: Evrotrust or rTrust
(see docs/agents/DECISIONS.md).
"""
import html
from datetime import UTC, datetime

from app.i18n import pick_locale, tr
from app.models import Contact, Document, Matter, SignatureRequest, Tenant, User

_PAGE = """<!DOCTYPE html>
<html lang="sq">
<head>
<meta charset="utf-8">
<style>
  @page {{ size: A4; margin: 2cm; }}
  body {{ font-family: "DejaVu Sans", sans-serif; color: #1a2233; font-size: 12px; line-height: 1.5; }}
  .head {{ border-bottom: 3px solid #4338ca; padding-bottom: 10px; margin-bottom: 22px; }}
  .brand {{ font-size: 22px; font-weight: bold; }}
  .brand span {{ color: #4338ca; }}
  h1 {{ font-size: 16px; margin: 0 0 4px; }}
  .muted {{ color: #667; font-size: 10px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 14px 0; }}
  th, td {{ border: 1px solid #c8ccd6; padding: 7px 10px; text-align: left; vertical-align: top; }}
  th {{ background: #eef0f6; width: 34%; font-weight: bold; }}
  .hash {{ font-family: monospace; font-size: 9.5px; word-break: break-all; }}
  .status {{ display: inline-block; padding: 2px 12px; border-radius: 10px;
            background: #dcfce7; color: #166534; font-weight: bold; }}
  .note {{ background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #4338ca;
          padding: 10px 14px; margin-top: 18px; font-size: 10.5px; color: #445; }}
  .foot {{ margin-top: 26px; border-top: 1px solid #d9dce3; padding-top: 8px; font-size: 9.5px; color: #778; }}
</style>
</head>
<body>
  <div class="head">
    <div class="brand">Bora<span>Law</span></div>
    <h1>CERTIFIKATË E NËNSHKRIMIT ELEKTRONIK</h1>
    <div class="muted">{subtitle}</div>
  </div>

  <p>Kjo certifikatë vërteton se dokumenti i identifikuar më poshtë është nënshkruar
  elektronikisht përmes platformës BoraLaw. Nënshkrimi është i lidhur në mënyrë
  kriptografike me përmbajtjen e saktë të dokumentit përmes vlerës SHA-256.</p>

  <table>
    <tr><th>Statusi</th><td><span class="status">✓ NËNSHKRUAR</span></td></tr>
    <tr><th>Dokumenti</th><td>{filename}</td></tr>
    <tr><th>Versioni i dokumentit</th><td>v{version}</td></tr>
    <tr><th>SHA-256 e dokumentit</th><td class="hash">{sha256}</td></tr>
    <tr><th>Lënda</th><td>{matter_ref} — {matter_title}</td></tr>
    <tr><th>Zyra ligjore</th><td>{firm_name}</td></tr>
    <tr><th>Kërkuar nga</th><td>{requested_by}</td></tr>
    <tr><th>Kërkuar më</th><td>{requested_at}</td></tr>
  </table>

  <table>
    <tr><th>Nënshkruesi</th><td>{contact_name}</td></tr>
    <tr><th>Emri i shtypur si nënshkrim</th><td><b>{signer_name}</b></td></tr>
    <tr><th>Nënshkruar më</th><td>{signed_at}</td></tr>
    <tr><th>Adresa IP e nënshkruesit</th><td>{signer_ip}</td></tr>
    <tr><th>ID e kërkesës së nënshkrimit</th><td class="hash">{request_id}</td></tr>
  </table>

  <div class="note">
    <b>Baza ligjore.</b> Ky dokument evidenton një nënshkrim elektronik sipas
    Ligjit Nr. 08/L-022 për Identifikimin Elektronik dhe Shërbimet e Besuara në
    Transaksionet Elektronike të Republikës së Kosovës. Sipas parimit të
    mosdiskriminimit, nënshkrimit elektronik nuk mund t'i mohohet efekti juridik
    dhe pranueshmëria si provë vetëm pse është në formë elektronike. Integriteti
    i dokumentit verifikohet duke krahasuar vlerën SHA-256 të skedarit me atë të
    regjistruar më lart. Të gjitha veprimet janë regjistruar në ditarin e
    auditimit të platformës.
  </div>

  <div class="foot">
    Gjeneruar nga BoraLaw · {generated_at} · Kjo certifikatë i referohet vetëm
    versionit të dokumentit me SHA-256 të cekur më lart.
  </div>
</body>
</html>"""


def build_certificate_pdf(
    *,
    sig: SignatureRequest,
    document: Document,
    matter: Matter,
    contact: Contact,
    tenant: Tenant | None,
    requested_by: User | None,
) -> bytes:
    from weasyprint import HTML

    def esc(value: object) -> str:
        return html.escape(str(value)) if value is not None else "—"

    def fmt(dt: datetime | None) -> str:
        return dt.astimezone(UTC).strftime("%d.%m.%Y %H:%M:%S UTC") if dt else "—"

    # Official record stays Albanian; the subtitle repeats the title in the
    # signer's language (plus English) per Law 02/L-37.
    loc = pick_locale(contact.locale, tenant.default_locale if tenant else None)
    subtitle = "Certificate of Electronic Signature Completion"
    if loc not in ("sq", "en"):
        subtitle = f"{tr(loc, 'cert_subtitle')} · {subtitle}"

    page = _PAGE.format(
        subtitle=html.escape(subtitle),
        filename=esc(document.filename),
        version=document.version,
        sha256=esc(sig.document_sha256),
        matter_ref=esc(matter.reference),
        matter_title=esc(matter.title),
        firm_name=esc(tenant.name if tenant else "—"),
        requested_by=esc(requested_by.full_name if requested_by else "—"),
        requested_at=fmt(sig.created_at),
        contact_name=esc(contact.display_name),
        signer_name=esc(sig.signer_name),
        signed_at=fmt(sig.signed_at),
        signer_ip=esc(sig.signer_ip),
        request_id=esc(sig.id),
        generated_at=fmt(datetime.now(UTC)),
    )
    return HTML(string=page).write_pdf()
