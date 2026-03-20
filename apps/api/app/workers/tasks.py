"""ARQ task definitions for async job processing."""
from __future__ import annotations

import logging
import uuid

from app.db.session import async_session
from app.services.diagnosis_pipeline import run_diagnosis

logger = logging.getLogger(__name__)


async def run_diagnosis_task(
    ctx: dict,
    job_id: str,
    company_code: str | None = None,
    company_name: str | None = None,
) -> None:
    """ARQ task to run a diagnosis job.

    Args:
        ctx: ARQ context dict.
        job_id: UUID string of the diagnosis job.
        company_code: Securities or EDINET code.
        company_name: Company name.
    """
    logger.info("Starting diagnosis task for job %s", job_id)
    async with async_session() as db:
        try:
            await run_diagnosis(
                db=db,
                job_id=uuid.UUID(job_id),
                company_code=company_code,
                company_name=company_name,
            )
        except Exception as e:
            logger.error("Diagnosis task failed for job %s: %s", job_id, e, exc_info=True)
            raise
