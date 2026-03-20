from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    edinet_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    securities_code: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(200))
    industry_code: Mapped[Optional[str]] = mapped_column(String(10))
    industry_name: Mapped[Optional[str]] = mapped_column(String(100))
    exchange: Mapped[Optional[str]] = mapped_column(String(50))
    accounting_standard: Mapped[Optional[str]] = mapped_column(String(20))
    fiscal_year_end: Mapped[Optional[str]] = mapped_column(String(4))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
