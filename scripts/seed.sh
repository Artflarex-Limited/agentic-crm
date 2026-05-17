#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR/backend"

echo "=== Seeding database with sample data ==="

export PYTHONPATH="${PROJECT_DIR}/backend:$PYTHONPATH"

if [ -n "$POSTGRES_PASSWORD" ]; then
    export PGPASSWORD="$POSTGRES_PASSWORD"
fi

DATABASE_URL="${DATABASE_URL:-postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-agentic_crm}}"
export DATABASE_URL

python3 << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/root/agentic-crm/backend')

from app.prisma import connect_prisma, disconnect_prisma, prisma
from app.models import User, Company, Contact, Lead, Agent, Deal

async def seed():
    await connect_prisma()

    existing = await prisma.user.count()
    if existing > 0:
        print(f"Database already has {existing} users, skipping seed")
        await disconnect_prisma()
        return

    print("Creating sample data...")

    user = await prisma.user.create(
        data={
            "email": "admin@agentic-crm.dev",
            "passwordHash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.A3J4MmHqG.X9S2",
            "fullName": "Admin User",
            "role": "admin",
        }
    )
    print(f"Created user: {user.email}")

    company = await prisma.company.create(
        data={
            "name": "Artflarex Solutions",
            "domain": "artflarex.com",
            "industry": "Technology",
            "size": "10-50",
        }
    )
    print(f"Created company: {company.name}")

    contact = await prisma.contact.create(
        data={
            "companyId": company.id,
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "title": "CEO",
        }
    )
    print(f"Created contact: {contact.firstName} {contact.lastName}")

    agent = await prisma.agent.create(
        data={
            "name": "Lead Sourcing Agent",
            "role": "lead_sourcing",
            "status": "active",
            "description": "Automatically finds and qualifies leads",
        }
    )
    print(f"Created agent: {agent.name}")

    lead = await prisma.lead.create(
        data={
            "contactId": contact.id,
            "source": "linkedin",
            "stage": "new",
            "score": 75,
            "assignedAgentId": agent.id,
        }
    )
    print(f"Created lead: {lead.id}")

    deal = await prisma.deal.create(
        data={
            "contactId": contact.id,
            "companyId": company.id,
            "name": "Enterprise License",
            "value": 50000.0,
            "stage": "qualified",
        }
    )
    print(f"Created deal: {deal.name} (${deal.value})")

    await disconnect_prisma()
    print("=== Seed complete ===")

asyncio.run(seed())
EOF

echo "=== Done ==="