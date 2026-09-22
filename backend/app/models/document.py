"""Modèles SQLAlchemy : utilisateurs (référence Supabase) et documents traités."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"  # extrait, mais des incohérences ont été détectées
    DONE = "done"
    FAILED = "failed"


class Document(Base):
    """
    Une facture / justificatif importé par un utilisateur.

    `extracted_data` suit strictement le schéma JSON du pipeline d'extraction
    (voir app/schemas/extraction.py) : c'est la source de vérité pour l'export.
    """
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)  # Supabase auth.users.id
    user_email: Mapped[str | None] = mapped_column(String, nullable=True)  # capturé au moment de l'upload, pour les emails transactionnels

    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=1)

    storage_key: Mapped[str] = mapped_column(String, nullable=False)  # chemin dans le bucket S3/R2
    storage_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"), default=DocumentStatus.UPLOADED, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    extracted_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # schéma facture, voir extraction.py
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    export_batches: Mapped[list["ExportBatchItem"]] = relationship(back_populates="document")


class ExportBatch(Base):
    """Un export Excel/CSV généré à partir d'un ou plusieurs documents."""
    __tablename__ = "export_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    format: Mapped[str] = mapped_column(String, nullable=False)  # "xlsx" | "csv"
    storage_key: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list["ExportBatchItem"]] = relationship(back_populates="batch")


class ExportBatchItem(Base):
    """Table d'association batch <-> document (many-to-many avec ordre)."""
    __tablename__ = "export_batch_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("export_batches.id"), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)

    batch: Mapped["ExportBatch"] = relationship(back_populates="items")
    document: Mapped["Document"] = relationship(back_populates="export_batches")


class UsageCounter(Base):
    """Compteur mensuel de pages traitées par utilisateur, pour la limite du plan gratuit."""
    __tablename__ = "usage_counters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)  # "2026-09"
    pages_used: Mapped[int] = mapped_column(Integer, default=0)
    user_email: Mapped[str | None] = mapped_column(String, nullable=True)
    near_limit_notified: Mapped[bool] = mapped_column(default=False)  # évite de renvoyer l'alerte plusieurs fois par période


class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    PERSONAL = "personal"
    PRO = "pro"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"


class Subscription(Base):
    """Abonnement Stripe d'un utilisateur — une ligne par utilisateur payant ou gratuit."""
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    plan: Mapped[SubscriptionPlan] = mapped_column(
        Enum(SubscriptionPlan, name="subscription_plan"), default=SubscriptionPlan.FREE, nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"), default=SubscriptionStatus.ACTIVE, nullable=False
    )

    stripe_customer_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
