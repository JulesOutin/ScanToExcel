"""ajoute la table subscriptions (Stripe)

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

subscription_plan = postgresql.ENUM("free", "personal", "pro", name="subscription_plan")
subscription_status = postgresql.ENUM("active", "past_due", "canceled", "incomplete", name="subscription_status")


def upgrade():
    subscription_plan.create(op.get_bind(), checkfirst=True)
    subscription_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String, nullable=False, unique=True, index=True),
        sa.Column("plan", subscription_plan, nullable=False, server_default="free"),
        sa.Column("status", subscription_status, nullable=False, server_default="active"),
        sa.Column("stripe_customer_id", sa.String, nullable=True, index=True),
        sa.Column("stripe_subscription_id", sa.String, nullable=True, index=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("subscriptions")
    subscription_status.drop(op.get_bind(), checkfirst=True)
    subscription_plan.drop(op.get_bind(), checkfirst=True)
