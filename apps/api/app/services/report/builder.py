"""Report builder - assembles the full diagnosis report.

Orchestrates data collection, analysis, scoring, and AI generation
into a complete report structure.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.services.analysis.financial import calc_financial_ratios, get_industry_benchmark
from app.services.analysis.scoring import (
    calculate_overall_score,
    score_competitive_position,
    score_dx_maturity,
    score_efficiency,
    score_profitability,
    score_safety,
    traffic_light_label,
)
from app.services.ai.generator import ReportGenerator
from app.services.data_collection.collector import CollectedData, collect_company_data

logger = logging.getLogger(__name__)


async def build_diagnosis_report(
    db: AsyncSession,
    company: Company,
) -> dict[str, Any]:
    """Build a complete diagnosis report for a company.

    This is the main orchestration function that:
    1. Collects data from EDINET, news, etc.
    2. Calculates financial ratios and scores
    3. Generates AI narrative for each section
    4. Assembles the complete report

    Args:
        db: Database session.
        company: Target company.

    Returns:
        Complete report data dict matching the API schema.
    """
    # Step 1: Collect data
    logger.info("Collecting data for %s...", company.name)
    collected = await collect_company_data(db, company)

    # Step 2: Calculate ratios and scores
    logger.info("Analyzing data for %s...", company.name)
    ratios = calc_financial_ratios(collected.financial_metrics)
    benchmark = get_industry_benchmark(collected.industry)

    profitability = score_profitability(ratios, benchmark)
    safety = score_safety(ratios, benchmark)
    efficiency = score_efficiency(ratios, benchmark)

    competitive = score_competitive_position(ratios, collected.peer_metrics)
    dx = score_dx_maturity(collected.financial_metrics, collected.news_articles)
    overall = calculate_overall_score(profitability, safety, efficiency, competitive, dx)

    # Step 3: Generate AI narratives
    logger.info("Generating AI report for %s...", company.name)
    generator = ReportGenerator()
    narratives = await generator.generate_full_report(
        company_name=company.name,
        industry=collected.industry,
        ratios=ratios,
        overall_score=overall,
        profitability=profitability,
        safety=safety,
        efficiency=efficiency,
        competitive=competitive,
        dx=dx,
        news_summary=collected.news_summary,
    )

    # Step 4: Assemble report
    report: dict[str, Any] = {
        "company": {
            "code": company.securities_code or company.edinet_code,
            "name": company.name,
            "industry": collected.industry,
        },
        "overall_score": {
            "score": overall["score"],
            "traffic_light": overall["traffic_light"],
            "summary_text": _build_summary_text(company.name, overall),
        },
        "sections": {
            "executive_summary": {
                "content": narratives.get("executive_summary", ""),
            },
            "financial_diagnosis": {
                "profitability": profitability,
                "safety": safety,
                "efficiency": efficiency,
                "narrative": narratives.get("financial_diagnosis", ""),
                "industry_comparison": {
                    "industry": collected.industry,
                    "benchmark": benchmark,
                },
            },
            "competitive_position": {
                "peers": competitive.get("peers", []),
                "ranking": competitive.get("ranking", []),
                "score": competitive["score"],
                "traffic_light": competitive["traffic_light"],
                "narrative": narratives.get("competitive_position", ""),
            },
            "dx_maturity": {
                "score": dx["score"],
                "traffic_light": dx["traffic_light"],
                "indicators": dx.get("indicators", []),
                "narrative": narratives.get("dx_maturity", ""),
            },
            "risk_opportunity": {
                "narrative": narratives.get("risk_opportunity", ""),
            },
        },
        "data_sources": collected.data_sources,
        "errors": collected.errors,
    }

    return report


def _build_summary_text(company_name: str, overall: dict[str, Any]) -> str:
    """Build a short summary text for the overall score banner."""
    score = overall["score"]
    tl = overall["traffic_light"]
    label = traffic_light_label(tl)

    if score >= 80:
        return f"{company_name}の経営状態は{label}です。財務基盤が安定しており、競争力のある経営を行っています。"
    elif score >= 60:
        return f"{company_name}の経営状態は概ね{label}です。一部改善の余地がありますが、全体として安定しています。"
    elif score >= 40:
        return f"{company_name}の経営状態には{label}が必要な領域があります。重点的な改善策の検討をお勧めします。"
    else:
        return f"{company_name}の経営状態は{label}が必要です。早急な対策の検討をお勧めします。"
