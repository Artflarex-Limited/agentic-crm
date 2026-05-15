"""Add procurement tables for supplier procurement network

Revision ID: 005_procurement
Revises: 004_suppliers
Create Date: 2026-05-16

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "005_procurement"
down_revision: str | None = "004_suppliers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "procurement_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.String(length=100), nullable=True),
        sa.Column("target_price", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("requested_delivery_date", sa.DateTime(), nullable=True),
        sa.Column("status", sa.Enum("draft", "submitted", "quotes_received", "approved", "in_production", "shipped", "delivered", "cancelled", name="procurementstatus"), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("assigned_agent_id", sa.Integer(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["product_categories.id"], ),
        sa.ForeignKeyConstraint(["assigned_agent_id"], ["agents.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_procurement_requests_id"), "procurement_requests", ["id"], unique=False)

    op.create_table(
        "quotes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("procurement_request_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("lead_time_days", sa.Integer(), nullable=True),
        sa.Column("validity_days", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("pending", "sent", "accepted", "rejected", "expired", name="quotestatus"), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["procurement_request_id"], ["procurement_requests.id"], ),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quotes_id"), "quotes", ["id"], unique=False)

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("procurement_request_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("quote_id", sa.Integer(), nullable=True),
        sa.Column("order_number", sa.String(length=100), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("status", sa.Enum("draft", "issued", "confirmed", "shipped", "delivered", "cancelled", name="purchaseorderstatus"), nullable=True),
        sa.Column("expected_delivery_date", sa.DateTime(), nullable=True),
        sa.Column("actual_delivery_date", sa.DateTime(), nullable=True),
        sa.Column("shipping_address", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["procurement_request_id"], ["procurement_requests.id"], ),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number"),
    )
    op.create_index(op.f("ix_purchase_orders_id"), "purchase_orders", ["id"], unique=False)

    op.create_table(
        "shipments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("tracking_number", sa.String(length=255), nullable=True),
        sa.Column("carrier", sa.String(length=100), nullable=True),
        sa.Column("status", sa.Enum("preparing", "in_transit", "customs", "delivered", "exception", name="shipmentstatus"), nullable=True),
        sa.Column("shipping_date", sa.DateTime(), nullable=True),
        sa.Column("estimated_delivery_date", sa.DateTime(), nullable=True),
        sa.Column("actual_delivery_date", sa.DateTime(), nullable=True),
        sa.Column("shipping_address", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_shipments_id"), "shipments", ["id"], unique=False)

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("invoice_number", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("status", sa.Enum("draft", "sent", "paid", "overdue", "cancelled", name="invoicestatus"), nullable=True),
        sa.Column("issue_date", sa.DateTime(), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("paid_date", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_number"),
    )
    op.create_index(op.f("ix_invoices_id"), "invoices", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_invoices_id"))
    op.drop_table("invoices")
    op.drop_index(op.f("ix_shipments_id"))
    op.drop_table("shipments")
    op.drop_index(op.f("ix_purchase_orders_id"))
    op.drop_table("purchase_orders")
    op.drop_index(op.f("ix_quotes_id"))
    op.drop_table("quotes")
    op.drop_index(op.f("ix_procurement_requests_id"))
    op.drop_table("procurement_requests")