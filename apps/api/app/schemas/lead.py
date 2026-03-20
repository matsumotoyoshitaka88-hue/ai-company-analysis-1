from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr


class LeadRequest(BaseModel):
    email: EmailStr
    company_code: str
    job_id: uuid.UUID
    name: str | None = None
    company_name_user: str | None = None


class LeadResponse(BaseModel):
    lead_id: int
    pdf_download_url: str

    model_config = {"from_attributes": True}
