from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession
from app.models.lead import Lead
from app.schemas.lead import LeadRequest, LeadResponse

router = APIRouter()


@router.post("", response_model=LeadResponse)
async def submit_lead(
    request: LeadRequest,
    db: DbSession,
) -> LeadResponse:
    lead = Lead(
        email=request.email,
        name=request.name,
        company_name_user=request.company_name_user,
        job_id=request.job_id,
        source="pdf_download",
    )
    db.add(lead)
    await db.flush()

    pdf_url = f"/api/v1/diagnosis/{request.job_id}/pdf"

    return LeadResponse(lead_id=lead.id, pdf_download_url=pdf_url)
