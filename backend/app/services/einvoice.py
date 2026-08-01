"""E-Rechnung (EN 16931) for German offices: a Factur-X/ZUGFeRD CII XML is
generated from the invoice and embedded into the WeasyPrint PDF, turning it
into a hybrid e-invoice (§ 14 UStG as amended by the Wachstumschancengesetz —
issuing becomes mandatory for B2B in 2027/2028). The raw XML is also offered
as a download for recipients that want the pure machine-readable form.

Uses `drafthorse` (EN 16931 profile). The tenant's `vat_number` becomes the
seller USt-IdNr (scheme VA), `fiscal_number` the Steuernummer (scheme FC),
and `iban` the SEPA payment means. Free-text addresses go to address line
one — fine for EN 16931's single-line fallback."""
import re
from datetime import date
from decimal import Decimal

from app.models import Contact, Invoice, Tenant

_UNIT = "C62"  # "one/unit" — invoice items are description + qty x price


def _q(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _fill_address(address_el, free_text: str | None, country: str) -> None:
    """Split a free-text address into EN 16931 components when it follows the
    German convention "Straße Nr., PLZ Stadt"; otherwise line one only."""
    address_el.country_id = country
    if not free_text:
        return
    text = free_text.strip()[:256]
    match = re.match(r"^(.*?),\s*(\d{4,5})\s+(.+)$", text)
    if match:
        address_el.line_one = match.group(1)[:128]
        address_el.postcode = match.group(2)
        address_el.city_name = match.group(3)[:64]
    else:
        address_el.line_one = text[:128]


def build_zugferd_xml(
    invoice: Invoice, tenant: Tenant, contact: Contact | None
) -> bytes:
    """EN 16931 (COMFORT) CII XML for the invoice."""
    from drafthorse.models.accounting import ApplicableTradeTax
    from drafthorse.models.document import Document
    from drafthorse.models.party import TaxRegistration
    from drafthorse.models.payment import PaymentMeans, PaymentTerms
    from drafthorse.models.tradelines import LineItem

    doc = Document()
    doc.context.guideline_parameter.id = (
        "urn:cen.eu:en16931:2017"  # EN 16931 compliance level
    )
    doc.header.id = invoice.number
    doc.header.type_code = "380"  # commercial invoice
    doc.header.issue_date_time = invoice.issued_on or date.today()

    seller = doc.trade.agreement.seller
    seller.name = tenant.name
    _fill_address(seller.address, tenant.address, tenant.country or "DE")
    if tenant.vat_number:
        seller.tax_registrations.add(TaxRegistration(id=("VA", tenant.vat_number)))
    if tenant.fiscal_number:
        seller.tax_registrations.add(TaxRegistration(id=("FC", tenant.fiscal_number)))

    buyer = doc.trade.agreement.buyer
    buyer.name = contact.display_name if contact else "—"
    # Domestic B2B is the mandate's scope; the client country isn't stored
    _fill_address(
        buyer.address, contact.address if contact else None, tenant.country or "DE"
    )

    settlement = doc.trade.settlement
    settlement.currency_code = invoice.currency or "EUR"

    if tenant.iban:
        means = PaymentMeans()
        means.type_code = "58"  # SEPA credit transfer
        means.payee_account.iban = tenant.iban.replace(" ", "")
        settlement.payment_means.add(means)

    vat_rate = Decimal(invoice.vat_rate or 0)
    for idx, item in enumerate(invoice.items, start=1):
        li = LineItem()
        li.document.line_id = str(idx)
        li.product.name = item.description[:256]
        li.agreement.net.amount = _q(item.unit_price)
        li.agreement.net.basis_quantity = (Decimal("1"), _UNIT)
        li.delivery.billed_quantity = (_q(item.quantity), _UNIT)
        li.settlement.trade_tax.type_code = "VAT"
        li.settlement.trade_tax.category_code = "S" if vat_rate else "Z"
        li.settlement.trade_tax.rate_applicable_percent = vat_rate
        li.settlement.monetary_summation.total_amount = _q(item.amount)
        doc.trade.items.add(li)

    net = _q(invoice.total)
    vat = _q(invoice.vat_amount)
    tax = ApplicableTradeTax()
    tax.calculated_amount = vat
    tax.basis_amount = net
    tax.type_code = "VAT"
    tax.category_code = "S" if vat_rate else "Z"
    tax.rate_applicable_percent = vat_rate
    settlement.trade_tax.add(tax)

    if invoice.due_on:
        terms = PaymentTerms()
        terms.description = f"Zahlbar bis {invoice.due_on:%d.%m.%Y}"
        terms.due = invoice.due_on
        settlement.terms.add(terms)

    summation = settlement.monetary_summation
    summation.line_total = net
    summation.charge_total = Decimal("0.00")
    summation.allowance_total = Decimal("0.00")
    summation.tax_basis_total = net
    summation.tax_total = (vat, invoice.currency or "EUR")
    summation.grand_total = _q(invoice.total_with_vat)
    summation.due_amount = _q(invoice.total_with_vat)

    return doc.serialize(schema="FACTUR-X_EN16931")


def attach_to_pdf(pdf: bytes, xml: bytes) -> bytes:
    """Embed the CII XML into the PDF (Factur-X/ZUGFeRD hybrid, PDF/A-3)."""
    from drafthorse.pdf import attach_xml

    return attach_xml(pdf, xml, "EN 16931")
