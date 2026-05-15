"""
Procurement Service
Handles procurement request lifecycle, quote management, and purchase orders.
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import AsyncSessionLocal
from app.models.models import (
    AuditLog,
    Invoice,
    InvoiceStatus,
    ProcurementRequest,
    ProcurementStatus,
    PurchaseOrder,
    PurchaseOrderStatus,
    Quote,
    QuoteStatus,
    Shipment,
    ShipmentStatus,
)

logger = logging.getLogger(__name__)


class ProcurementService:
    def __init__(self):
        pass

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
        async with AsyncSessionLocal() as db:
            procurement = ProcurementRequest(
                title=title,
                description=description,
                category_id=category_id,
                quantity=quantity,
                target_price=target_price,
                currency=currency,
                requested_delivery_date=requested_delivery_date,
                priority=priority,
                status=ProcurementStatus.DRAFT,
                created_by=created_by,
            )
            db.add(procurement)
            await db.flush()

            audit = AuditLog(
                action="procurement_request_created",
                entity_type="procurement_request",
                entity_id=procurement.id,
                details={
                    "title": title,
                    "target_price": target_price,
                    "currency": currency,
                    "priority": priority,
                },
            )
            db.add(audit)
            await db.commit()

            logger.info(f"Procurement request created: {procurement.id}")
            return {
                "id": procurement.id,
                "title": procurement.title,
                "status": procurement.status.value if hasattr(procurement.status, "value") else procurement.status,
                "created_at": procurement.created_at.isoformat() if procurement.created_at else None,
            }

    async def submit_procurement_request(self, request_id: int) -> bool:
        """
        Submit a procurement request to receive quotes from suppliers.
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ProcurementRequest).where(ProcurementRequest.id == request_id)
            )
            procurement = result.scalar_one_or_none()
            if not procurement:
                return False

            procurement.status = ProcurementStatus.SUBMITTED
            await db.flush()

            audit = AuditLog(
                action="procurement_request_submitted",
                entity_type="procurement_request",
                entity_id=request_id,
                details={},
            )
            db.add(audit)
            await db.commit()

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
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ProcurementRequest).where(ProcurementRequest.id == procurement_request_id)
            )
            procurement = result.scalar_one_or_none()
            if not procurement:
                logger.warning(f"Procurement request not found: {procurement_request_id}")
                return None

            submitted_at = datetime.utcnow()
            expires_at = submitted_at + timedelta(days=validity_days)

            quote = Quote(
                procurement_request_id=procurement_request_id,
                supplier_id=supplier_id,
                price=price,
                currency=currency,
                lead_time_days=lead_time_days,
                validity_days=validity_days,
                notes=notes,
                status=QuoteStatus.SENT,
                submitted_at=submitted_at,
                expires_at=expires_at,
            )
            db.add(quote)
            await db.flush()

            audit = AuditLog(
                action="quote_created",
                entity_type="quote",
                entity_id=quote.id,
                details={
                    "procurement_request_id": procurement_request_id,
                    "supplier_id": supplier_id,
                    "price": price,
                    "currency": currency,
                },
            )
            db.add(audit)

            quotes_result = await db.execute(
                select(Quote).where(Quote.procurement_request_id == procurement_request_id)
            )
            quotes = quotes_result.scalars().all()
            if len(quotes) >= 1:
                procurement.status = ProcurementStatus.QUOTES_RECEIVED
                await db.flush()

            await db.commit()

            logger.info(f"Quote created: {quote.id} for procurement request: {procurement_request_id}")
            return {
                "id": quote.id,
                "price": quote.price,
                "currency": quote.currency,
                "status": quote.status.value if hasattr(quote.status, "value") else quote.status,
            }

    async def accept_quote(self, quote_id: int) -> dict[str, Any] | None:
        """
        Accept a quote and create a purchase order.
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Quote).where(Quote.id == quote_id).options(selectinload(Quote.procurement_request))
            )
            quote = result.scalar_one_or_none()
            if not quote:
                return None

            quote.status = QuoteStatus.ACCEPTED

            purchase_order = PurchaseOrder(
                procurement_request_id=quote.procurement_request_id,
                supplier_id=quote.supplier_id,
                quote_id=quote.id,
                order_number=f"PO-{quote.procurement_request_id}-{quote.supplier_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                total_amount=quote.price,
                currency=quote.currency,
                status=PurchaseOrderStatus.ISSUED,
                expected_delivery_date=datetime.utcnow() + timedelta(days=quote.lead_time_days or 30) if quote.lead_time_days else None,
            )
            db.add(purchase_order)
            await db.flush()

            procurement = quote.procurement_request
            procurement.status = ProcurementStatus.APPROVED

            audit = AuditLog(
                action="quote_accepted",
                entity_type="quote",
                entity_id=quote_id,
                details={
                    "purchase_order_id": purchase_order.id,
                    "order_number": purchase_order.order_number,
                },
            )
            db.add(audit)
            await db.commit()

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
        async with AsyncSessionLocal() as db:
            order_number = f"PO-{procurement_request_id}-{supplier_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            purchase_order = PurchaseOrder(
                procurement_request_id=procurement_request_id,
                supplier_id=supplier_id,
                order_number=order_number,
                total_amount=total_amount,
                currency=currency,
                status=PurchaseOrderStatus.ISSUED,
                expected_delivery_date=expected_delivery_date,
                shipping_address=shipping_address,
            )
            db.add(purchase_order)
            await db.flush()

            procurement_result = await db.execute(
                select(ProcurementRequest).where(ProcurementRequest.id == procurement_request_id)
            )
            procurement = procurement_result.scalar_one_or_none()
            if procurement:
                procurement.status = ProcurementStatus.IN_PRODUCTION

            audit = AuditLog(
                action="purchase_order_created",
                entity_type="purchase_order",
                entity_id=purchase_order.id,
                details={
                    "order_number": order_number,
                    "total_amount": total_amount,
                },
            )
            db.add(audit)
            await db.commit()

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
        async with AsyncSessionLocal() as db:
            shipment = Shipment(
                purchase_order_id=purchase_order_id,
                tracking_number=tracking_number,
                carrier=carrier,
                status=ShipmentStatus.PREPARING,
                estimated_delivery_date=estimated_delivery_date,
                shipping_date=datetime.utcnow(),
                shipping_address=shipping_address,
            )
            db.add(shipment)
            await db.flush()

            po_result = await db.execute(
                select(PurchaseOrder).where(PurchaseOrder.id == purchase_order_id)
            )
            purchase_order = po_result.scalar_one_or_none()
            if purchase_order:
                purchase_order.status = PurchaseOrderStatus.SHIPPED

            audit = AuditLog(
                action="shipment_created",
                entity_type="shipment",
                entity_id=shipment.id,
                details={
                    "purchase_order_id": purchase_order_id,
                    "tracking_number": tracking_number,
                },
            )
            db.add(audit)
            await db.commit()

            logger.info(f"Shipment created: {shipment.id} for PO: {purchase_order_id}")
            return {
                "id": shipment.id,
                "tracking_number": tracking_number,
                "status": shipment.status.value if hasattr(shipment.status, "value") else shipment.status,
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
        async with AsyncSessionLocal() as db:
            invoice_number = f"INV-{purchase_order_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            invoice = Invoice(
                purchase_order_id=purchase_order_id,
                invoice_number=invoice_number,
                amount=amount,
                currency=currency,
                status=InvoiceStatus.SENT,
                issue_date=datetime.utcnow(),
                due_date=due_date or (datetime.utcnow() + timedelta(days=30)),
                notes=notes,
            )
            db.add(invoice)
            await db.flush()

            audit = AuditLog(
                action="invoice_created",
                entity_type="invoice",
                entity_id=invoice.id,
                details={
                    "invoice_number": invoice_number,
                    "amount": amount,
                },
            )
            db.add(audit)
            await db.commit()

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
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
            invoice = result.scalar_one_or_none()
            if not invoice:
                return False

            invoice.status = InvoiceStatus.PAID
            invoice.paid_date = datetime.utcnow()
            await db.flush()

            audit = AuditLog(
                action="invoice_paid",
                entity_type="invoice",
                entity_id=invoice_id,
                details={},
            )
            db.add(audit)
            await db.commit()

            logger.info(f"Invoice marked as paid: {invoice_id}")
            return True

    async def get_procurement_summary(self, request_id: int) -> dict | None:
        """
        Get comprehensive summary of a procurement request with all related data.
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ProcurementRequest)
                .where(ProcurementRequest.id == request_id)
                .options(
                    selectinload(ProcurementRequest.quotes),
                    selectinload(ProcurementRequest.purchase_orders),
                )
            )
            procurement = result.scalar_one_or_none()
            if not procurement:
                return None

            return {
                "id": procurement.id,
                "title": procurement.title,
                "description": procurement.description,
                "status": procurement.status.value if hasattr(procurement.status, "value") else procurement.status,
                "priority": procurement.priority,
                "target_price": procurement.target_price,
                "currency": procurement.currency,
                "quantity": procurement.quantity,
                "requested_delivery_date": procurement.requested_delivery_date.isoformat() if procurement.requested_delivery_date else None,
                "quotes_count": len(procurement.quotes),
                "purchase_orders_count": len(procurement.purchase_orders),
                "quotes": [
                    {
                        "id": q.id,
                        "price": q.price,
                        "status": q.status.value if hasattr(q.status, "value") else q.status,
                        "submitted_at": q.submitted_at.isoformat() if q.submitted_at else None,
                    }
                    for q in procurement.quotes
                ],
                "purchase_orders": [
                    {
                        "id": po.id,
                        "order_number": po.order_number,
                        "total_amount": po.total_amount,
                        "status": po.status.value if hasattr(po.status, "value") else po.status,
                    }
                    for po in procurement.purchase_orders
                ],
            }


async def get_procurement_service() -> ProcurementService:
    return ProcurementService()