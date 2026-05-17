"""
RFQ Service
Automated RFQ generation, processing, and tracking.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from app.prisma import prisma

logger = logging.getLogger(__name__)


class RFQService:
    def __init__(self):
        pass

    async def create_rfq_from_lead(
        self,
        lead_id: int,
        deal_name: str | None = None,
        deal_value: float = 0.0,
        expected_close_days: int = 30,
    ) -> dict[str, Any] | None:
        """
        Create an RFQ (deal) from a lead.
        Automates the conversion from lead to deal.
        """
        lead = await prisma.lead.find_unique(
            where={"id": lead_id},
            include={"contact": True},
        )
        if not lead:
            logger.warning(f"Lead not found for RFQ: {lead_id}")
            return None

        contact = lead.contact
        if not contact:
            logger.warning(f"Contact not found for lead: {lead_id}")
            return None

        expected_close_date = datetime.utcnow() + timedelta(days=expected_close_days)

        # Build email-based deal name
        email_username = contact.email.split('@')[0] if contact.email else "unknown"
        deal_name_value = deal_name or f"RFQ-{lead_id}-{email_username}"

        deal = await prisma.deal.create(
            data={
                "contact_id": contact.id,
                "company_id": contact.company_id,
                "name": deal_name_value,
                "value": deal_value,
                "stage": "LEAD",
                "expected_close_date": expected_close_date,
            }
        )

        activity_meta = json.dumps({
            "action": "rfq_generated",
            "deal_id": deal.id,
            "deal_value": deal_value,
        })

        await prisma.activity.create(
            data={
                "lead_id": lead_id,
                "contact_id": contact.id,
                "deal_id": deal.id,
                "type": "AGENT_ACTION",
                "content": f"RFQ generated: {deal.name}",
                "activity_meta": activity_meta,
            }
        )

        await prisma.auditlog.create(
            data={
                "action": "rfq_generated",
                "entity_type": "deal",
                "entity_id": deal.id,
                "details": json.dumps({
                    "lead_id": lead_id,
                    "contact_email": contact.email,
                    "deal_value": deal_value,
                    "expected_close_date": expected_close_date.isoformat(),
                }),
            }
        )

        logger.info(f"RFQ created: deal_id={deal.id}, lead_id={lead_id}")
        return {
            "status": "created",
            "deal_id": deal.id,
            "lead_id": lead_id,
            "deal_value": deal_value,
        }

    async def update_rfq_value(self, deal_id: int, new_value: float) -> bool:
        """
        Update RFQ deal value.
        """
        deal = await prisma.deal.find_unique(where={"id": deal_id})
        if not deal:
            return False

        old_value = deal.value
        await prisma.deal.update(
            where={"id": deal_id},
            data={"value": new_value},
        )

        await prisma.auditlog.create(
            data={
                "action": "rfq_value_updated",
                "entity_type": "deal",
                "entity_id": deal_id,
                "details": json.dumps({
                    "old_value": old_value,
                    "new_value": new_value,
                }),
            }
        )

        logger.info(f"RFQ value updated: deal_id={deal_id}, {old_value} -> {new_value}")
        return True

    async def advance_rfq_stage(self, deal_id: int, target_stage: str) -> bool:
        """
        Advance RFQ to next pipeline stage.
        """
        deal = await prisma.deal.find_unique(where={"id": deal_id})
        if not deal:
            return False

        old_stage = deal.stage
        new_stage_value = target_stage.value if hasattr(target_stage, 'value') else str(target_stage)

        update_data: dict = {"stage": new_stage_value}

        if new_stage_value == "WON" or new_stage_value == "LOST":
            update_data["actual_close_date"] = datetime.utcnow()

        await prisma.deal.update(where={"id": deal_id}, data=update_data)

        activity_meta = json.dumps({
            "old_stage": old_stage.value if hasattr(old_stage, 'value') else str(old_stage),
            "new_stage": new_stage_value,
        })

        await prisma.activity.create(
            data={
                "deal_id": deal_id,
                "contact_id": deal.contact_id,
                "type": "STAGE_CHANGED",
                "content": f"RFQ stage changed: {old_stage} -> {target_stage}",
                "activity_meta": activity_meta,
            }
        )

        await prisma.auditlog.create(
            data={
                "action": "rfq_stage_advanced",
                "entity_type": "deal",
                "entity_id": deal_id,
                "details": json.dumps({
                    "old_stage": old_stage.value if hasattr(old_stage, 'value') else str(old_stage),
                    "new_stage": new_stage_value,
                }),
            }
        )

        logger.info(f"RFQ stage advanced: deal_id={deal_id}, {old_stage} -> {target_stage}")
        return True

    async def get_rfq_summary(self, deal_id: int) -> dict | None:
        """
        Get summary of RFQ including related activities.
        """
        deal = await prisma.deal.find_unique(
            where={"id": deal_id},
            include={"contact": True, "company": True},
        )
        if not deal:
            return None

        activities = await prisma.activity.find_many(
            where={"deal_id": deal_id},
            order={"created_at": "desc"},
            take=20,
        )

        def parse_status(s):
            return s.value if hasattr(s, 'value') else str(s) if s else None

        contact_name = None
        contact_email = None
        if deal.contact:
            contact_name = f"{deal.contact.first_name or ''} {deal.contact.last_name or ''}".strip()
            contact_email = deal.contact.email

        company_name = deal.company.name if deal.company else None

        return {
            "deal_id": deal.id,
            "name": deal.name,
            "value": deal.value,
            "stage": parse_status(deal.stage),
            "contact": {
                "email": contact_email,
                "name": contact_name,
            },
            "company": {
                "name": company_name,
            } if company_name else None,
            "expected_close_date": deal.expected_close_date.isoformat() if deal.expected_close_date else None,
            "actual_close_date": deal.actual_close_date.isoformat() if deal.actual_close_date else None,
            "activity_count": len(activities),
            "recent_activities": [
                {
                    "id": a.id,
                    "type": a.type,
                    "content": a.content,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in activities
            ],
        }


async def get_rfq_service() -> RFQService:
    return RFQService()
