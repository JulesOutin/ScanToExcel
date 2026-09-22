"""Tests de l'export comptable FEC."""
from types import SimpleNamespace
import uuid

from app.services.fec_export import FEC_COLUMNS, build_fec, fec_filename


def make_doc(**extracted_overrides):
    data = dict(
        supplier={"name": "Fournisseur SARL", "registration_number": "", "address": ""},
        invoice_number="F-001",
        invoice_date="2026-09-01",
        currency="EUR",
        subtotal=100.0,
        tax=20.0,
        total=120.0,
    )
    data.update(extracted_overrides)
    return SimpleNamespace(id=uuid.uuid4(), extracted_data=data, confidence=0.9)


def test_header_matches_fec_spec_columns():
    content = build_fec([make_doc()]).decode("utf-8")
    header = content.splitlines()[0].split("\t")
    assert header == FEC_COLUMNS


def test_one_invoice_produces_three_balanced_lines():
    content = build_fec([make_doc()]).decode("utf-8")
    lines = [l for l in content.splitlines()[1:] if l.strip()]
    assert len(lines) == 3  # achats (débit) + TVA (débit) + fournisseurs (crédit)

    debit_idx = FEC_COLUMNS.index("Debit")
    credit_idx = FEC_COLUMNS.index("Credit")

    def to_float(s: str) -> float:
        return float(s.replace(",", ".")) if s else 0.0

    total_debit = sum(to_float(l.split("\t")[debit_idx]) for l in lines)
    total_credit = sum(to_float(l.split("\t")[credit_idx]) for l in lines)
    assert round(total_debit, 2) == round(total_credit, 2) == 120.0  # écriture équilibrée


def test_dates_are_formatted_without_separators():
    content = build_fec([make_doc(invoice_date="2026-09-01")]).decode("utf-8")
    date_idx = FEC_COLUMNS.index("EcritureDate")
    first_row = content.splitlines()[1].split("\t")
    assert first_row[date_idx] == "20260901"


def test_zero_amount_lines_are_omitted():
    content = build_fec([make_doc(subtotal=0, tax=0, total=100.0)]).decode("utf-8")
    lines = [l for l in content.splitlines()[1:] if l.strip()]
    assert len(lines) == 1  # seule la ligne fournisseurs (crédit) est écrite


def test_filename_uses_configured_siren():
    name = fec_filename()
    assert name.endswith(".txt")
    assert "FEC" in name
