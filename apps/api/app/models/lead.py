import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDType


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    company_name_user: Mapped[Optional[str]] = mapped_column(String(200))
    diagnosed_company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"))
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType(), ForeignKey("diagnosis_jobs.id"))
    source: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
