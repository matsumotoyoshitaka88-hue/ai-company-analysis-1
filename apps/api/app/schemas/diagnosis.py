from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DiagnosisRequest(BaseModel):
    company_code: str | None = None
    company_name: str | None = None


class DiagnosisJobResponse(BaseModel):
    job_id: uuid.UUID
    status: str

    model_config = {"from_attributes": True}


class DiagnosisProgress(BaseModel):
    current_step: str
    percent: int
    message: str | None = None


class DiagnosisStatusResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    progress: DiagnosisProgress | None = None
    report: dict[str, Any] | None = None
    generated_at: datetime | None = None

    model_config = {"from_attributes": True}
