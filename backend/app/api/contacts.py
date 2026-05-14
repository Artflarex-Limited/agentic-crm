"""
Contacts API routes
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.database import get_db
from app.models.models import Contact
from app.schemas.schemas import ContactCreate, ContactResponse

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=list[ContactResponse])
@limiter.limit(settings.rate_limit_default)
async def list_contacts(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).order_by(Contact.id.desc()))
    contacts = result.scalars().all()
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
@limiter.limit(settings.rate_limit_default)
async def get_contact(contact_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.post("/", response_model=ContactResponse, status_code=201)
@limiter.limit(settings.rate_limit_default)
async def create_contact(request: Request, data: ContactCreate, db: AsyncSession = Depends(get_db)):
    contact = Contact(**data.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
@limiter.limit(settings.rate_limit_default)
async def update_contact(contact_id: int, request: Request, data: ContactCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    for key, value in data.model_dump().items():
        setattr(contact, key, value)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.delete("/{contact_id}")
@limiter.limit(settings.rate_limit_default)
async def delete_contact(contact_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    await db.delete(contact)
    await db.commit()
    return {"deleted": True}
