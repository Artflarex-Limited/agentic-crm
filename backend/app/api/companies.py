"""
Companies API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Company
from app.schemas.schemas import CompanyCreate, CompanyResponse

router = APIRouter()


@router.get("/", response_model=list[CompanyResponse])
async def list_companies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).order_by(Company.id.desc()))
    return result.scalars().all()


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/", response_model=CompanyResponse, status_code=201)
async def create_company(data: CompanyCreate, db: AsyncSession = Depends(get_db)):
    company = Company(**data.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: int, data: CompanyCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for key, value in data.model_dump().items():
        setattr(company, key, value)
    await db.commit()
    await db.refresh(company)
    return company


@router.delete("/{company_id}")
async def delete_company(company_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    await db.delete(company)
    await db.commit()
    return {"deleted": True}
