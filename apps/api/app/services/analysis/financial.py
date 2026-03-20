"""Financial metric calculation and scoring.

All calculations are deterministic - no AI involved.
"""
from __future__ import annotations

from typing import Any, Optional


def safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    """Safe division, returns None if either value is None or divisor is zero."""
    if a is None or b is None or b == 0:
        return None
    return a / b


def calc_financial_ratios(metrics: dict[str, Any]) -> dict[str, Any]:
    """Calculate key financial ratios from raw metrics.

    Args:
        metrics: Raw financial metrics from XBRL parsing.

    Returns:
        Dict of calculated financial ratios.
    """
    revenue = metrics.get("revenue")
    operating_income = metrics.get("operating_income")
    ordinary_income = metrics.get("ordinary_income")
    net_income = metrics.get("net_income")
    total_assets = metrics.get("total_assets")
    net_assets = metrics.get("net_assets")
    shareholders_equity = metrics.get("shareholders_equity", net_assets)
    total_liabilities = metrics.get("total_liabilities")
    current_assets = metrics.get("current_assets")
    current_liabilities = metrics.get("current_liabilities")
    operating_cf = metrics.get("operating_cash_flow")

    ratios: dict[str, Any] = {}

    # Profitability
    ratios["operating_margin"] = safe_div(operating_income, revenue)
    ratios["ordinary_margin"] = safe_div(ordinary_income, revenue)
    ratios["net_margin"] = safe_div(net_income, revenue)
    ratios["roe"] = safe_div(net_income, shareholders_equity)
    ratios["roa"] = safe_div(net_income, total_assets)

    # Safety
    ratios["equity_ratio"] = safe_div(shareholders_equity, total_assets)
    ratios["current_ratio"] = safe_div(current_assets, current_liabilities)
    if total_liabilities is not None and shareholders_equity is not None and shareholders_equity > 0:
        ratios["debt_to_equity"] = total_liabilities / shareholders_equity
    else:
        ratios["debt_to_equity"] = None

    # Efficiency
    ratios["asset_turnover"] = safe_div(revenue, total_assets)

    # Cash flow
    ratios["operating_cf_margin"] = safe_div(operating_cf, revenue)

    # Raw values for display
    ratios["revenue"] = revenue
    ratios["operating_income"] = operating_income
    ratios["net_income"] = net_income
    ratios["total_assets"] = total_assets
    ratios["net_assets"] = net_assets

    return ratios


# Industry average benchmarks (simplified for MVP)
# In production, these would be calculated from actual EDINET data
INDUSTRY_BENCHMARKS: dict[str, dict[str, float]] = {
    "default": {
        "operating_margin": 0.06,
        "roe": 0.08,
        "roa": 0.04,
        "equity_ratio": 0.40,
        "current_ratio": 1.5,
        "asset_turnover": 0.8,
    },
    "製造業": {
        "operating_margin": 0.07,
        "roe": 0.08,
        "roa": 0.04,
        "equity_ratio": 0.45,
        "current_ratio": 1.6,
        "asset_turnover": 0.7,
    },
    "情報・通信業": {
        "operating_margin": 0.12,
        "roe": 0.12,
        "roa": 0.06,
        "equity_ratio": 0.50,
        "current_ratio": 2.0,
        "asset_turnover": 0.9,
    },
    "小売業": {
        "operating_margin": 0.03,
        "roe": 0.08,
        "roa": 0.03,
        "equity_ratio": 0.35,
        "current_ratio": 1.2,
        "asset_turnover": 1.5,
    },
    "サービス業": {
        "operating_margin": 0.08,
        "roe": 0.10,
        "roa": 0.05,
        "equity_ratio": 0.45,
        "current_ratio": 1.5,
        "asset_turnover": 1.0,
    },
}


def get_industry_benchmark(industry: str) -> dict[str, float]:
    """Get benchmark values for an industry."""
    return INDUSTRY_BENCHMARKS.get(industry, INDUSTRY_BENCHMARKS["default"])


def format_metric(value: Optional[float], fmt: str = "percent") -> str:
    """Format a metric value for display.

    Args:
        value: The metric value.
        fmt: Format type - "percent", "ratio", "yen", "times".

    Returns:
        Formatted string.
    """
    if value is None:
        return "N/A"

    if fmt == "percent":
        return f"{value * 100:.1f}%"
    elif fmt == "ratio":
        return f"{value:.2f}"
    elif fmt == "yen":
        if abs(value) >= 1e12:
            return f"{value / 1e12:.1f}兆円"
        elif abs(value) >= 1e8:
            return f"{value / 1e8:.0f}億円"
        elif abs(value) >= 1e4:
            return f"{value / 1e4:.0f}万円"
        return f"{value:.0f}円"
    elif fmt == "times":
        return f"{value:.2f}倍"
    return str(value)
