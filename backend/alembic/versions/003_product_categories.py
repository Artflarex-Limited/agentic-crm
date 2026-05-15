"""Add product_categories table for AI categorization taxonomy

Revision ID: 003_product_categories
Revises: 002_tracking_fields
Create Date: 2026-05-15

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "003_product_categories"
down_revision: str | None = "002_tracking_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family", sa.String(length=100), nullable=False),
        sa.Column("cls", sa.String(length=100), nullable=False),
        sa.Column("commodity", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_product_categories_family", "product_categories", ["family"])
    op.create_index("ix_product_categories_cls", "product_categories", ["cls"])


def downgrade() -> None:
    op.drop_index("ix_product_categories_cls")
    op.drop_index("ix_product_categories_family")
    op.drop_table("product_categories")