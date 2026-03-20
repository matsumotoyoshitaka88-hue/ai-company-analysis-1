"""ARQ worker configuration."""
from __future__ import annotations

from arq import cron
from arq.connections import RedisSettings

from app.config import settings
from app.workers.tasks import run_diagnosis_task


def parse_redis_url(url: str) -> RedisSettings:
    """Parse Redis URL into ARQ RedisSettings."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=parsed.password,
        database=int(parsed.path.lstrip("/") or "0"),
    )


class WorkerSettings:
    """ARQ worker settings."""

    functions = [run_diagnosis_task]
    redis_settings = parse_redis_url(settings.redis_url)
    max_jobs = 10
    job_timeout = 300  # 5 minutes max per job
    keep_result = 3600  # Keep results for 1 hour
