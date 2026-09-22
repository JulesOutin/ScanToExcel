"""
Export au format FEC (Fichier des Écritures Comptables) — le format d'échange
comptable standardisé par l'administration fiscale française (article A47 A-1
du LPF), importable tel quel par Pennylane, Sage, QuickBooks, Indy, Cegid, etc.

Chaque facture fournisseur est traduite en une écriture à 3 lignes :
  - débit  : compte d'achats (montant HT)
  - débit  : compte de TVA déductible (montant de la taxe)
  - crédit : compte fournisseurs (montant TTC)

Les comptes utilisés sont des comptes génériques configurables
(FEC_ACCOUNT_*) — un cabinet comptable réel les ajustera à son propre plan
comptable ; ScanToExcel ne prétend pas connaître la comptabilité analytique
de l'utilisateur.
"""
import io
from datetime import date

from app.core.config import get_settings
from app.models.document import Document

settings = get_settings()

FEC_COLUMNS = [
    "JournalCode", "JournalLib", "EcritureNum", "EcritureDate",
    "CompteNum", "CompteLib", "CompAuxNum", "CompAuxLib",
    "PieceRef", "PieceDate", "EcritureLib",
    "Debit", "Credit", "EcritureLet", "DateLet",
    "ValidDate", "Montantdevise", "Idevise",
]


def _fmt_date(value: str) -> str:
    """AAAA-MM-JJ -> AAAAMMJJ (format FEC) ; chaîne vide si la date est absente/invalide."""
    if not value:
        return ""
    digits = value.replace("-", "")
    return digits if len(digits) == 8 else ""


def _fmt_amount(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")  # convention FEC : virgule décimale


def _invoice_lines(doc: Document, ecriture_num: int) -> list[list[str]]:
    d = doc.extracted_data or {}
    supplier_name = (d.get("supplier") or {}).get("name", "") or "Fournisseur inconnu"
    invoice_ref = d.get("invoice_number", "") or str(doc.id)
    invoice_date = _fmt_date(d.get("invoice_date", ""))
    subtotal = float(d.get("subtotal") or 0)
    tax = float(d.get("tax") or 0)
    total = float(d.get("total") or 0)
    label = f"{supplier_name} {invoice_ref}".strip()

    rows = []
    common = lambda compte, compte_lib, debit, credit: [
        "ACH", "Achats", str(ecriture_num), invoice_date,
        compte, compte_lib, "", "",
        invoice_ref, invoice_date, label,
        _fmt_amount(debit), _fmt_amount(credit), "", "",
        invoice_date, "", "",
    ]

    if subtotal:
        rows.append(common(settings.FEC_ACCOUNT_PURCHASES, "Achats", subtotal, 0))
    if tax:
        rows.append(common(settings.FEC_ACCOUNT_VAT_DEDUCTIBLE, "TVA déductible", tax, 0))
    if total:
        rows.append(common(settings.FEC_ACCOUNT_SUPPLIERS, "Fournisseurs", 0, total))
    return rows


def build_fec(documents: list[Document]) -> bytes:
    buf = io.StringIO()
    buf.write("\t".join(FEC_COLUMNS) + "\r\n")
    for i, doc in enumerate(documents, start=1):
        for row in _invoice_lines(doc, ecriture_num=i):
            buf.write("\t".join(row) + "\r\n")
    return buf.getvalue().encode("utf-8")


def fec_filename() -> str:
    siren = settings.COMPANY_SIREN or "SIREN"
    return f"{siren}FEC{date.today():%Y%m%d}.txt"
