"""
Agentic CRM - Database Models
"""
import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.db.database import Base


class AgentRole(enum.StrEnum):
    LEAD_SOURCING = "lead_sourcing"
    RESEARCH = "research"
    OUTREACH = "outreach"
    FOLLOW_UP = "follow_up"
    QUALIFICATION = "qualification"
    REPORTING = "reporting"


class AgentStatus(enum.StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class LeadSource(enum.StrEnum):
    LINKEDIN = "linkedin"
    EMAIL = "email"
    WEB = "web"
    PHONE = "phone"
    COLD_OUTREACH = "cold_outreach"
    REFERRAL = "referral"
    OTHER = "other"


class LeadStage(enum.StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class DealStage(enum.StrEnum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class ActivityType(enum.StrEnum):
    EMAIL_SENT = "email_sent"
    EMAIL_OPENED = "email_opened"
    EMAIL_REPLIED = "email_replied"
    LINKEDIN_MESSAGE = "linkedin_message"
    LINKEDIN_CONNECTION = "linkedin_connection"
    CALL_MADE = "call_made"
    CALL_RECEIVED = "call_received"
    NOTE_ADDED = "note_added"
    MEETING_SCHEDULED = "meeting_scheduled"
    STAGE_CHANGED = "stage_changed"
    AGENT_ACTION = "agent_action"


# ─────────────────────────────────────────────────────────────────────────────
# Core Entities
# ─────────────────────────────────────────────────────────────────────────────

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), index=True, nullable=True)
    industry = Column(String(100), nullable=True)
    size = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    extra_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contacts = relationship("Contact", back_populates="company")
    deals = relationship("Deal", back_populates="company")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), index=True, nullable=True)
    phone = Column(String(50), nullable=True)
    title = Column(String(200), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    extra_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="contacts")
    leads = relationship("Lead", back_populates="contact")
    deals = relationship("Deal", back_populates="contact")
    activities = relationship("Activity", back_populates="contact")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    source = Column(SQLEnum(LeadSource), default=LeadSource.OTHER)
    stage = Column(SQLEnum(LeadStage), default=LeadStage.NEW)
    score = Column(Integer, default=0)
    tags = Column(JSON, default=[])
    notes = Column(Text, nullable=True)
    assigned_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    snooze_until = Column(DateTime, nullable=True)
    last_contacted_at = Column(DateTime, nullable=True)
    utm_source = Column(String(255), nullable=True)
    utm_medium = Column(String(255), nullable=True)
    utm_campaign = Column(String(255), nullable=True)
    utm_term = Column(String(255), nullable=True)
    utm_content = Column(String(255), nullable=True)
    hubspot_contact_id = Column(String(255), nullable=True)
    ga_client_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contact = relationship("Contact", back_populates="leads")
    assigned_agent = relationship("Agent", back_populates="assigned_leads")
    activities = relationship("Activity", back_populates="lead")
    sequence_enrollments = relationship("SequenceEnrollment", back_populates="lead")


class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    name = Column(String(255), nullable=False)
    value = Column(Float, default=0.0)
    stage = Column(SQLEnum(DealStage), default=DealStage.LEAD)
    expected_close_date = Column(DateTime, nullable=True)
    actual_close_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contact = relationship("Contact", back_populates="deals")
    company = relationship("Company", back_populates="deals")
    activities = relationship("Activity", back_populates="deal")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    role = Column(SQLEnum(AgentRole), nullable=False)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.PAUSED)
    config = Column(JSON, default={})
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assigned_leads = relationship("Lead", back_populates="assigned_agent")
    activities = relationship("Activity", back_populates="agent")
    audit_logs = relationship("AuditLog", back_populates="agent")


class Sequence(Base):
    __tablename__ = "sequences"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    steps = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    enrollments = relationship("SequenceEnrollment", back_populates="sequence")


class SequenceEnrollment(Base):
    __tablename__ = "sequence_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    sequence_id = Column(Integer, ForeignKey("sequences.id"), nullable=False)
    current_step = Column(Integer, default=0)
    status = Column(String(50), default="active")
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    last_sent_at = Column(DateTime, nullable=True)

    lead = relationship("Lead", back_populates="sequence_enrollments")
    sequence = relationship("Sequence", back_populates="enrollments")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    type = Column(SQLEnum(ActivityType), nullable=False)
    content = Column(Text, nullable=True)
    activity_meta = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="activities")
    contact = relationship("Contact", back_populates="activities")
    deal = relationship("Deal", back_populates="activities")
    agent = relationship("Agent", back_populates="activities")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    action = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(Integer, nullable=True)
    details = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="audit_logs")
