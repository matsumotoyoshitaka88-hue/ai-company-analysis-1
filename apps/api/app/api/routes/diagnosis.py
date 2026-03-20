from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.db.session import async_session
from app.models.diagnosis import DiagnosisJob, DiagnosisReport
from app.schemas.diagnosis import DiagnosisJobResponse, DiagnosisRequest, DiagnosisStatusResponse

router = APIRouter()
logger = logging.getLogger(__name__)


async def _run_diagnosis_background(
    job_id: uuid.UUID,
    company_code: str | None,
    company_name: str | None,
) -> None:
    """Run the diagnosis pipeline in a background task with its own DB session."""
    from app.services.diagnosis_pipeline import run_diagnosis

    async with async_session() as db:
        try:
            await run_diagnosis(
                db=db,
                job_id=job_id,
                company_code=company_code,
                company_name=company_name,
            )
        except Exception:
            logger.exception("Background diagnosis failed for job %s", job_id)


@router.post("", response_model=DiagnosisJobResponse)
async def start_diagnosis(
    request: DiagnosisRequest,
    db: DbSession,
) -> DiagnosisJobResponse:
    if not request.company_code and not request.company_name:
        raise HTTPException(status_code=400, detail="company_code or company_name is required")

    # Create job record (company_id is resolved later in the pipeline)
    job = DiagnosisJob(status="PENDING")
    db.add(job)
    await db.commit()

    # Run pipeline in background so the response returns immediately
    asyncio.create_task(
        _run_diagnosis_background(
            job_id=job.id,
            company_code=request.company_code,
            company_name=request.company_name,
        )
    )

    return DiagnosisJobResponse(job_id=job.id, status=job.status)


@router.get("/{job_id}", response_model=DiagnosisStatusResponse)
async def get_diagnosis_status(
    job_id: uuid.UUID,
    db: DbSession,
) -> DiagnosisStatusResponse:
    stmt = select(DiagnosisJob).where(DiagnosisJob.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Diagnosis job not found")

    report_data = None
    generated_at = None
    if job.status == "COMPLETED":
        stmt = select(DiagnosisReport).where(DiagnosisReport.job_id == job_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()
        if report:
            report_data = report.report_data
            generated_at = report.generated_at

    return DiagnosisStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        report=report_data,
        generated_at=generated_at,
    )
