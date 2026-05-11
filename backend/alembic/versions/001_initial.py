"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2026-05-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # companies table
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("size", sa.String(length=50), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_companies_domain"), "companies", ["domain"], unique=False)
    op.create_index(op.f("ix_companies_id"), "companies", ["id"], unique=False)

    # contacts table
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contacts_email"), "contacts", ["email"], unique=False)
    op.create_index(op.f("ix_contacts_id"), "contacts", ["id"], unique=False)

    # agents table
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.Enum("lead_sourcing", "research", "outreach", "follow_up", "qualification", "reporting", name="agentrole"), nullable=False),
        sa.Column("status", sa.Enum("active", "paused", "stopped", name="agentstatus"), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agents_id"), "agents", ["id"], unique=False)

    # leads table
    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.Enum("linkedin", "email", "web", "phone", "cold_outreach", "referral", "other", name="leadsource"), nullable=True),
        sa.Column("stage", sa.Enum("new", "contacted", "qualified", "proposal", "negotiation", "won", "lost", name="leadstage"), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("assigned_agent_id", sa.Integer(), nullable=True),
        sa.Column("snooze_until", sa.DateTime(), nullable=True),
        sa.Column("last_contacted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["assigned_agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_leads_id"), "leads", ["id"], unique=False)

    # deals table
    op.create_table(
        "deals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("stage", sa.Enum("lead", "qualified", "proposal", "negotiation", "won", "lost", name="dealstage"), nullable=True),
        sa.Column("expected_close_date", sa.DateTime(), nullable=True),
        sa.Column("actual_close_date", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_deals_id"), "deals", ["id"], unique=False)

    # sequences table
    op.create_table(
        "sequences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("steps", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sequences_id"), "sequences", ["id"], unique=False)

    # sequence_enrollments table
    op.create_table(
        "sequence_enrollments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("sequence_id", sa.Integer(), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("enrolled_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("last_sent_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["sequence_id"], ["sequences.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sequence_enrollments_id"), "sequence_enrollments", ["id"], unique=False)

    # activities table
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("deal_id", sa.Integer(), nullable=True),
        sa.Column("agent_id", sa.Integer(), nullable=True),
        sa.Column("type", sa.Enum("email_sent", "email_opened", "email_replied", "linkedin_message", "linkedin_connection", "call_made", "call_received", "note_added", "meeting_scheduled", "stage_changed", "agent_action", name="activitytype"), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_activities_id"), "activities", ["id"], unique=False)

    # audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("activities")
    op.drop_table("sequence_enrollments")
    op.drop_table("sequences")
    op.drop_table("deals")
    op.drop_table("leads")
    op.drop_table("agents")
    op.drop_table("contacts")
    op.drop_table("companies")
