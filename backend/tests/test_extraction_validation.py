"""Tests des règles de cohérence appliquées à une facture extraite."""
from app.schemas.extraction import ExtractedInvoice, LineItem, Supplier
from app.services.extraction import validate_invoice


def make_invoice(**overrides) -> ExtractedInvoice:
    base = dict(
        document_type="invoice",
        supplier=Supplier(name="Fournisseur SARL", registration_number="FR12345678901", address="1 rue Test"),
        invoice_number="F-2026-001",
        invoice_date="2026-09-01",
        due_date="2026-10-01",
        currency="EUR",
        subtotal=100.0,
        tax=20.0,
        total=120.0,
        items=[LineItem(description="Prestation", quantity=1, unit_price=100.0, tax_rate=20, total=100.0)],
        confidence=0.9,
    )
    base.update(overrides)
    return ExtractedInvoice(**base)


def test_valid_invoice_has_no_warnings():
    inv = make_invoice()
    assert validate_invoice(inv) == []


def test_subtotal_plus_tax_mismatch_is_flagged():
    inv = make_invoice(total=999.0)
    warnings = validate_invoice(inv)
    assert any("Sous-total" in w for w in warnings)


def test_missing_invoice_number_is_flagged():
    inv = make_invoice(invoice_number="")
    warnings = validate_invoice(inv)
    assert any("Numéro de facture" in w for w in warnings)


def test_bad_currency_is_flagged():
    inv = make_invoice(currency="EU")
    warnings = validate_invoice(inv)
    assert any("Devise" in w for w in warnings)


def test_line_item_quantity_price_mismatch_is_flagged():
    inv = make_invoice(items=[LineItem(description="X", quantity=2, unit_price=10, tax_rate=20, total=999)])
    warnings = validate_invoice(inv)
    assert any("Ligne 1" in w for w in warnings)


def test_zero_total_line_item_is_not_flagged():
    # une ligne à 0 (pas encore remplie) ne doit pas générer un faux positif
    inv = make_invoice(items=[LineItem(description="", quantity=1, unit_price=0, tax_rate=0, total=0)])
    warnings = validate_invoice(inv)
    assert not any("Ligne 1" in w for w in warnings)
