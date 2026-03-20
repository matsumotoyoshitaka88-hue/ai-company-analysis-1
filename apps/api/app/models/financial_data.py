from datetime import date, datetime
from typing import Any, Dict, Optional

from sqlalchemy import DATE, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FinancialData(Base):
    __tablename__ = "financial_data"
    __table_args__ = (UniqueConstraint("company_id", "fiscal_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    fiscal_year: Mapped[str] = mapped_column(String(4), nullable=False)
    period_end: Mapped[date] = mapped_column(DATE, nullable=False)
    data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    raw_xbrl_ref: Mapped[Optional[str]] = mapped_column(String(500))
    collected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
