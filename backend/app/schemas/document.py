"""Schémas Pydantic exposés par l'API pour les documents."""
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.document import DocumentStatus
from app.schemas.extraction import ExtractedInvoice


class DocumentOut(BaseModel):
    id: uuid.UUID
    original_filename: str
    status: DocumentStatus
    confidence: float | None = None
    extracted_data: ExtractedInvoice | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentUpdateIn(BaseModel):
    """Corrections manuelles apportées par l'utilisateur à la fiche extraite."""
    extracted_data: ExtractedInvoice


class ExportRequestIn(BaseModel):
    document_ids: list[uuid.UUID]
    format: str = "xlsx"  # "xlsx" | "csv"
