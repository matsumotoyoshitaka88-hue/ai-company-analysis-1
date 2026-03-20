from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.company import Company
from app.schemas.company import CompanyResponse

router = APIRouter()


@router.get("/search", response_model=list[CompanyResponse])
async def search_companies(
    db: DbSession,
    q: str = Query(..., min_length=1, description="Search query (company name or securities code)"),
    limit: int = Query(10, ge=1, le=50),
) -> list[CompanyResponse]:
    stmt = (
        select(Company)
        .where(Company.name.ilike(f"%{q}%") | Company.securities_code.ilike(f"{q}%"))
        .limit(limit)
    )
    result = await db.execute(stmt)
    companies = result.scalars().all()
    return [
        CompanyResponse(
            code=c.securities_code or c.edinet_code,
            name=c.name,
            industry=c.industry_name,
            exchange=c.exchange,
        )
        for c in companies
    ]
