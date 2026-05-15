"""
RFQ Service
Automated RFQ generation, processing, and tracking.
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.models.models import Activity, ActivityType, AuditLog, Company, Contact, Deal, DealStage, Lead

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
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Lead).where(Lead.id == lead_id).options(selectinload(Lead.contact))
            )
            lead = result.scalar_one_or_none()
            if not lead:
                logger.warning(f"Lead not found for RFQ: {lead_id}")
                return None

            contact = lead.contact
            if not contact:
                logger.warning(f"Contact not found for lead: {lead_id}")
                return None

            expected_close_date = datetime.utcnow() + timedelta(days=expected_close_days)

            deal = Deal(
                contact_id=contact.id,
                company_id=contact.company_id,
                name=deal_name or f"RFQ-{lead_id}-{contact.email.split('@')[0]}",
                value=deal_value,
                stage=DealStage.LEAD,
                expected_close_date=expected_close_date,
            )
            db.add(deal)
            await db.flush()

            activity = Activity(
                lead_id=lead_id,
                contact_id=contact.id,
                deal_id=deal.id,
                type=ActivityType.AGENT_ACTION,
                content=f"RFQ generated: {deal.name}",
                activity_meta={
                    "action": "rfq_generated",
                    "deal_id": deal.id,
                    "deal_value": deal_value,
                },
            )
            db.add(activity)

            audit = AuditLog(
                action="rfq_generated",
                entity_type="deal",
                entity_id=deal.id,
                details={
                    "lead_id": lead_id,
                    "contact_email": contact.email,
                    "deal_value": deal_value,
                    "expected_close_date": expected_close_date.isoformat(),
                },
            )
            db.add(audit)
            await db.commit()

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
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Deal).where(Deal.id == deal_id))
            deal = result.scalar_one_or_none()
            if not deal:
                return False

            old_value = deal.value
            deal.value = new_value
            await db.commit()

            audit = AuditLog(
                action="rfq_value_updated",
                entity_type="deal",
                entity_id=deal_id,
                details={
                    "old_value": old_value,
                    "new_value": new_value,
                },
            )
            db.add(audit)
            await db.commit()

            logger.info(f"RFQ value updated: deal_id={deal_id}, {old_value} -> {new_value}")
            return True

    async def advance_rfq_stage(self, deal_id: int, target_stage: DealStage | str) -> bool:
        """
        Advance RFQ to next pipeline stage.
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Deal).where(Deal.id == deal_id))
            deal = result.scalar_one_or_none()
            if not deal:
                return False

            old_stage = deal.stage
            deal.stage = DealStage(target_stage) if isinstance(target_stage, str) else target_stage

            if deal.stage == DealStage.WON:
                deal.actual_close_date = datetime.utcnow()
            elif deal.stage == DealStage.LOST:
                deal.actual_close_date = datetime.utcnow()

            activity = Activity(
                deal_id=deal_id,
                contact_id=deal.contact_id,
                type=ActivityType.STAGE_CHANGED,
                content=f"RFQ stage changed: {old_stage.value if hasattr(old_stage, 'value') else old_stage} -> {target_stage}",
                activity_meta={
                    "old_stage": old_stage.value if hasattr(old_stage, 'value') else str(old_stage),
                    "new_stage": target_stage.value if hasattr(target_stage, 'value') else str(target_stage),
                },
            )
            db.add(activity)

            audit = AuditLog(
                action="rfq_stage_advanced",
                entity_type="deal",
                entity_id=deal_id,
                details={
                    "old_stage": old_stage.value if hasattr(old_stage, 'value') else str(old_stage),
                    "new_stage": target_stage.value if hasattr(target_stage, 'value') else str(target_stage),
                },
            )
            db.add(audit)
            await db.commit()

            logger.info(f"RFQ stage advanced: deal_id={deal_id}, {old_stage} -> {target_stage}")
            return True

    async def get_rfq_summary(self, deal_id: int) -> dict | None:
        """
        Get summary of RFQ including related activities.
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Deal)
                .where(Deal.id == deal_id)
                .options(selectinload(Deal.contact), selectinload(Deal.company))
            )
            deal = result.scalar_one_or_none()
            if not deal:
                return None

            activities_result = await db.execute(
                select(Activity)
                .where(Activity.deal_id == deal_id)
                .order_by(Activity.created_at.desc())
                .limit(20)
            )
            activities = activities_result.scalars().all()

            return {
                "deal_id": deal.id,
                "name": deal.name,
                "value": deal.value,
                "stage": deal.stage.value if hasattr(deal.stage, "value") else deal.stage,
                "contact": {
                    "email": deal.contact.email if deal.contact else None,
                    "name": f"{deal.contact.first_name} {deal.contact.last_name}" if deal.contact else None,
                },
                "company": {
                    "name": deal.company.name if deal.company else None,
                } if deal.company else None,
                "expected_close_date": deal.expected_close_date.isoformat() if deal.expected_close_date else None,
                "actual_close_date": deal.actual_close_date.isoformat() if deal.actual_close_date else None,
                "activity_count": len(activities),
                "recent_activities": [
                    {
                        "id": a.id,
                        "type": a.type.value if hasattr(a.type, "value") else a.type,
                        "content": a.content,
                        "created_at": a.created_at.isoformat() if a.created_at else None,
                    }
                    for a in activities
                ],
            }


async def get_rfq_service() -> RFQService:
    return RFQService()