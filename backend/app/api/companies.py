"""
Companies API routes
"""
from fastapi import APIRouter, HTTPException, Request

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.prisma import prisma
from app.schemas.schemas import CompanyCreate, CompanyResponse

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=list[CompanyResponse])
@limiter.limit(settings.rate_limit_default)
async def list_companies(request: Request):
    companies = await prisma.company.find_many(order=[{"id": "desc"}])
    return companies


@router.get("/{company_id}", response_model=CompanyResponse)
@limiter.limit(settings.rate_limit_default)
async def get_company(company_id: int, request: Request):
    company = await prisma.company.find_unique(where={"id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/", response_model=CompanyResponse, status_code=201)
@limiter.limit(settings.rate_limit_default)
async def create_company(request: Request, data: CompanyCreate):
    company = await prisma.company.create(
        data={
            **{k: v for k, v in data.model_dump().items() if k != "extra_data"},
            "extraData": data.extra_data,
        }
    )
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
@limiter.limit(settings.rate_limit_default)
async def update_company(company_id: int, request: Request, data: CompanyCreate):
    existing = await prisma.company.find_unique(where={"id": company_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Company not found")
    company = await prisma.company.update(
        where={"id": company_id},
        data={
            **{k: v for k, v in data.model_dump().items() if k != "extra_data"},
            "extraData": data.extra_data,
        },
    )
    return company


@router.delete("/{company_id}")
@limiter.limit(settings.rate_limit_default)
async def delete_company(company_id: int, request: Request):
    existing = await prisma.company.find_unique(where={"id": company_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Company not found")
    await prisma.company.delete(where={"id": company_id})
    return {"deleted": True}
