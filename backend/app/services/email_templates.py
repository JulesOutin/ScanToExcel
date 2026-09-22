"""Gabarits HTML des emails transactionnels — sobres, cohérents avec le ton du produit."""

_WRAPPER = """\
<div style="font-family: 'IBM Plex Sans', Helvetica, Arial, sans-serif; color:#1c231f; max-width:480px; margin:0 auto; padding:24px;">
  <p style="font-family:monospace; font-size:12px; color:#4b564e; letter-spacing:.02em; margin:0 0 16px;">SCANTOEXCEL</p>
  {body}
  <p style="font-size:12px; color:#4b564e; margin-top:32px;">Tu reçois cet email car tu as un compte ScanToExcel.</p>
</div>
"""


def confirmation_html(*, invoice_number: str, supplier_name: str, total: float, currency: str, document_url: str) -> str:
    body = f"""
    <h1 style="font-size:20px; margin:0 0 12px;">Ta facture est prête</h1>
    <p style="font-size:14px; line-height:1.5;">
      {supplier_name or "Une facture"}{" — " + invoice_number if invoice_number else ""} a été extraite
      ({total:.2f} {currency}). Les données sont modifiables avant export.
    </p>
    <p style="margin-top:20px;">
      <a href="{document_url}" style="background:#2f6f5e; color:#fff; padding:10px 16px; border-radius:8px; text-decoration:none; font-size:14px;">
        Vérifier la fiche
      </a>
    </p>
    """
    return _WRAPPER.format(body=body)


def near_limit_html(*, pages_used: int, limit: int, period: str, billing_url: str) -> str:
    body = f"""
    <h1 style="font-size:20px; margin:0 0 12px;">Tu approches de ta limite gratuite</h1>
    <p style="font-size:14px; line-height:1.5;">
      {pages_used} pages sur {limit} utilisées ce mois-ci ({period}). Passé ce seuil,
      les nouveaux envois seront refusés jusqu'au mois prochain — ou tu peux passer
      à un plan payant dès maintenant.
    </p>
    <p style="margin-top:20px;">
      <a href="{billing_url}" style="background:#2f6f5e; color:#fff; padding:10px 16px; border-radius:8px; text-decoration:none; font-size:14px;">
        Voir les plans
      </a>
    </p>
    """
    return _WRAPPER.format(body=body)
