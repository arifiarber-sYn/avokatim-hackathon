"""ZUGFeRD/Factur-X e-invoice generation (D-037 phase 2)."""
from datetime import date
from decimal import Decimal

from lxml import etree

from app.models import Contact, Invoice, InvoiceItem, Tenant
from app.services.einvoice import attach_to_pdf, build_zugferd_xml


def _sample():
    tenant = Tenant(
        name="Kanzlei Muster",
        country="DE",
        address="Musterstraße 1, 10115 Berlin",
        vat_number="DE123456789",
        fiscal_number="30/123/45678",
        iban="DE89 3704 0044 0532 0130 00",
    )
    contact = Contact(
        display_name="Beispiel GmbH", address="Beispielweg 2, 80331 München"
    )
    # totals and item amounts are computed properties (from items / qty x price)
    invoice = Invoice(
        number="RE-2026-0042",
        currency="EUR",
        issued_on=date(2026, 8, 1),
        due_on=date(2026, 8, 15),
        vat_rate=19,
    )
    invoice.items = [
        InvoiceItem(
            description="Verfahrensgebühr (1. Instanz) (VV 3100)",
            quantity=Decimal("1"),
            unit_price=Decimal("460.85"),
        ),
        InvoiceItem(
            description="Terminsgebühr (VV 3104)",
            quantity=Decimal("1"),
            unit_price=Decimal("425.40"),
        ),
        InvoiceItem(
            description="Auslagenpauschale (VV 7002)",
            quantity=Decimal("1"),
            unit_price=Decimal("20.00"),
        ),
    ]
    return invoice, tenant, contact


def test_zugferd_xml_is_valid_cii():
    invoice, tenant, contact = _sample()
    xml = build_zugferd_xml(invoice, tenant, contact)
    root = etree.fromstring(xml)
    assert root.tag.endswith("CrossIndustryInvoice")
    text = xml.decode("utf-8")
    assert "urn:cen.eu:en16931:2017" in text
    assert "RE-2026-0042" in text
    assert "1078.44" in text  # grand total
    assert "DE123456789" in text  # USt-IdNr
    assert "DE89370400440532013000" in text  # IBAN without spaces
    assert text.count("IncludedSupplyChainTradeLineItem") == 6  # 3 open + 3 close


def test_hybrid_pdf_embeds_facturx():
    from weasyprint import HTML

    invoice, tenant, contact = _sample()
    xml = build_zugferd_xml(invoice, tenant, contact)
    pdf = HTML(string="<html><body><p>Rechnung RE-2026-0042</p></body></html>").write_pdf()
    hybrid = attach_to_pdf(pdf, xml)
    assert hybrid[:5] == b"%PDF-"
    assert b"factur-x.xml" in hybrid
    assert len(hybrid) > len(pdf)
