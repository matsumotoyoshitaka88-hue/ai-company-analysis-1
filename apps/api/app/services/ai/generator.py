"""AI report generation using Claude API.

Generates narrative sections from pre-computed structured data.
Each section is generated independently for parallelism and retry.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import anthropic

from app.config import settings
from app.services.ai.prompts import (
    SYSTEM_PROMPT,
    build_competitive_position_prompt,
    build_dx_maturity_prompt,
    build_executive_summary_prompt,
    build_financial_diagnosis_prompt,
    build_risk_opportunity_prompt,
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate diagnosis report sections using Claude API."""

    def __init__(self) -> None:
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    async def _generate_section(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate a single report section.

        Args:
            prompt: The section-specific prompt.
            max_tokens: Max tokens for response.

        Returns:
            Generated text content.
        """
        try:
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            logger.error("Claude API error: %s", e)
            return f"レポート生成中にエラーが発生しました: {str(e)}"

    async def generate_full_report(
        self,
        company_name: str,
        industry: str,
        ratios: dict[str, Any],
        overall_score: dict[str, Any],
        profitability: dict[str, Any],
        safety: dict[str, Any],
        efficiency: dict[str, Any],
        competitive: dict[str, Any],
        dx: dict[str, Any],
        news_summary: str,
    ) -> dict[str, str]:
        """Generate all report sections in parallel.

        Args:
            company_name: Company name.
            industry: Industry name.
            ratios: Calculated financial ratios.
            overall_score: Overall score dict.
            profitability: Profitability scoring.
            safety: Safety scoring.
            efficiency: Efficiency scoring.
            competitive: Competitive position scoring.
            dx: DX maturity scoring.
            news_summary: News summary text.

        Returns:
            Dict mapping section name to generated content.
        """
        # Build all prompts
        prompts = {
            "executive_summary": build_executive_summary_prompt(
                company_name, overall_score, profitability, safety, competitive, dx, news_summary
            ),
            "financial_diagnosis": build_financial_diagnosis_prompt(
                company_name, ratios, profitability, safety, efficiency, industry
            ),
            "competitive_position": build_competitive_position_prompt(
                company_name, ratios, competitive
            ),
            "dx_maturity": build_dx_maturity_prompt(
                company_name, dx, news_summary
            ),
            "risk_opportunity": build_risk_opportunity_prompt(
                company_name, overall_score, profitability, safety, competitive, news_summary, industry
            ),
        }

        # Generate all sections in parallel
        tasks = {
            name: self._generate_section(prompt)
            for name, prompt in prompts.items()
        }

        results: dict[str, str] = {}
        gathered = await asyncio.gather(
            *[tasks[name] for name in tasks],
            return_exceptions=True,
        )

        for name, result in zip(tasks.keys(), gathered):
            if isinstance(result, Exception):
                logger.error("Section %s generation failed: %s", name, result)
                results[name] = f"このセクションの生成中にエラーが発生しました。"
            else:
                results[name] = result

        return results
