"""Invoice PDF: a professional fiscal invoice for Kosovo practice —
firm identity (NUI/VAT), client, line items, VAT and bank details.

Labels are bilingual (Albanian / client language) when the client's
communication language differs — Law 02/L-37 on the Use of Languages."""
import html
from datetime import date

from app.i18n import bilabel, pick_locale, tr
from app.models import Contact, Invoice, Matter, Tenant

_PAGE = """<!DOCTYPE html>
<html lang="sq">
<head>
<meta charset="utf-8">
<style>
  @page {{ size: A4; margin: 1.8cm; }}
  body {{ font-family: "DejaVu Sans", sans-serif; color: #1a2233; font-size: 11px; line-height: 1.5; }}
  .top {{ display: flex; justify-content: space-between; align-items: flex-start;
         border-bottom: 3px solid #4338ca; padding-bottom: 14px; margin-bottom: 20px; }}
  .firm-name {{ font-size: 18px; font-weight: bold; }}
  .firm-meta {{ color: #556; font-size: 10px; margin-top: 4px; white-space: pre-line; }}
  .logo {{ max-height: 52px; max-width: 180px; }}
  h1 {{ font-size: 20px; margin: 0; text-align: right; }}
  .inv-no {{ font-size: 12px; color: #4338ca; font-weight: bold; text-align: right; }}
  .status {{ display: inline-block; padding: 2px 12px; border-radius: 10px; font-weight: bold;
            font-size: 10px; margin-top: 6px; }}
  .paid {{ background: #dcfce7; color: #166534; }}
  .unpaid {{ background: #fef3c7; color: #92400e; }}
  .cols {{ display: flex; justify-content: space-between; margin: 16px 0; gap: 24px; }}
  .box {{ flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 14px; }}
  .box h3 {{ margin: 0 0 6px; font-size: 10px; text-transform: uppercase; color: #667; letter-spacing: 0.5px; }}
  table.items {{ border-collapse: collapse; width: 100%; margin: 14px 0; }}
  .items th, .items td {{ border: 1px solid #c8ccd6; padding: 7px 10px; text-align: left; }}
  .items th {{ background: #eef0f6; font-size: 10px; text-transform: uppercase; letter-spacing: 0.4px; }}
  .items td.num, .items th.num {{ text-align: right; white-space: nowrap; }}
  table.totals {{ border-collapse: collapse; margin-left: auto; min-width: 46%; }}
  .totals td {{ padding: 5px 10px; }}
  .totals .label {{ color: #556; text-align: right; }}
  .totals .value {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
  .totals .grand td {{ border-top: 2px solid #4338ca; font-weight: bold; font-size: 13px; padding-top: 8px; }}
  .pay {{ background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #4338ca;
         padding: 10px 14px; margin-top: 20px; font-size: 10.5px; }}
  .notes {{ margin-top: 14px; color: #445; font-size: 10.5px; white-space: pre-line; }}
  .foot {{ margin-top: 30px; border-top: 1px solid #d9dce3; padding-top: 8px; font-size: 9px; color: #778; }}
</style>
</head>
<body>
  <div class="top">
    <div>
      {logo_html}
      <div class="firm-name">{firm_name}</div>
      <div class="firm-meta">{firm_meta}</div>
    </div>
    <div>
      <h1>{l_title}</h1>
      <div class="inv-no">{l_no} {number}</div>
      <div style="text-align:right"><span class="status {status_class}">{status_label}</span></div>
    </div>
  </div>

  <div class="cols">
    <div class="box">
      <h3>{l_billed_to}</h3>
      <b>{client_name}</b><br>{client_meta}
    </div>
    <div class="box">
      <h3>{l_details}</h3>
      {l_issued}: <b>{issued_on}</b><br>
      {l_due}: <b>{due_on}</b><br>
      {matter_line}
    </div>
  </div>

  <table class="items">
    <tr><th>{l_desc}</th><th class="num">{l_qty}</th><th class="num">{l_unit_price}</th><th class="num">{l_amount}</th></tr>
    {item_rows}
  </table>

  <table class="totals">
    <tr><td class="label">{l_subtotal}</td><td class="value">{subtotal} {currency}</td></tr>
    <tr><td class="label">{l_vat} ({vat_rate}%)</td><td class="value">{vat_amount} {currency}</td></tr>
    <tr class="grand"><td class="label">{l_total_due}</td><td class="value">{total} {currency}</td></tr>
  </table>

  {payment_html}
  {notes_html}

  <div class="foot">
    Gjeneruar nga AvokatIM · {generated_on}{fiscal_foot}
  </div>
</body>
</html>"""


def build_invoice_pdf(
    *,
    invoice: Invoice,
    tenant: Tenant,
    contact: Contact | None,
    matter: Matter | None,
) -> bytes:
    from weasyprint import HTML

    def esc(value: object) -> str:
        return html.escape(str(value)) if value not in (None, "") else "—"

    def money(value) -> str:
        return f"{value:,.2f}".replace(",", " ")

    # Client's language: bilingual labels (sq / client) when it differs
    loc = pick_locale(contact.locale if contact else None, tenant.default_locale)

    firm_meta_parts = []
    if tenant.address:
        firm_meta_parts.append(tenant.address)
    if tenant.fiscal_number:
        firm_meta_parts.append(f"NUI: {tenant.fiscal_number}")
    if tenant.vat_number:
        firm_meta_parts.append(f"Nr. TVSH: {tenant.vat_number}")

    logo_html = ""
    if tenant.logo and tenant.logo.startswith("data:image/"):
        logo_html = f'<img class="logo" src="{tenant.logo}" alt="">'

    client_meta_parts = []
    if contact:
        if contact.address:
            client_meta_parts.append(esc(contact.address))
        if contact.national_id:
            client_meta_parts.append(
                f"{bilabel(loc, 'inv_national_id')}: {esc(contact.national_id)}"
            )
        if contact.email:
            client_meta_parts.append(esc(contact.email))

    item_rows = "".join(
        f"<tr><td>{esc(i.description)}</td>"
        f'<td class="num">{money(i.quantity)}</td>'
        f'<td class="num">{money(i.unit_price)}</td>'
        f'<td class="num">{money(i.amount)}</td></tr>'
        for i in invoice.items
    ) or '<tr><td colspan="4">—</td></tr>'

    if invoice.status == "paid":
        status_class, status_label = "paid", bilabel(loc, "inv_status_paid")
        pay_line = (
            tr(loc, "inv_paid_on", date=f"{invoice.paid_on:%d.%m.%Y}")
            if invoice.paid_on
            else tr(loc, "inv_paid")
        )
        if invoice.payment_reference:
            pay_line += " " + tr(loc, "inv_ref", ref=esc(invoice.payment_reference))
        payment_html = f'<div class="pay"><b>{bilabel(loc, "inv_payment")}</b> {pay_line}</div>'
    else:
        status_class = "unpaid"
        status_key = {"draft": "inv_status_draft", "sent": "inv_status_sent",
                      "void": "inv_status_void"}.get(invoice.status)
        status_label = bilabel(loc, status_key) if status_key else invoice.status.upper()
        bank = esc(tenant.bank_details) if tenant.bank_details else None
        pay_body = tr(loc, "inv_pay_body", number=f"<b>{esc(invoice.number)}</b>")
        if loc != "sq":
            pay_body = (
                tr("sq", "inv_pay_body", number=f"<b>{esc(invoice.number)}</b>")
                + "<br>" + pay_body
            )
        payment_html = (
            f'<div class="pay"><b>{bilabel(loc, "inv_pay_head")}</b> {pay_body}'
            + (f"<br>{bank}" if bank else "")
            + "</div>"
        )

    matter_line = ""
    if matter:
        matter_line = (
            f"{bilabel(loc, 'inv_matter')}: <b>{esc(matter.reference)}</b> — {esc(matter.title)}"
        )

    notes_html = f'<div class="notes">{esc(invoice.notes)}</div>' if invoice.notes else ""

    fiscal_foot = ""
    if tenant.fiscal_number:
        fiscal_foot = f" · {esc(tenant.name)} · NUI {esc(tenant.fiscal_number)}"

    page = _PAGE.format(
        logo_html=logo_html,
        firm_name=esc(tenant.name),
        firm_meta=html.escape("\n".join(firm_meta_parts)),
        number=esc(invoice.number),
        l_title=bilabel(loc, "inv_title"),
        l_no=bilabel(loc, "inv_no"),
        l_billed_to=bilabel(loc, "inv_billed_to"),
        l_details=bilabel(loc, "inv_details"),
        l_issued=bilabel(loc, "inv_issued"),
        l_due=bilabel(loc, "inv_due"),
        l_desc=bilabel(loc, "inv_desc"),
        l_qty=bilabel(loc, "inv_qty"),
        l_unit_price=bilabel(loc, "inv_unit_price"),
        l_amount=bilabel(loc, "inv_amount"),
        l_subtotal=bilabel(loc, "inv_subtotal"),
        l_vat=bilabel(loc, "inv_vat"),
        l_total_due=bilabel(loc, "inv_total_due"),
        status_class=status_class,
        status_label=status_label,
        client_name=esc(contact.display_name if contact else None),
        client_meta="<br>".join(client_meta_parts) or "—",
        issued_on=invoice.issued_on.strftime("%d.%m.%Y") if invoice.issued_on else "—",
        due_on=invoice.due_on.strftime("%d.%m.%Y") if invoice.due_on else "—",
        matter_line=matter_line,
        item_rows=item_rows,
        subtotal=money(invoice.total),
        vat_rate=invoice.vat_rate or 0,
        vat_amount=money(invoice.vat_amount),
        total=money(invoice.total_with_vat),
        currency=esc(invoice.currency),
        payment_html=payment_html,
        notes_html=notes_html,
        generated_on=date.today().strftime("%d.%m.%Y"),
        fiscal_foot=fiscal_foot,
    )
    return HTML(string=page).write_pdf()
