"""Add tracking fields to leads - UTM, HubSpot, GA4

Revision ID: 002_tracking_fields
Revises: 001_initial
Create Date: 2026-05-14

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002_tracking_fields"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("utm_source", sa.String(length=255), nullable=True))
    op.add_column("leads", sa.Column("utm_medium", sa.String(length=255), nullable=True))
    op.add_column("leads", sa.Column("utm_campaign", sa.String(length=255), nullable=True))
    op.add_column("leads", sa.Column("utm_term", sa.String(length=255), nullable=True))
    op.add_column("leads", sa.Column("utm_content", sa.String(length=255), nullable=True))
    op.add_column("leads", sa.Column("hubspot_contact_id", sa.String(length=255), nullable=True))
    op.add_column("leads", sa.Column("ga_client_id", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("leads", "ga_client_id")
    op.drop_column("leads", "hubspot_contact_id")
    op.drop_column("leads", "utm_content")
    op.drop_column("leads", "utm_term")
    op.drop_column("leads", "utm_campaign")
    op.drop_column("leads", "utm_medium")
    op.drop_column("leads", "utm_source")