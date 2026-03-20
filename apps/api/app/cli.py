"""CLI commands for administration tasks."""
from __future__ import annotations

import asyncio
import logging
import sys

from app.db.session import async_session
from app.services.data_collection.company_master import sync_company_master

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _sync_companies() -> None:
    """Sync EDINET company master data to local database."""
    async with async_session() as db:
        count = await sync_company_master(db)
        await db.commit()
        logger.info("Synced %d companies", count)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m app.cli <command>")
        print("Commands: sync-companies")
        sys.exit(1)

    command = sys.argv[1]
    if command == "sync-companies":
        asyncio.run(_sync_companies())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
