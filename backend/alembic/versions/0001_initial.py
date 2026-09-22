"""schema initial : documents, export_batches, export_batch_items, usage_counters

Revision ID: 0001
Revises:
Create Date: 2026-09-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

document_status = postgresql.ENUM(
    "uploaded", "queued", "processing", "needs_review", "done", "failed",
    name="document_status",
)


def upgrade():
    document_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String, nullable=False, index=True),
        sa.Column("original_filename", sa.String, nullable=False),
        sa.Column("content_type", sa.String, nullable=False),
        sa.Column("page_count", sa.Integer, server_default="1"),
        sa.Column("storage_key", sa.String, nullable=False),
        sa.Column("storage_deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", document_status, nullable=False, server_default="uploaded"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("extracted_data", postgresql.JSONB, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_documents_user_id", "documents", ["user_id"])

    op.create_table(
        "export_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String, nullable=False, index=True),
        sa.Column("format", sa.String, nullable=False),
        sa.Column("storage_key", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_export_batches_user_id", "export_batches", ["user_id"])

    op.create_table(
        "export_batch_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("export_batches.id"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("position", sa.Integer, server_default="0"),
    )

    op.create_table(
        "usage_counters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String, nullable=False, index=True),
        sa.Column("period", sa.String, nullable=False),
        sa.Column("pages_used", sa.Integer, server_default="0"),
    )
    op.create_index("ix_usage_counters_user_id", "usage_counters", ["user_id"])


def downgrade():
    op.drop_table("usage_counters")
    op.drop_table("export_batch_items")
    op.drop_table("export_batches")
    op.drop_index("ix_documents_user_id", table_name="documents")
    op.drop_table("documents")
    document_status.drop(op.get_bind(), checkfirst=True)
