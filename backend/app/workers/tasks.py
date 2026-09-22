"""Tâches asynchrones : l'API dépose une tâche, le worker fait l'extraction en arrière-plan."""
import logging

from app.core.db import SessionLocal
from app.models.document import Document, DocumentStatus
from app.services import storage
from app.services.extraction import ExtractionError, extract_invoice, validate_invoice
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.process_document", bind=True, max_retries=2)
def process_document(self, document_id: str) -> None:
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if doc is None:
            logger.warning("Document %s introuvable (tâche ignorée)", document_id)
            return

        doc.status = DocumentStatus.PROCESSING
        db.commit()

        try:
            file_bytes = storage.download_bytes(doc.storage_key)
            invoice = extract_invoice(file_bytes, doc.content_type)
            warnings = validate_invoice(invoice)

            doc.extracted_data = invoice.model_dump()
            doc.confidence = invoice.confidence
            doc.status = DocumentStatus.NEEDS_REVIEW if warnings else DocumentStatus.DONE
            doc.error_message = None
        except ExtractionError as exc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(exc)

        db.commit()
    finally:
        db.close()
