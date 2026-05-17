"""
String-based enums used in Pydantic schemas.
Mirrors the string values stored in SQLite via Prisma.
Prisma stores these as plain strings (no native enum support in SQLite).
"""

from enum import StrEnum


class LeadSource(StrEnum):
    LINKEDIN = "linkedin"
    EMAIL = "email"
    WEB = "web"
    PHONE = "phone"
    COLD_OUTREACH = "cold_outreach"
    REFERRAL = "referral"
    OTHER = "other"


class LeadStage(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class DealStage(StrEnum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class AgentRole(StrEnum):
    LEAD_SOURCING = "lead_sourcing"
    RESEARCH = "research"
    OUTREACH = "outreach"
    FOLLOW_UP = "follow_up"
    QUALIFICATION = "qualification"
    REPORTING = "reporting"


class AgentStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class ActivityType(StrEnum):
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


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class SupplierStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class ProcurementStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    QUOTES_RECEIVED = "quotes_received"
    APPROVED = "approved"
    ORDERED = "ordered"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class QuoteStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"



class ShipmentStatus(StrEnum):
    PREPARING = "preparing"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
