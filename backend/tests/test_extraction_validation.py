"""Tests des règles de cohérence appliquées à une facture extraite."""
from app.schemas.extraction import ExtractedInvoice, LineItem, Supplier
from app.services.extraction import validate_invoice


def _luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _valid_siren() -> str:
    for last in "0123456789":
        candidate = "73282932" + last
        if _luhn_ok(candidate):
            return candidate
    raise AssertionError


def make_invoice(**overrides) -> ExtractedInvoice:
    base = dict(
        document_type="invoice",
        supplier=Supplier(name="Fournisseur SARL", registration_number="", address="1 rue Test"),
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


def test_valid_invoice_with_valid_siret_has_no_warnings():
    siren = _valid_siren()
    siret = None
    for last in "0123456789":
        candidate = siren + "0001" + last
        if _luhn_ok(candidate):
            siret = candidate
            break
    assert siret is not None
    inv = make_invoice(supplier=Supplier(name="Fournisseur SARL", registration_number=siret, address="1 rue Test"))
    assert validate_invoice(inv) == []


def test_invoice_with_bad_siret_is_flagged():
    inv = make_invoice(supplier=Supplier(name="Fournisseur SARL", registration_number="12345678900000", address=""))
    warnings = validate_invoice(inv)
    assert any("SIRET" in w for w in warnings)


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
