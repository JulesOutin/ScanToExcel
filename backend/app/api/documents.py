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
from app.services import usage
from app.services.email_templates import near_limit_html
from app.services.extraction import count_pages
from app.workers.tasks import process_document, send_transactional_email

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

    try:
        page_count = count_pages(data, file.content_type)
    except Exception:
        page_count = 1  # un PDF illisible sera de toute façon rejeté à l'extraction

    try:
        should_notify_near_limit = usage.check_and_reserve_pages(db, user.id, page_count, user_email=user.email)
    except usage.UsageLimitExceeded as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            f"Limite du plan gratuit atteinte ({exc.used}/{exc.limit} pages ce mois-ci). Passe à un plan payant pour continuer.",
        ) from exc

    key = storage.build_key(user.id, file.filename or "document")
    try:
        storage.upload_bytes(key, data, file.content_type)
    except Exception:
        usage.release_pages(db, user.id, page_count)
        db.commit()
        raise

    doc = Document(
        id=uuid.uuid4(),
        user_id=user.id,
        user_email=user.email,
        original_filename=file.filename or "document",
        content_type=file.content_type,
        page_count=page_count,
        storage_key=key,
        status=DocumentStatus.QUEUED,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    process_document.delay(str(doc.id))

    if should_notify_near_limit and user.email:
        counter = usage.get_or_create_counter(db, user.id)
        send_transactional_email.delay(
            user.email,
            "Tu approches de ta limite mensuelle gratuite",
            near_limit_html(
                pages_used=counter.pages_used,
                limit=settings.FREE_PLAN_PAGES_PER_MONTH,
                period=counter.period,
                billing_url=f"{settings.FRONTEND_URL}/facturation",
            ),
        )

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


@router.get("/{document_id}/file-url")
def get_document_file_url(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """URL signée temporaire vers le fichier original — pour l'aperçu dans la page de détail."""
    doc = db.get(Document, document_id)
    if doc is None or doc.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable.")
    if doc.storage_deleted_at is not None:
        raise HTTPException(
            status.HTTP_410_GONE,
            "Le fichier original a été supprimé après le délai de rétention. Les données extraites restent disponibles.",
        )
    return {"url": storage.presigned_get_url(doc.storage_key), "content_type": doc.content_type}


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
