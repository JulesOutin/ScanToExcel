"""
Service d'extraction : convertit un document (image ou 1ère page de PDF) en
JSON structuré via l'API Claude (multimodal), selon le schéma ExtractedInvoice.

Ce module fait le pont entre "fichier brut" et "JSON validé" ; il ne connaît
ni la base de données ni la file de tâches — voir app/workers/tasks.py pour
l'orchestration asynchrone.
"""
import base64
import io
import json

import anthropic
import pypdfium2 as pdfium
from PIL import Image

from app.core.config import get_settings
from app.schemas.extraction import EXTRACTION_JSON_SCHEMA_EXAMPLE, ExtractedInvoice

settings = get_settings()

EXTRACTION_PROMPT = f"""Tu es un moteur d'extraction de données pour un outil qui convertit des \
factures en tableur. Analyse l'image jointe (une facture, un reçu, ou un document assimilé) et \
réponds UNIQUEMENT avec un objet JSON, sans aucun texte autour, au format exact suivant :

{json.dumps(EXTRACTION_JSON_SCHEMA_EXAMPLE, ensure_ascii=False)}

Règles :
- Utilise une chaîne vide ou 0 quand une information est absente ou illisible ; ne l'invente jamais.
- Tous les montants et quantités sont des nombres JSON (jamais de symbole monétaire, jamais de texte).
- tax_rate est un pourcentage (ex. 20 pour 20 %).
- confidence est un nombre entre 0 et 1 reflétant ta confiance globale dans l'extraction.
- Si le document n'est pas une facture ni un reçu, mets document_type à "other" et remplis les \
champs visibles du mieux possible."""


class ExtractionError(Exception):
    pass


def count_pages(file_bytes: bytes, content_type: str) -> int:
    """Nombre de pages du document — sert au comptage d'usage (1 pour une image)."""
    if content_type != "application/pdf":
        return 1
    pdf = pdfium.PdfDocument(file_bytes)
    return max(1, len(pdf))


def pdf_first_page_to_png(pdf_bytes: bytes, scale: float = 2.0) -> bytes:
    """Rend la première page d'un PDF en PNG (pour l'envoyer au modèle multimodal)."""
    pdf = pdfium.PdfDocument(pdf_bytes)
    page = pdf[0]
    bitmap = page.render(scale=scale)
    pil_image: Image.Image = bitmap.to_pil()
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return buf.getvalue()


def extract_invoice(file_bytes: bytes, content_type: str) -> ExtractedInvoice:
    """
    file_bytes : contenu brut du fichier (PDF ou image).
    content_type : type MIME d'origine.
    Retourne une ExtractedInvoice validée par Pydantic.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise ExtractionError("ANTHROPIC_API_KEY manquante — configure-la dans .env")

    if content_type == "application/pdf":
        image_bytes = pdf_first_page_to_png(file_bytes)
        media_type = "image/png"
    else:
        image_bytes = file_bytes
        media_type = content_type

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=settings.EXTRACTION_MODEL,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            },
                        },
                        {"type": "text", "text": EXTRACTION_PROMPT},
                    ],
                }
            ],
        )
    except anthropic.APIError as exc:
        raise ExtractionError(f"Appel au modèle échoué : {exc}") from exc

    text_blocks = [b.text for b in response.content if b.type == "text"]
    raw_text = "\n".join(text_blocks).strip()

    # Tolère un bloc ```json ... ``` autour de la réponse.
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ExtractionError(f"Réponse non-JSON du modèle : {raw_text[:200]}") from exc

    return ExtractedInvoice.model_validate(data)


def validate_invoice(inv: ExtractedInvoice) -> list[str]:
    """Contrôles de cohérence — mêmes règles que le prototype front."""
    warnings: list[str] = []

    if inv.total and abs((inv.subtotal + inv.tax) - inv.total) > 0.02:
        warnings.append(
            f"Sous-total + TVA ({inv.subtotal + inv.tax:.2f}) ne correspond pas au total ({inv.total:.2f})."
        )
    if not inv.invoice_number:
        warnings.append("Numéro de facture manquant.")
    if not inv.currency or len(inv.currency) != 3:
        warnings.append("Devise absente ou incorrecte.")
    for idx, item in enumerate(inv.items, start=1):
        expected = item.quantity * item.unit_price
        if item.total and abs(expected - item.total) > max(0.02, expected * 0.02):
            warnings.append(f"Ligne {idx} : quantité × prix unitaire ≠ total de ligne.")
    return warnings
