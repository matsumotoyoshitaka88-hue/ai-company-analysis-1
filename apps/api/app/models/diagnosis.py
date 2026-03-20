import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, JSONType, UUIDType


class DiagnosisJob(Base):
    __tablename__ = "diagnosis_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    progress: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType())
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class DiagnosisReport(Base):
    __tablename__ = "diagnosis_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), ForeignKey("diagnosis_jobs.id"), unique=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    overall_score: Mapped[Optional[int]] = mapped_column(Integer)
    overall_traffic_light: Mapped[Optional[str]] = mapped_column(String(10))
    report_data: Mapped[Dict[str, Any]] = mapped_column(JSONType(), nullable=False)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500))
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
