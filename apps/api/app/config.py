from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Company Diagnosis Service"
    debug: bool = False

    # Database (use SQLite for local dev, PostgreSQL for production)
    database_url: str = "sqlite+aiosqlite:///./company_analysis.db"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Claude API
    anthropic_api_key: str = ""

    # EDINET API
    edinet_api_key: str = ""

    # Report cache TTL (seconds) - 7 days
    report_cache_ttl: int = 7 * 24 * 60 * 60

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
