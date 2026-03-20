"""Data collection orchestrator.

Coordinates parallel data collection from multiple sources.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.financial_data import FinancialData
from app.services.data_collection.company_master import find_peer_companies
from app.services.data_collection.edinet import EdinetClient, XbrlParser
from app.services.data_collection.news import NewsCollector

logger = logging.getLogger(__name__)


class CollectedData:
    """Container for all collected data about a company."""

    def __init__(self) -> None:
        self.company_name: str = ""
        self.edinet_code: str = ""
        self.securities_code: str = ""
        self.industry: str = ""
        self.financial_metrics: dict[str, Any] = {}
        self.peer_metrics: dict[str, dict[str, Any]] = {}  # peer_name -> metrics
        self.news_articles: list[dict[str, Any]] = []
        self.news_summary: str = ""
        self.data_sources: list[str] = []
        self.errors: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "edinet_code": self.edinet_code,
            "securities_code": self.securities_code,
            "industry": self.industry,
            "financial_metrics": self.financial_metrics,
            "peer_metrics": self.peer_metrics,
            "news_articles": self.news_articles,
            "news_summary": self.news_summary,
            "data_sources": self.data_sources,
            "errors": self.errors,
        }


async def collect_company_data(
    db: AsyncSession,
    company: Company,
    edinet_client: Optional[EdinetClient] = None,
) -> CollectedData:
    """Collect all available data for a company.

    Runs data collection from multiple sources in parallel.

    Args:
        db: Database session.
        company: Target company.
        edinet_client: Optional EDINET client.

    Returns:
        CollectedData with all collected information.
    """
    result = CollectedData()
    result.company_name = company.name
    result.edinet_code = company.edinet_code
    result.securities_code = company.securities_code or ""
    result.industry = company.industry_name or ""

    client = edinet_client or EdinetClient()
    news_collector = NewsCollector()

    try:
        # Run collections in parallel
        financial_task = _collect_financial_data(db, company, client, result)
        peer_task = _collect_peer_data(db, company, client, result)
        news_task = _collect_news(company.name, news_collector, result)

        await asyncio.gather(
            financial_task,
            peer_task,
            news_task,
            return_exceptions=True,
        )

    finally:
        if edinet_client is None:
            await client.close()
        await news_collector.close()

    return result


async def _collect_financial_data(
    db: AsyncSession,
    company: Company,
    client: EdinetClient,
    result: CollectedData,
) -> None:
    """Collect financial data from EDINET."""
    try:
        # Check cache first
        from sqlalchemy import select

        stmt = (
            select(FinancialData)
            .where(FinancialData.company_id == company.id)
            .order_by(FinancialData.fiscal_year.desc())
            .limit(3)
        )
        db_result = await db.execute(stmt)
        cached = list(db_result.scalars().all())

        if cached:
            # Use cached data
            result.financial_metrics = cached[0].data
            result.data_sources.append(f"有価証券報告書（キャッシュ: {cached[0].fiscal_year}年度）")
            return

        # Fetch from EDINET
        filings = await client.search_filings(company.edinet_code)
        if not filings:
            result.errors.append("有価証券報告書が見つかりませんでした")
            return

        latest_filing = filings[0]
        doc_id = latest_filing.get("docID")
        if not doc_id:
            result.errors.append("書類IDが取得できませんでした")
            return

        # Download and parse XBRL
        xbrl_files = await client.download_xbrl(doc_id)
        metrics: dict[str, Any] = {}

        for filename, content in xbrl_files.items():
            if filename.endswith(".json"):
                parsed = XbrlParser.parse_xbrl_json(content)
            elif filename.endswith((".htm", ".xbrl")):
                parsed = XbrlParser.parse_inline_xbrl(content)
            else:
                continue
            # Merge keeping largest absolute values (prefer consolidated)
            for k, v in parsed.items():
                if k not in metrics or abs(v) > abs(metrics[k]):
                    metrics[k] = v

        if metrics:
            result.financial_metrics = metrics
            result.data_sources.append(
                f"有価証券報告書（{latest_filing.get('periodEnd', 'N/A')}）"
            )

            # Cache to database
            fiscal_year = latest_filing.get("periodEnd", "")[:4] or str(date.today().year)
            period_end_str = latest_filing.get("periodEnd", "")
            try:
                period_end = date.fromisoformat(period_end_str) if period_end_str else date.today()
            except ValueError:
                period_end = date.today()

            financial_data = FinancialData(
                company_id=company.id,
                fiscal_year=fiscal_year,
                period_end=period_end,
                data=metrics,
                raw_xbrl_ref=doc_id,
            )
            db.add(financial_data)
        else:
            result.errors.append("財務データの解析に失敗しました")

    except Exception as e:
        logger.error("Financial data collection failed for %s: %s", company.name, e)
        result.errors.append(f"財務データ取得エラー: {str(e)}")


async def _collect_peer_data(
    db: AsyncSession,
    company: Company,
    client: EdinetClient,
    result: CollectedData,
) -> None:
    """Collect financial data for peer companies."""
    try:
        peers = await find_peer_companies(db, company, limit=5)
        if not peers:
            return

        for peer in peers:
            try:
                # Check cache
                from sqlalchemy import select

                stmt = (
                    select(FinancialData)
                    .where(FinancialData.company_id == peer.id)
                    .order_by(FinancialData.fiscal_year.desc())
                    .limit(1)
                )
                db_result = await db.execute(stmt)
                cached = db_result.scalar_one_or_none()

                if cached:
                    result.peer_metrics[peer.name] = cached.data
                else:
                    # Fetch from EDINET (simplified: just use cached data for MVP)
                    pass
            except Exception as e:
                logger.warning("Failed to collect peer data for %s: %s", peer.name, e)

        if result.peer_metrics:
            result.data_sources.append(f"同業他社データ（{len(result.peer_metrics)}社）")

    except Exception as e:
        logger.error("Peer data collection failed: %s", e)


async def _collect_news(
    company_name: str,
    collector: NewsCollector,
    result: CollectedData,
) -> None:
    """Collect recent news articles."""
    try:
        articles = await collector.search_news(company_name)
        result.news_articles = articles
        result.news_summary = await collector.summarize_news_context(articles)
        if articles:
            result.data_sources.append(f"ニュース記事（{len(articles)}件）")
    except Exception as e:
        logger.error("News collection failed for %s: %s", company_name, e)
        result.errors.append(f"ニュース取得エラー: {str(e)}")
