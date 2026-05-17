"""
Procurement Service
Handles procurement request lifecycle, quote management, and purchase orders.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from app.prisma import prisma

logger = logging.getLogger(__name__)


class ProcurementService:
    def __init__(self):
        pass

    async def _parse_status(self, status_value, default=None):
        """Parse a status enum/value for JSON serialization."""
        if hasattr(status_value, 'value'):
            return status_value.value
        return str(status_value) if status_value else default

    async def create_procurement_request(
        self,
        title: str,
        description: str | None = None,
        category_id: int | None = None,
        quantity: str | None = None,
        target_price: float | None = None,
        currency: str = "USD",
        requested_delivery_date: datetime | None = None,
        priority: str = "medium",
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new procurement request.
        """
        procurement = await prisma.procurementrequest.create(
            data={
                "title": title,
                "description": description,
                "category_id": category_id,
                "quantity": quantity,
                "target_price": target_price,
                "currency": currency,
                "requested_delivery_date": requested_delivery_date,
                "priority": priority,
                "status": "DRAFT",
                "created_by": created_by,
            }
        )

        await prisma.auditlog.create(
            data={
                "action": "procurement_request_created",
                "entity_type": "procurement_request",
                "entity_id": procurement.id,
                "details": json.dumps({
                    "title": title,
                    "target_price": target_price,
                    "currency": currency,
                    "priority": priority,
                }),
            }
        )

        logger.info(f"Procurement request created: {procurement.id}")
        return {
            "id": procurement.id,
            "title": procurement.title,
            "status": procurement.status,
            "created_at": procurement.created_at.isoformat() if procurement.created_at else None,
        }

    async def submit_procurement_request(self, request_id: int) -> bool:
        """
        Submit a procurement request to receive quotes from suppliers.
        """
        procurement = await prisma.procurementrequest.update(
            where={"id": request_id},
            data={"status": "SUBMITTED"},
        )
        if not procurement:
            return False

        await prisma.auditlog.create(
            data={
                "action": "procurement_request_submitted",
                "entity_type": "procurement_request",
                "entity_id": request_id,
                "details": "{}",
            }
        )

        logger.info(f"Procurement request submitted: {request_id}")
        return True

    async def create_quote(
        self,
        procurement_request_id: int,
        supplier_id: int,
        price: float,
        currency: str = "USD",
        lead_time_days: int | None = None,
        validity_days: int = 30,
        notes: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Create a quote for a procurement request from a supplier.
        """
        procurement = await prisma.procurementrequest.find_unique(
            where={"id": procurement_request_id}
        )
        if not procurement:
            logger.warning(f"Procurement request not found: {procurement_request_id}")
            return None

        submitted_at = datetime.utcnow()
        expires_at = submitted_at + timedelta(days=validity_days)

        quote = await prisma.quote.create(
            data={
                "procurement_request_id": procurement_request_id,
                "supplier_id": supplier_id,
                "price": price,
                "currency": currency,
                "lead_time_days": lead_time_days,
                "validity_days": validity_days,
                "notes": notes,
                "status": "SENT",
                "submitted_at": submitted_at,
                "expires_at": expires_at,
            }
        )

        await prisma.auditlog.create(
            data={
                "action": "quote_created",
                "entity_type": "quote",
                "entity_id": quote.id,
                "details": json.dumps({
                    "procurement_request_id": procurement_request_id,
                    "supplier_id": supplier_id,
                    "price": price,
                    "currency": currency,
                }),
            }
        )

        # Count existing quotes
        existing_quotes = await prisma.quote.find_many(
            where={"procurement_request_id": procurement_request_id}
        )
        if len(existing_quotes) >= 1:
            await prisma.procurementrequest.update(
                where={"id": procurement_request_id},
                data={"status": "QUOTES_RECEIVED"},
            )

        logger.info(f"Quote created: {quote.id} for procurement request: {procurement_request_id}")
        return {
            "id": quote.id,
            "price": quote.price,
            "currency": quote.currency,
            "status": quote.status,
        }

    async def accept_quote(self, quote_id: int) -> dict[str, Any] | None:
        """
        Accept a quote and create a purchase order.
        """
        quote = await prisma.quote.find_unique(
            where={"id": quote_id},
            include={"procurement_request": True},
        )
        if not quote:
            return None

        await prisma.quote.update(
            where={"id": quote_id},
            data={"status": "ACCEPTED"},
        )

        expected_delivery = None
        if quote.lead_time_days:
            expected_delivery = datetime.utcnow() + timedelta(days=quote.lead_time_days)

        purchase_order = await prisma.purchaseorder.create(
            data={
                "procurement_request_id": quote.procurement_request_id,
                "supplier_id": quote.supplier_id,
                "quote_id": quote.id,
                "order_number": f"PO-{quote.procurement_request_id}-{quote.supplier_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "total_amount": quote.price,
                "currency": quote.currency,
                "status": "ISSUED",
                "expected_delivery_date": expected_delivery,
            }
        )

        if quote.procurement_request:
            await prisma.procurementrequest.update(
                where={"id": quote.procurement_request_id},
                data={"status": "APPROVED"},
            )

        await prisma.auditlog.create(
            data={
                "action": "quote_accepted",
                "entity_type": "quote",
                "entity_id": quote_id,
                "details": json.dumps({
                    "purchase_order_id": purchase_order.id,
                    "order_number": purchase_order.order_number,
                }),
            }
        )

        logger.info(f"Quote {quote_id} accepted, PO created: {purchase_order.id}")
        return {
            "purchase_order_id": purchase_order.id,
            "order_number": purchase_order.order_number,
            "total_amount": purchase_order.total_amount,
        }

    async def create_purchase_order(
        self,
        procurement_request_id: int,
        supplier_id: int,
        total_amount: float,
        currency: str = "USD",
        expected_delivery_date: datetime | None = None,
        shipping_address: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a purchase order directly (without quote).
        """
        order_number = f"PO-{procurement_request_id}-{supplier_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        purchase_order = await prisma.purchaseorder.create(
            data={
                "procurement_request_id": procurement_request_id,
                "supplier_id": supplier_id,
                "order_number": order_number,
                "total_amount": total_amount,
                "currency": currency,
                "status": "ISSUED",
                "expected_delivery_date": expected_delivery_date,
                "shipping_address": shipping_address,
            }
        )

        procurement = await prisma.procurementrequest.find_unique(
            where={"id": procurement_request_id}
        )
        if procurement:
            await prisma.procurementrequest.update(
                where={"id": procurement_request_id},
                data={"status": "IN_PRODUCTION"},
            )

        await prisma.auditlog.create(
            data={
                "action": "purchase_order_created",
                "entity_type": "purchase_order",
                "entity_id": purchase_order.id,
                "details": json.dumps({
                    "order_number": order_number,
                    "total_amount": total_amount,
                }),
            }
        )

        logger.info(f"Purchase order created: {purchase_order.id}")
        return {
            "id": purchase_order.id,
            "order_number": order_number,
            "total_amount": total_amount,
        }

    async def create_shipment(
        self,
        purchase_order_id: int,
        tracking_number: str | None = None,
        carrier: str | None = None,
        estimated_delivery_date: datetime | None = None,
        shipping_address: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a shipment for a purchase order.
        """
        shipment = await prisma.shipment.create(
            data={
                "purchase_order_id": purchase_order_id,
                "tracking_number": tracking_number,
                "carrier": carrier,
                "status": "PREPARING",
                "estimated_delivery_date": estimated_delivery_date,
                "shipping_date": datetime.utcnow(),
                "shipping_address": shipping_address,
            }
        )

        await prisma.purchaseorder.update(
            where={"id": purchase_order_id},
            data={"status": "SHIPPED"},
        )

        await prisma.auditlog.create(
            data={
                "action": "shipment_created",
                "entity_type": "shipment",
                "entity_id": shipment.id,
                "details": json.dumps({
                    "purchase_order_id": purchase_order_id,
                    "tracking_number": tracking_number,
                }),
            }
        )

        logger.info(f"Shipment created: {shipment.id} for PO: {purchase_order_id}")
        return {
            "id": shipment.id,
            "tracking_number": tracking_number,
            "status": shipment.status,
        }

    async def create_invoice(
        self,
        purchase_order_id: int,
        amount: float,
        currency: str = "USD",
        due_date: datetime | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """
        Create an invoice for a purchase order.
        """
        invoice_number = f"INV-{purchase_order_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        invoice = await prisma.invoice.create(
            data={
                "purchase_order_id": purchase_order_id,
                "invoice_number": invoice_number,
                "amount": amount,
                "currency": currency,
                "status": "SENT",
                "issue_date": datetime.utcnow(),
                "due_date": due_date or (datetime.utcnow() + timedelta(days=30)),
                "notes": notes,
            }
        )

        await prisma.auditlog.create(
            data={
                "action": "invoice_created",
                "entity_type": "invoice",
                "entity_id": invoice.id,
                "details": json.dumps({
                    "invoice_number": invoice_number,
                    "amount": amount,
                }),
            }
        )

        logger.info(f"Invoice created: {invoice.id}")
        return {
            "id": invoice.id,
            "invoice_number": invoice_number,
            "amount": amount,
        }

    async def mark_invoice_paid(self, invoice_id: int) -> bool:
        """
        Mark an invoice as paid.
        """
        invoice = await prisma.invoice.find_unique(where={"id": invoice_id})
        if not invoice:
            return False

        await prisma.invoice.update(
            where={"id": invoice_id},
            data={
                "status": "PAID",
                "paid_date": datetime.utcnow(),
            },
        )

        await prisma.auditlog.create(
            data={
                "action": "invoice_paid",
                "entity_type": "invoice",
                "entity_id": invoice_id,
                "details": "{}",
            }
        )

        logger.info(f"Invoice marked as paid: {invoice_id}")
        return True

    async def get_procurement_summary(self, request_id: int) -> dict | None:
        """
        Get comprehensive summary of a procurement request with all related data.
        """
        procurement = await prisma.procurementrequest.find_unique(
            where={"id": request_id},
            include={
                "quotes": True,
                "purchase_orders": True,
            },
        )
        if not procurement:
            return None

        def parse_status(s):
            return s.value if hasattr(s, 'value') else str(s) if s else None

        return {
            "id": procurement.id,
            "title": procurement.title,
            "description": procurement.description,
            "status": parse_status(procurement.status),
            "priority": procurement.priority,
            "target_price": procurement.target_price,
            "currency": procurement.currency,
            "quantity": procurement.quantity,
            "requested_delivery_date": procurement.requested_delivery_date.isoformat() if procurement.requested_delivery_date else None,
            "quotes_count": len(procurement.quotes) if procurement.quotes else 0,
            "purchase_orders_count": len(procurement.purchase_orders) if procurement.purchase_orders else 0,
            "quotes": [
                {
                    "id": q.id,
                    "price": q.price,
                    "status": parse_status(q.status),
                    "submitted_at": q.submitted_at.isoformat() if q.submitted_at else None,
                }
                for q in (procurement.quotes or [])
            ],
            "purchase_orders": [
                {
                    "id": po.id,
                    "order_number": po.order_number,
                    "total_amount": po.total_amount,
                    "status": parse_status(po.status),
                }
                for po in (procurement.purchase_orders or [])
            ],
        }


async def get_procurement_service() -> ProcurementService:
    return ProcurementService()