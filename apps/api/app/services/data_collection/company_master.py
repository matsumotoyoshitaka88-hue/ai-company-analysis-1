"""Company master data management.

Syncs the EDINET company code list to the local database.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.services.data_collection.edinet import EdinetClient

logger = logging.getLogger(__name__)

# Mapping of EDINET CSV column names to our model fields
CSV_FIELD_MAP = {
    "ＥＤＩＮＥＴコード": "edinet_code",
    "提出者種別": "submitter_type",
    "上場区分": "listing_status",
    "提出者名": "name",
    "提出者名（英字）": "name_en",
    "提出者業種": "industry_name",
    "証券コード": "securities_code",
    "提出者法人番号": "corporate_number",
}


async def sync_company_master(db: AsyncSession, edinet_client: Optional[EdinetClient] = None) -> int:
    """Sync EDINET company list to local database.

    Args:
        db: Database session.
        edinet_client: Optional EDINET client (created if not provided).

    Returns:
        Number of companies synced.
    """
    client = edinet_client or EdinetClient()
    try:
        raw_companies = await client.get_company_list()
    finally:
        if edinet_client is None:
            await client.close()

    count = 0
    for row in raw_companies:
        edinet_code = row.get("ＥＤＩＮＥＴコード", "").strip()
        if not edinet_code:
            continue

        # Only import listed companies (上場区分 contains exchange info)
        listing = row.get("上場区分", "").strip()
        if not listing or listing == "非上場":
            continue

        securities_code = row.get("証券コード", "").strip() or None
        name = row.get("提出者名", "").strip()
        if not name:
            continue

        # Upsert: check if company exists
        stmt = select(Company).where(Company.edinet_code == edinet_code)
        result = await db.execute(stmt)
        company = result.scalar_one_or_none()

        if company is None:
            company = Company(edinet_code=edinet_code)
            db.add(company)

        company.name = name
        company.name_en = row.get("提出者名（英字）", "").strip() or None
        company.securities_code = securities_code
        company.industry_name = row.get("提出者業種", "").strip() or None
        company.exchange = listing

        count += 1

    await db.flush()
    logger.info("Synced %d companies from EDINET", count)
    return count


async def find_company(
    db: AsyncSession,
    query: str,
) -> Optional[Company]:
    """Find a company by securities code, EDINET code, or name.

    First searches the local DB, then falls back to EDINET API.

    Args:
        db: Database session.
        query: Search query (securities code, EDINET code, or name).

    Returns:
        Company if found, None otherwise.
    """
    # Try securities code first (4-5 digits)
    if query.isdigit() and len(query) <= 5:
        stmt = select(Company).where(Company.securities_code == query)
        result = await db.execute(stmt)
        company = result.scalar_one_or_none()
        if company:
            return company

    # Try EDINET code
    stmt = select(Company).where(Company.edinet_code == query)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    if company:
        return company

    # Try exact name match
    stmt = select(Company).where(Company.name == query)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    if company:
        return company

    # Try partial name match
    stmt = select(Company).where(Company.name.ilike(f"%{query}%")).limit(1)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    if company:
        return company

    # Fallback: search EDINET API for the company in recent filings
    return await _find_company_from_edinet(db, query)


async def _find_company_from_edinet(
    db: AsyncSession,
    query: str,
) -> Optional[Company]:
    """Search EDINET recent filings to find and register a company."""
    from datetime import date, timedelta

    client = EdinetClient()
    try:
        # Search recent 7 days of filings for the company name
        today = date.today()
        for day_offset in range(7):
            check_date = today - timedelta(days=day_offset)
            try:
                docs = await client.list_documents(check_date)
            except Exception:
                continue

            for doc in docs:
                filer_name = doc.get("filerName", "")
                edinet_code = doc.get("edinetCode", "")
                sec_code = doc.get("secCode")

                if not filer_name or not edinet_code:
                    continue

                # Check if the query matches the filer name
                if query in filer_name or filer_name in query:
                    # Register this company in the DB
                    stmt = select(Company).where(Company.edinet_code == edinet_code)
                    result = await db.execute(stmt)
                    company = result.scalar_one_or_none()

                    if company is None:
                        company = Company(
                            edinet_code=edinet_code,
                            name=filer_name,
                            securities_code=sec_code if sec_code and sec_code.strip() else None,
                            industry_name=doc.get("industryCodeForSummary"),
                        )
                        db.add(company)
                        await db.flush()
                        logger.info("Registered company from EDINET: %s (%s)", filer_name, edinet_code)

                    return company
    finally:
        await client.close()

    return None


async def find_peer_companies(
    db: AsyncSession,
    company: Company,
    limit: int = 5,
) -> list[Company]:
    """Find peer companies in the same industry.

    Args:
        db: Database session.
        company: Target company.
        limit: Max number of peers.

    Returns:
        List of peer companies.
    """
    if not company.industry_name:
        return []

    stmt = (
        select(Company)
        .where(
            Company.industry_name == company.industry_name,
            Company.id != company.id,
            Company.securities_code.isnot(None),
        )
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
