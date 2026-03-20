"""Diagnosis pipeline - the full async job orchestrator.

Coordinates the entire diagnosis process from company resolution
to report storage.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.company import Company
from app.models.diagnosis import DiagnosisJob, DiagnosisReport
from app.services.data_collection.company_master import find_company
from app.services.report.builder import build_diagnosis_report

logger = logging.getLogger(__name__)


async def run_diagnosis(
    db: AsyncSession,
    job_id: uuid.UUID,
    company_code: str | None = None,
    company_name: str | None = None,
) -> None:
    """Run the full diagnosis pipeline for a job.

    Updates job status as it progresses through each step.

    Args:
        db: Database session.
        job_id: The diagnosis job ID.
        company_code: Securities code or EDINET code.
        company_name: Company name (used if code not provided).
    """
    # Get the job
    stmt = select(DiagnosisJob).where(DiagnosisJob.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        logger.error("Job %s not found", job_id)
        return

    try:
        # Step 1: Resolve company
        await _update_job_status(db, job, "COLLECTING", "企業情報を検索中...", 10)

        query = company_code or company_name or ""
        company = await find_company(db, query)
        if not company:
            await _fail_job(db, job, f"企業が見つかりませんでした: {query}")
            return

        job.company_id = company.id
        await db.flush()

        # Step 2: Check for cached report
        cached = await _check_cache(db, company.id)
        if cached:
            job.status = "COMPLETED"
            job.completed_at = datetime.utcnow()
            job.progress = {"current_step": "完了", "percent": 100, "message": "キャッシュ済みレポートを使用"}

            # Create report linking to cached data
            report = DiagnosisReport(
                job_id=job.id,
                company_id=company.id,
                overall_score=cached.overall_score,
                overall_traffic_light=cached.overall_traffic_light,
                report_data=cached.report_data,
            )
            db.add(report)
            await db.commit()
            return

        # Step 3: Collect data
        await _update_job_status(db, job, "COLLECTING", "公開データを収集中...", 30)

        # Step 4: Analyze
        await _update_job_status(db, job, "ANALYZING", "財務データを分析中...", 50)

        # Step 5: Generate report
        await _update_job_status(db, job, "GENERATING", "AIがレポートを生成中...", 70)

        report_data = await build_diagnosis_report(db, company)

        # Step 6: Store report
        overall_score_data = report_data.get("overall_score", {})
        report = DiagnosisReport(
            job_id=job.id,
            company_id=company.id,
            overall_score=overall_score_data.get("score"),
            overall_traffic_light=overall_score_data.get("traffic_light"),
            report_data=report_data,
        )
        db.add(report)

        # Mark job as complete
        job.status = "COMPLETED"
        job.completed_at = datetime.utcnow()
        job.expires_at = datetime.utcnow() + timedelta(seconds=settings.report_cache_ttl)
        job.progress = {"current_step": "完了", "percent": 100, "message": "診断レポートが完成しました"}

        await db.commit()
        logger.info("Diagnosis completed for %s (job: %s)", company.name, job_id)

    except Exception as e:
        logger.error("Diagnosis pipeline failed for job %s: %s", job_id, e, exc_info=True)
        await _fail_job(db, job, f"診断処理中にエラーが発生しました: {str(e)}")


async def _update_job_status(
    db: AsyncSession,
    job: DiagnosisJob,
    status: str,
    message: str,
    percent: int,
) -> None:
    """Update job status and progress."""
    job.status = status
    job.progress = {"current_step": status, "percent": percent, "message": message}
    await db.commit()


async def _fail_job(db: AsyncSession, job: DiagnosisJob, error: str) -> None:
    """Mark a job as failed."""
    job.status = "FAILED"
    job.error_message = error
    job.progress = {"current_step": "FAILED", "percent": 0, "message": error}
    await db.commit()


async def _check_cache(db: AsyncSession, company_id: int) -> DiagnosisReport | None:
    """Check if a recent valid report exists for this company."""
    stmt = (
        select(DiagnosisReport)
        .join(DiagnosisJob)
        .where(
            DiagnosisReport.company_id == company_id,
            DiagnosisJob.status == "COMPLETED",
            DiagnosisJob.expires_at > datetime.utcnow(),
        )
        .order_by(DiagnosisReport.generated_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
