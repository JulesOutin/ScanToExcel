"""Schéma pivot de l'extraction — identique à celui utilisé par le prototype."""
from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str = ""
    quantity: float = 1
    unit_price: float = 0
    tax_rate: float = 0
    total: float = 0


class Supplier(BaseModel):
    name: str = ""
    registration_number: str = ""  # SIRET / n° TVA
    address: str = ""


class ExtractedInvoice(BaseModel):
    document_type: str = Field(default="invoice")  # invoice | receipt | other
    supplier: Supplier = Field(default_factory=Supplier)
    invoice_number: str = ""
    invoice_date: str = ""  # AAAA-MM-JJ
    due_date: str = ""
    currency: str = "EUR"
    subtotal: float = 0
    tax: float = 0
    total: float = 0
    items: list[LineItem] = Field(default_factory=list)
    confidence: float = 0


EXTRACTION_JSON_SCHEMA_EXAMPLE = {
    "document_type": "invoice",
    "supplier": {"name": "", "registration_number": "", "address": ""},
    "invoice_number": "",
    "invoice_date": "",
    "due_date": "",
    "currency": "EUR",
    "subtotal": 0,
    "tax": 0,
    "total": 0,
    "items": [
        {"description": "", "quantity": 1, "unit_price": 0, "tax_rate": 0, "total": 0}
    ],
    "confidence": 0,
}
