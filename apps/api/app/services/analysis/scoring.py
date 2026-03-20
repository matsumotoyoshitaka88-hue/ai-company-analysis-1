"""Scoring engine for company diagnosis.

Calculates scores for each dimension and overall composite score.
All scoring is deterministic.
"""
from __future__ import annotations

from typing import Any, Optional

from app.services.analysis.financial import (
    calc_financial_ratios,
    format_metric,
    get_industry_benchmark,
    safe_div,
)


def _score_metric(
    value: Optional[float],
    benchmark: float,
    higher_is_better: bool = True,
    max_score: int = 100,
) -> int:
    """Score a single metric relative to a benchmark.

    Returns 0-100 score.
    """
    if value is None:
        return 50  # Neutral score for missing data

    if higher_is_better:
        ratio = value / benchmark if benchmark != 0 else 1.0
    else:
        ratio = benchmark / value if value != 0 else 1.0

    # Convert ratio to score: 1.0 = benchmark = 60 points, 1.5+ = 90+, 0.5- = 30-
    if ratio >= 1.5:
        score = 90 + min(10, (ratio - 1.5) * 20)
    elif ratio >= 1.0:
        score = 60 + (ratio - 1.0) * 60
    elif ratio >= 0.5:
        score = 30 + (ratio - 0.5) * 60
    else:
        score = max(0, ratio * 60)

    return min(max_score, max(0, int(score)))


def traffic_light(score: int) -> str:
    """Convert a score to traffic light color."""
    if score >= 70:
        return "green"
    elif score >= 40:
        return "yellow"
    return "red"


def traffic_light_label(color: str) -> str:
    """Japanese label for traffic light."""
    return {"green": "良好", "yellow": "注意", "red": "要改善"}.get(color, "不明")


def score_profitability(ratios: dict[str, Any], benchmark: dict[str, float]) -> dict[str, Any]:
    """Score profitability metrics."""
    scores = {
        "operating_margin": _score_metric(ratios.get("operating_margin"), benchmark["operating_margin"]),
        "roe": _score_metric(ratios.get("roe"), benchmark["roe"]),
        "roa": _score_metric(ratios.get("roa"), benchmark["roa"]),
    }
    avg = sum(scores.values()) // len(scores)
    return {
        "score": avg,
        "traffic_light": traffic_light(avg),
        "metrics": [
            {"name": "営業利益率", "value": format_metric(ratios.get("operating_margin")),
             "benchmark": format_metric(benchmark["operating_margin"]), "score": scores["operating_margin"]},
            {"name": "ROE", "value": format_metric(ratios.get("roe")),
             "benchmark": format_metric(benchmark["roe"]), "score": scores["roe"]},
            {"name": "ROA", "value": format_metric(ratios.get("roa")),
             "benchmark": format_metric(benchmark["roa"]), "score": scores["roa"]},
        ],
    }


def score_safety(ratios: dict[str, Any], benchmark: dict[str, float]) -> dict[str, Any]:
    """Score financial safety metrics."""
    scores = {
        "equity_ratio": _score_metric(ratios.get("equity_ratio"), benchmark["equity_ratio"]),
        "current_ratio": _score_metric(ratios.get("current_ratio"), benchmark["current_ratio"]),
        "debt_to_equity": _score_metric(ratios.get("debt_to_equity"), 1.0, higher_is_better=False),
    }
    avg = sum(scores.values()) // len(scores)
    return {
        "score": avg,
        "traffic_light": traffic_light(avg),
        "metrics": [
            {"name": "自己資本比率", "value": format_metric(ratios.get("equity_ratio")),
             "benchmark": format_metric(benchmark["equity_ratio"]), "score": scores["equity_ratio"]},
            {"name": "流動比率", "value": format_metric(ratios.get("current_ratio"), "times"),
             "benchmark": format_metric(benchmark["current_ratio"], "times"), "score": scores["current_ratio"]},
            {"name": "負債資本倍率", "value": format_metric(ratios.get("debt_to_equity"), "times"),
             "benchmark": "1.00倍以下", "score": scores["debt_to_equity"]},
        ],
    }


def score_efficiency(ratios: dict[str, Any], benchmark: dict[str, float]) -> dict[str, Any]:
    """Score efficiency metrics."""
    at_score = _score_metric(ratios.get("asset_turnover"), benchmark["asset_turnover"])
    return {
        "score": at_score,
        "traffic_light": traffic_light(at_score),
        "metrics": [
            {"name": "総資産回転率", "value": format_metric(ratios.get("asset_turnover"), "times"),
             "benchmark": format_metric(benchmark["asset_turnover"], "times"), "score": at_score},
        ],
    }


def score_competitive_position(
    company_ratios: dict[str, Any],
    peer_ratios: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Score competitive position relative to peers."""
    if not peer_ratios:
        return {
            "score": 50,
            "traffic_light": "yellow",
            "peers": [],
            "ranking": [],
        }

    # Compare on key metrics
    metrics_to_compare = ["operating_margin", "roe", "asset_turnover"]
    company_ranks = []

    peers_list = []
    for peer_name, peer_raw in peer_ratios.items():
        peer_calc = calc_financial_ratios(peer_raw)
        peers_list.append({"name": peer_name, "ratios": peer_calc})

    for metric in metrics_to_compare:
        company_val = company_ratios.get(metric)
        if company_val is None:
            company_ranks.append(len(peers_list) // 2 + 1)
            continue

        values = [(company_val, "自社")]
        for p in peers_list:
            pv = p["ratios"].get(metric)
            if pv is not None:
                values.append((pv, p["name"]))

        values.sort(reverse=True)
        rank = next((i + 1 for i, (v, n) in enumerate(values) if n == "自社"), len(values))
        company_ranks.append(rank)

    total_companies = len(peers_list) + 1
    avg_rank = sum(company_ranks) / len(company_ranks) if company_ranks else total_companies / 2

    # Convert rank to score: rank 1 = 95, last = 30
    if total_companies <= 1:
        score = 50
    else:
        score = int(95 - (avg_rank - 1) / (total_companies - 1) * 65)

    return {
        "score": max(0, min(100, score)),
        "traffic_light": traffic_light(score),
        "peers": [{"name": p["name"], "ratios": p["ratios"]} for p in peers_list],
        "ranking": [
            {"metric": m, "rank": r, "total": total_companies}
            for m, r in zip(metrics_to_compare, company_ranks)
        ],
    }


def score_dx_maturity(metrics: dict[str, Any], news_articles: list[dict[str, Any]]) -> dict[str, Any]:
    """Score DX maturity based on available signals.

    For MVP, this is a simplified heuristic based on:
    - IT investment mentions in financial data
    - DX-related keywords in news articles
    """
    score = 50  # Base score

    # Check for DX-related news
    dx_keywords = ["DX", "デジタル", "AI", "クラウド", "IoT", "SaaS", "RPA", "自動化", "データ活用"]
    dx_news_count = 0
    for article in news_articles:
        title = article.get("title", "")
        if any(kw in title for kw in dx_keywords):
            dx_news_count += 1

    if dx_news_count >= 5:
        score = 75
    elif dx_news_count >= 2:
        score = 65
    elif dx_news_count >= 1:
        score = 55

    indicators = [
        {
            "name": "DX関連ニュース",
            "value": f"{dx_news_count}件",
            "status": "green" if dx_news_count >= 3 else "yellow" if dx_news_count >= 1 else "red",
        },
    ]

    return {
        "score": score,
        "traffic_light": traffic_light(score),
        "indicators": indicators,
    }


def calculate_overall_score(
    profitability: dict[str, Any],
    safety: dict[str, Any],
    efficiency: dict[str, Any],
    competitive: dict[str, Any],
    dx: dict[str, Any],
) -> dict[str, Any]:
    """Calculate the overall composite score.

    Weights: Financial 40% (profitability 15%, safety 15%, efficiency 10%),
             Competitive 25%, DX 15%, Risk 20% (derived from safety).
    """
    financial_score = (
        profitability["score"] * 0.15
        + safety["score"] * 0.15
        + efficiency["score"] * 0.10
    ) / 0.40  # Normalize to 0-100

    weighted_score = (
        financial_score * 0.40
        + competitive["score"] * 0.25
        + dx["score"] * 0.15
        + safety["score"] * 0.20  # Risk is inversely related to safety
    )

    score = int(weighted_score)

    return {
        "score": score,
        "traffic_light": traffic_light(score),
    }
