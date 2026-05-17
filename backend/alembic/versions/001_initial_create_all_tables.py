"""Initial migration - create all tables

Revision ID: 001
Revises:
Create Date: 2026-05-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # User table
    op.create_table('User', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'email', sa.String(), nullable=False, unique=True)
    op.create_column(None, 'passwordHash', sa.String(), nullable=False)
    op.create_column(None, 'fullName', sa.String(), nullable=True)
    op.create_column(None, 'role', sa.String(), nullable=False, server_default='user')
    op.create_column(None, 'isActive', sa.Boolean(), nullable=False, server_default='true')
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'updatedAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')

    # Company table
    op.create_table('Company', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'name', sa.String(), nullable=False)
    op.create_column(None, 'domain', sa.String(), nullable=True)
    op.create_column(None, 'industry', sa.String(), nullable=True)
    op.create_column(None, 'size', sa.String(), nullable=True)
    op.create_column(None, 'linkedinUrl', sa.String(), nullable=True)
    op.create_column(None, 'extraData', sa.String(), nullable=True)
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'updatedAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')

    # Contact table
    op.create_table('Contact', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'companyId', sa.Integer(), nullable=True)
    op.create_column(None, 'firstName', sa.String(), nullable=True)
    op.create_column(None, 'lastName', sa.String(), nullable=True)
    op.create_column(None, 'email', sa.String(), nullable=True)
    op.create_column(None, 'phone', sa.String(), nullable=True)
    op.create_column(None, 'title', sa.String(), nullable=True)
    op.create_column(None, 'linkedinUrl', sa.String(), nullable=True)
    op.create_column(None, 'extraData', sa.String(), nullable=True)
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'updatedAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_foreign_key(None, 'Contact', 'Company', ['companyId'], ['id'])

    # Lead table
    op.create_table('Lead', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'contactId', sa.Integer(), nullable=False)
    op.create_column(None, 'source', sa.String(), nullable=False, server_default='other')
    op.create_column(None, 'stage', sa.String(), nullable=False, server_default='new')
    op.create_column(None, 'score', sa.Integer(), nullable=False, server_default='0')
    op.create_column(None, 'tags', sa.String(), nullable=True)
    op.create_column(None, 'notes', sa.String(), nullable=True)
    op.create_column(None, 'assignedAgentId', sa.Integer(), nullable=True)
    op.create_column(None, 'snoozeUntil', sa.DateTime(), nullable=True)
    op.create_column(None, 'lastContactedAt', sa.DateTime(), nullable=True)
    op.create_column(None, 'utmSource', sa.String(), nullable=True)
    op.create_column(None, 'utmMedium', sa.String(), nullable=True)
    op.create_column(None, 'utmCampaign', sa.String(), nullable=True)
    op.create_column(None, 'utmTerm', sa.String(), nullable=True)
    op.create_column(None, 'utmContent', sa.String(), nullable=True)
    op.create_column(None, 'hubspotContactId', sa.String(), nullable=True)
    op.create_column(None, 'gaClientId', sa.String(), nullable=True)
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'updatedAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_foreign_key(None, 'Lead', 'Contact', ['contactId'], ['id'])
    op.create_foreign_key(None, 'Lead', 'Agent', ['assignedAgentId'], ['id'])

    # Deal table
    op.create_table('Deal', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'contactId', sa.Integer(), nullable=False)
    op.create_column(None, 'companyId', sa.Integer(), nullable=True)
    op.create_column(None, 'name', sa.String(), nullable=False)
    op.create_column(None, 'value', sa.Float(), nullable=False, server_default='0')
    op.create_column(None, 'stage', sa.String(), nullable=False, server_default='lead')
    op.create_column(None, 'expectedCloseDate', sa.DateTime(), nullable=True)
    op.create_column(None, 'actualCloseDate', sa.DateTime(), nullable=True)
    op.create_column(None, 'notes', sa.String(), nullable=True)
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'updatedAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_foreign_key(None, 'Deal', 'Contact', ['contactId'], ['id'])
    op.create_foreign_key(None, 'Deal', 'Company', ['companyId'], ['id'])

    # Agent table
    op.create_table('Agent', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'name', sa.String(), nullable=False)
    op.create_column(None, 'role', sa.String(), nullable=False)
    op.create_column(None, 'status', sa.String(), nullable=False, server_default='paused')
    op.create_column(None, 'config', sa.String(), nullable=True)
    op.create_column(None, 'description', sa.String(), nullable=True)
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'updatedAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')

    # Sequence table
    op.create_table('Sequence', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'name', sa.String(), nullable=False)
    op.create_column(None, 'description', sa.String(), nullable=True)
    op.create_column(None, 'steps', sa.String(), nullable=True)
    op.create_column(None, 'isActive', sa.Boolean(), nullable=False, server_default='true')
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'updatedAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')

    # SequenceEnrollment table
    op.create_table('SequenceEnrollment', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'leadId', sa.Integer(), nullable=False)
    op.create_column(None, 'sequenceId', sa.Integer(), nullable=False)
    op.create_column(None, 'currentStep', sa.Integer(), nullable=False, server_default='0')
    op.create_column(None, 'status', sa.String(), nullable=False, server_default='active')
    op.create_column(None, 'enrolledAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'completedAt', sa.DateTime(), nullable=True)
    op.create_column(None, 'lastSentAt', sa.DateTime(), nullable=True)
    op.create_foreign_key(None, 'SequenceEnrollment', 'Lead', ['leadId'], ['id'])
    op.create_foreign_key(None, 'SequenceEnrollment', 'Sequence', ['sequenceId'], ['id'])

    # Activity table
    op.create_table('Activity', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'leadId', sa.Integer(), nullable=True)
    op.create_column(None, 'contactId', sa.Integer(), nullable=True)
    op.create_column(None, 'dealId', sa.Integer(), nullable=True)
    op.create_column(None, 'agentId', sa.Integer(), nullable=True)
    op.create_column(None, 'type', sa.String(), nullable=False)
    op.create_column(None, 'content', sa.String(), nullable=True)
    op.create_column(None, 'activityMeta', sa.String(), nullable=True)
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_foreign_key(None, 'Activity', 'Lead', ['leadId'], ['id'])
    op.create_foreign_key(None, 'Activity', 'Contact', ['contactId'], ['id'])
    op.create_foreign_key(None, 'Activity', 'Deal', ['dealId'], ['id'])
    op.create_foreign_key(None, 'Activity', 'Agent', ['agentId'], ['id'])

    # AuditLog table
    op.create_table('AuditLog', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'action', sa.String(), nullable=False)
    op.create_column(None, 'entityType', sa.String(), nullable=True)
    op.create_column(None, 'entityId', sa.Integer(), nullable=True)
    op.create_column(None, 'details', sa.String(), nullable=True)
    op.create_column(None, 'agentId', sa.Integer(), nullable=True)
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_foreign_key(None, 'AuditLog', 'Agent', ['agentId'], ['id'])

    # ProductCategory table
    op.create_table('ProductCategory', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'name', sa.String(), nullable=False)
    op.create_column(None, 'description', sa.String(), nullable=True)
    op.create_column(None, 'parentId', sa.Integer(), nullable=True)
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'updatedAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_foreign_key(None, 'ProductCategory', 'ProductCategory', ['parentId'], ['id'])

    # Supplier table
    op.create_table('Supplier', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'name', sa.String(), nullable=False)
    op.create_column(None, 'contactEmail', sa.String(), nullable=True)
    op.create_column(None, 'contactPhone', sa.String(), nullable=True)
    op.create_column(None, 'website', sa.String(), nullable=True)
    op.create_column(None, 'address', sa.String(), nullable=True)
    op.create_column(None, 'country', sa.String(), nullable=True)
    op.create_column(None, 'status', sa.String(), nullable=False, server_default='pending')
    op.create_column(None, 'rating', sa.Float(), nullable=True)
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'updatedAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')

    # ProcurementRequest table
    op.create_table('ProcurementRequest', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'rfqId', sa.Integer(), nullable=True)
    op.create_column(None, 'title', sa.String(), nullable=False)
    op.create_column(None, 'description', sa.String(), nullable=True)
    op.create_column(None, 'status', sa.String(), nullable=False, server_default='draft')
    op.create_column(None, 'targetPrice', sa.Float(), nullable=True)
    op.create_column(None, 'requestedDeliveryDate', sa.DateTime(), nullable=True)
    op.create_column(None, 'categoryId', sa.Integer(), nullable=True)
    op.create_column(None, 'agentId', sa.Integer(), nullable=True)
    op.create_column(None, 'extraData', sa.String(), nullable=True)
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'updatedAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_foreign_key(None, 'ProcurementRequest', 'Agent', ['agentId'], ['id'])
    op.create_foreign_key(None, 'ProcurementRequest', 'ProductCategory', ['categoryId'], ['id'])

    # Quote table
    op.create_table('Quote', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'supplierId', sa.Integer(), nullable=True)
    op.create_column(None, 'procurementRequestId', sa.Integer(), nullable=True)
    op.create_column(None, 'price', sa.Float(), nullable=False)
    op.create_column(None, 'currency', sa.String(), nullable=False, server_default='USD')
    op.create_column(None, 'validUntil', sa.DateTime(), nullable=True)
    op.create_column(None, 'notes', sa.String(), nullable=True)
    op.create_column(None, 'status', sa.String(), nullable=False, server_default='pending')
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'updatedAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_foreign_key(None, 'Quote', 'Supplier', ['supplierId'], ['id'])
    op.create_foreign_key(None, 'Quote', 'ProcurementRequest', ['procurementRequestId'], ['id'])

    # PurchaseOrder table
    op.create_table('PurchaseOrder', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'quoteId', sa.Integer(), nullable=True)
    op.create_column(None, 'supplierId', sa.Integer(), nullable=True)
    op.create_column(None, 'status', sa.String(), nullable=False, server_default='pending')
    op.create_column(None, 'orderDate', sa.DateTime(), nullable=True)
    op.create_column(None, 'expectedDeliveryDate', sa.DateTime(), nullable=True)
    op.create_column(None, 'actualDeliveryDate', sa.DateTime(), nullable=True)
    op.create_column(None, 'totalAmount', sa.Float(), nullable=False)
    op.create_column(None, 'notes', sa.String(), nullable=True)
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'updatedAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_foreign_key(None, 'PurchaseOrder', 'Quote', ['quoteId'], ['id'])
    op.create_foreign_key(None, 'PurchaseOrder', 'Supplier', ['supplierId'], ['id'])

    # Shipment table
    op.create_table('Shipment', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'purchaseOrderId', sa.Integer(), nullable=True)
    op.create_column(None, 'trackingNumber', sa.String(), nullable=True)
    op.create_column(None, 'carrier', sa.String(), nullable=True)
    op.create_column(None, 'status', sa.String(), nullable=False, server_default='preparing')
    op.create_column(None, 'estimatedDeliveryDate', sa.DateTime(), nullable=True)
    op.create_column(None, 'actualDeliveryDate', sa.DateTime(), nullable=True)
    op.create_column(None, 'shippingAddress', sa.String(), nullable=True)
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'updatedAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_foreign_key(None, 'Shipment', 'PurchaseOrder', ['purchaseOrderId'], ['id'])

    # Invoice table
    op.create_table('Invoice', sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True))
    op.create_column(None, 'purchaseOrderId', sa.Integer(), nullable=True)
    op.create_column(None, 'invoiceNumber', sa.String(), nullable=False, unique=True)
    op.create_column(None, 'status', sa.String(), nullable=False, server_default='draft')
    op.create_column(None, 'amount', sa.Float(), nullable=False)
    op.create_column(None, 'dueDate', sa.DateTime(), nullable=True)
    op.create_column(None, 'paidDate', sa.DateTime(), nullable=True)
    op.create_column(None, 'notes', sa.String(), nullable=True)
    op.create_column(None, 'createdAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_column(None, 'updatedAt', sa.DateTime(), nullable=False, server_default='CURRENT_TIMESTAMP')
    op.create_foreign_key(None, 'Invoice', 'PurchaseOrder', ['purchaseOrderId'], ['id'])


def downgrade() -> None:
    op.drop_table('Invoice')
    op.drop_table('Shipment')
    op.drop_table('PurchaseOrder')
    op.drop_table('Quote')
    op.drop_table('ProcurementRequest')
    op.drop_table('Supplier')
    op.drop_table('ProductCategory')
    op.drop_table('AuditLog')
    op.drop_table('Activity')
    op.drop_table('SequenceEnrollment')
    op.drop_table('Sequence')
    op.drop_table('Agent')
    op.drop_table('Deal')
    op.drop_table('Lead')
    op.drop_table('Contact')
    op.drop_table('Company')
    op.drop_table('User')