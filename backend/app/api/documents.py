"""Routes : upload, consultation, correction et export des documents."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import CurrentUser, get_current_user
from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentOut, DocumentUpdateIn, ExportRequestIn
from app.services import export as export_service
from app.services import storage
from app.workers.tasks import process_document

router = APIRouter(prefix="/documents", tags=["documents"])
settings = get_settings()


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if file.content_type not in settings.ALLOWED_UPLOAD_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Type de fichier non supporté.")

    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Fichier trop volumineux.")

    # TODO Phase 3 : vérifier le compteur d'usage mensuel (UsageCounter) avant d'accepter l'upload.

    key = storage.build_key(user.id, file.filename or "document")
    storage.upload_bytes(key, data, file.content_type)

    doc = Document(
        id=uuid.uuid4(),
        user_id=user.id,
        original_filename=file.filename or "document",
        content_type=file.content_type,
        storage_key=key,
        status=DocumentStatus.QUEUED,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    process_document.delay(str(doc.id))

    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return (
        db.query(Document)
        .filter(Document.user_id == user.id)
        .order_by(Document.created_at.desc())
        .limit(100)
        .all()
    )


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    doc = db.get(Document, document_id)
    if doc is None or doc.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable.")
    return doc


@router.patch("/{document_id}", response_model=DocumentOut)
def update_document(
    document_id: uuid.UUID,
    payload: DocumentUpdateIn,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Corrections manuelles de la fiche extraite (l'utilisateur a le dernier mot)."""
    doc = db.get(Document, document_id)
    if doc is None or doc.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable.")

    doc.extracted_data = payload.extracted_data.model_dump()
    doc.status = DocumentStatus.DONE
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    doc = db.get(Document, document_id)
    if doc is None or doc.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable.")

    if doc.storage_deleted_at is None:
        storage.delete_object(doc.storage_key)
    db.delete(doc)
    db.commit()


@router.post("/export")
def export_documents(
    payload: ExportRequestIn,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    docs = (
        db.query(Document)
        .filter(Document.id.in_(payload.document_ids), Document.user_id == user.id)
        .all()
    )
    if not docs:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucun document trouvé pour cet export.")

    order = {doc_id: i for i, doc_id in enumerate(payload.document_ids)}
    docs.sort(key=lambda d: order.get(d.id, 0))

    if payload.format == "csv":
        content = export_service.build_csv(docs)
        media_type = "text/csv"
        filename = "scantoexcel-factures.csv"
    else:
        content = export_service.build_xlsx(docs)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "scantoexcel-export.xlsx"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
