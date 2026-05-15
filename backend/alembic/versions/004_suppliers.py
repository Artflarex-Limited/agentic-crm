"""Add suppliers table for AI supplier matching network

Revision ID: 004_suppliers
Revises: 003_product_categories
Create Date: 2026-05-15

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004_suppliers"
down_revision: str | None = "003_product_categories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=False),
        sa.Column("business_email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("industry", sa.String(length=200), nullable=False),
        sa.Column("production_capacity", sa.String(length=100), nullable=True),
        sa.Column("certifications", sa.JSON(), nullable=True),
        sa.Column("exporting_to_eu", sa.Boolean(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("waitlist_position", sa.Integer(), nullable=True),
        sa.Column("status", sa.Enum("pending", "verified", "rejected", "suspended", name="supplierstatus"), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_suppliers_id"), "suppliers", ["id"], unique=False)
    op.create_index(op.f("ix_suppliers_country"), "suppliers", ["country"], unique=False)
    op.create_index(op.f("ix_suppliers_industry"), "suppliers", ["industry"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_suppliers_industry"))
    op.drop_index(op.f("ix_suppliers_country"))
    op.drop_index(op.f("ix_suppliers_id"))
    op.drop_table("suppliers")