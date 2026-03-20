"""Tests for financial analysis and scoring."""
from app.services.analysis.financial import calc_financial_ratios, format_metric, safe_div
from app.services.analysis.scoring import (
    calculate_overall_score,
    score_efficiency,
    score_profitability,
    score_safety,
    traffic_light,
)


def test_safe_div():
    assert safe_div(10, 2) == 5.0
    assert safe_div(None, 2) is None
    assert safe_div(10, 0) is None
    assert safe_div(10, None) is None


def test_calc_financial_ratios():
    metrics = {
        "revenue": 1_000_000,
        "operating_income": 100_000,
        "net_income": 60_000,
        "total_assets": 2_000_000,
        "net_assets": 800_000,
        "current_assets": 500_000,
        "current_liabilities": 300_000,
    }
    ratios = calc_financial_ratios(metrics)

    assert ratios["operating_margin"] == 0.1  # 10%
    assert ratios["net_margin"] == 0.06  # 6%
    assert ratios["roe"] == 60_000 / 800_000
    assert ratios["roa"] == 60_000 / 2_000_000
    assert ratios["equity_ratio"] == 0.4
    assert ratios["asset_turnover"] == 0.5
    assert abs(ratios["current_ratio"] - 5 / 3) < 0.001


def test_traffic_light():
    assert traffic_light(80) == "green"
    assert traffic_light(70) == "green"
    assert traffic_light(69) == "yellow"
    assert traffic_light(40) == "yellow"
    assert traffic_light(39) == "red"
    assert traffic_light(0) == "red"


def test_score_profitability():
    ratios = {
        "operating_margin": 0.10,
        "roe": 0.12,
        "roa": 0.06,
    }
    benchmark = {
        "operating_margin": 0.06,
        "roe": 0.08,
        "roa": 0.04,
    }
    result = score_profitability(ratios, benchmark)

    assert "score" in result
    assert "traffic_light" in result
    assert "metrics" in result
    assert result["score"] > 60  # Above benchmark = above 60


def test_score_safety():
    ratios = {
        "equity_ratio": 0.50,
        "current_ratio": 2.0,
        "debt_to_equity": 0.5,
    }
    benchmark = {
        "equity_ratio": 0.40,
        "current_ratio": 1.5,
    }
    result = score_safety(ratios, benchmark)

    assert result["score"] > 60


def test_format_metric():
    assert format_metric(0.1) == "10.0%"
    assert format_metric(None) == "N/A"
    assert format_metric(1_500_000_000_000, "yen") == "1.5兆円"
    assert format_metric(50_000_000_000, "yen") == "500億円"
    assert format_metric(1.5, "times") == "1.50倍"


def test_overall_score():
    profitability = {"score": 70, "traffic_light": "green"}
    safety = {"score": 60, "traffic_light": "yellow"}
    efficiency = {"score": 50, "traffic_light": "yellow"}
    competitive = {"score": 65, "traffic_light": "yellow"}
    dx = {"score": 55, "traffic_light": "yellow"}

    result = calculate_overall_score(profitability, safety, efficiency, competitive, dx)

    assert 0 <= result["score"] <= 100
    assert result["traffic_light"] in ("green", "yellow", "red")
