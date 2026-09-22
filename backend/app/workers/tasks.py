"""Tâches asynchrones : l'API dépose une tâche, le worker fait l'extraction en arrière-plan."""
import logging
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.models.document import Document, DocumentStatus
from app.services import storage
from app.services.extraction import ExtractionError, extract_invoice, validate_invoice
from app.workers.celery_app import celery_app

settings = get_settings()

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


@celery_app.task(name="app.workers.tasks.purge_expired_originals")
def purge_expired_originals() -> int:
    """
    Supprime du stockage objet les fichiers originaux plus vieux que
    ORIGINAL_FILE_RETENTION_HOURS et dont l'extraction est terminée (ou en échec) —
    on ne touche jamais un document encore en file ou en cours de traitement.
    Les données extraites (`extracted_data`) restent en base : seul le fichier
    source est purgé. Retourne le nombre de documents purgés (pratique pour les tests).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.ORIGINAL_FILE_RETENTION_HOURS)
    db = SessionLocal()
    purged = 0
    try:
        candidates = (
            db.query(Document)
            .filter(
                Document.storage_deleted_at.is_(None),
                Document.created_at < cutoff,
                Document.status.in_([DocumentStatus.DONE, DocumentStatus.NEEDS_REVIEW, DocumentStatus.FAILED]),
            )
            .all()
        )
        for doc in candidates:
            try:
                storage.delete_object(doc.storage_key)
                doc.storage_deleted_at = datetime.now(timezone.utc)
                purged += 1
            except Exception:
                logger.exception("Échec de suppression du fichier original pour le document %s", doc.id)
        db.commit()
    finally:
        db.close()
    return purged
