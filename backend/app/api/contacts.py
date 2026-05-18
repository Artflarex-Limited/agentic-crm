"""
Contacts API routes
"""
from fastapi import APIRouter, HTTPException, Request

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.prisma import prisma
from app.schemas.schemas import ContactCreate, ContactResponse

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=list[ContactResponse])
@limiter.limit(settings.rate_limit_default)
async def list_contacts(request: Request):
    contacts = await prisma.contact.find_many(order=[{"id": "desc"}])
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
@limiter.limit(settings.rate_limit_default)
async def get_contact(contact_id: int, request: Request):
    contact = await prisma.contact.find_unique(where={"id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.post("/", response_model=ContactResponse, status_code=201)
@limiter.limit(settings.rate_limit_default)
async def create_contact(request: Request, data: ContactCreate):
    contact = await prisma.contact.create(
        data={
            **{k: v for k, v in data.model_dump().items() if k != "extra_data"},
            "extraData": data.extra_data,
        }
    )
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
@limiter.limit(settings.rate_limit_default)
async def update_contact(contact_id: int, request: Request, data: ContactCreate):
    existing = await prisma.contact.find_unique(where={"id": contact_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact = await prisma.contact.update(
        where={"id": contact_id},
        data={
            **{k: v for k, v in data.model_dump().items() if k != "extra_data"},
            "extraData": data.extra_data,
        },
    )
    return contact


@router.delete("/{contact_id}")
@limiter.limit(settings.rate_limit_default)
async def delete_contact(contact_id: int, request: Request):
    existing = await prisma.contact.find_unique(where={"id": contact_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Contact not found")
    await prisma.contact.delete(where={"id": contact_id})
    return {"deleted": True}
