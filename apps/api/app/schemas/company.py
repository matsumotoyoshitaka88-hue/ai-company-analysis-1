from __future__ import annotations

from pydantic import BaseModel


class CompanyResponse(BaseModel):
    code: str
    name: str
    industry: str | None = None
    exchange: str | None = None

    model_config = {"from_attributes": True}
