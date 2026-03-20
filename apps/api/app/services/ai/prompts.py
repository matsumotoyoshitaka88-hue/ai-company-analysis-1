"""Prompt templates for AI report generation.

Each section has its own prompt with structured data context.
Claude receives pre-computed metrics and generates narrative only.
"""
from __future__ import annotations

from typing import Any

from app.services.analysis.financial import format_metric


SYSTEM_PROMPT = """あなたは企業分析の専門家です。提供された財務データと分析結果に基づいて、
経営者向けの分かりやすい診断レポートを日本語で作成してください。

重要なルール:
- 提供されたデータのみを使用してください。データにない情報を推測で補わないでください。
- 財務数値は提供された値をそのまま使用してください。計算や推定は行わないでください。
- 専門用語には簡単な説明を添えてください。
- 結論や評価は明確にしてください。
"""


def build_executive_summary_prompt(
    company_name: str,
    overall_score: dict[str, Any],
    profitability: dict[str, Any],
    safety: dict[str, Any],
    competitive: dict[str, Any],
    dx: dict[str, Any],
    news_summary: str,
) -> str:
    """Build prompt for executive summary section."""
    return f"""以下の企業診断データに基づいて、エグゼクティブサマリーを作成してください。
経営者が1分で全体像を把握できる内容にしてください。

## 企業: {company_name}

## 総合スコア: {overall_score['score']}/100 ({_tl_label(overall_score['traffic_light'])})

## 各領域スコア
- 収益性: {profitability['score']}/100 ({_tl_label(profitability['traffic_light'])})
- 安全性: {safety['score']}/100 ({_tl_label(safety['traffic_light'])})
- 競合ポジション: {competitive['score']}/100 ({_tl_label(competitive['traffic_light'])})
- DX成熟度: {dx['score']}/100 ({_tl_label(dx['traffic_light'])})

## 直近ニュース概要
{news_summary}

## 出力形式
3-5段落で以下を含めてください:
1. 総合的な経営状態の評価（1-2文）
2. 強みとなっている領域
3. 改善が必要な領域
4. 注目すべき動向（ニュースから）
5. 今後の展望（1-2文）
"""


def build_financial_diagnosis_prompt(
    company_name: str,
    ratios: dict[str, Any],
    profitability: dict[str, Any],
    safety: dict[str, Any],
    efficiency: dict[str, Any],
    industry: str,
) -> str:
    """Build prompt for financial diagnosis section."""
    metrics_text = _format_metrics_for_prompt(profitability, safety, efficiency)

    return f"""以下の財務データに基づいて、財務診断の詳細レポートを作成してください。

## 企業: {company_name}
## 業種: {industry}

## 主要財務指標
- 売上高: {format_metric(ratios.get('revenue'), 'yen')}
- 営業利益: {format_metric(ratios.get('operating_income'), 'yen')}
- 純利益: {format_metric(ratios.get('net_income'), 'yen')}
- 総資産: {format_metric(ratios.get('total_assets'), 'yen')}
- 純資産: {format_metric(ratios.get('net_assets'), 'yen')}

## スコアリング結果
{metrics_text}

## 出力形式
以下の3セクションで詳細に分析してください:

### 収益性分析
営業利益率・ROE・ROAの分析と業界比較での位置づけ

### 安全性分析
自己資本比率・流動比率の分析と財務リスクの評価

### 効率性分析
資産活用の効率性の評価
"""


def build_competitive_position_prompt(
    company_name: str,
    company_ratios: dict[str, Any],
    competitive_data: dict[str, Any],
) -> str:
    """Build prompt for competitive position section."""
    peers_text = ""
    for peer in competitive_data.get("peers", []):
        ratios = peer.get("ratios", {})
        peers_text += f"\n- {peer['name']}: 営業利益率 {format_metric(ratios.get('operating_margin'))}, ROE {format_metric(ratios.get('roe'))}"

    ranking_text = ""
    for r in competitive_data.get("ranking", []):
        ranking_text += f"\n- {r['metric']}: {r['rank']}位/{r['total']}社中"

    return f"""以下のデータに基づいて、競合ポジション分析を作成してください。

## 企業: {company_name}
## 自社指標
- 営業利益率: {format_metric(company_ratios.get('operating_margin'))}
- ROE: {format_metric(company_ratios.get('roe'))}
- 総資産回転率: {format_metric(company_ratios.get('asset_turnover'), 'times')}

## 同業他社{peers_text if peers_text else '（データなし）'}

## ランキング{ranking_text if ranking_text else '（データなし）'}

## 出力形式
1. 業界内での総合的なポジション評価
2. 競合と比較した強み・弱み
3. 差別化のポイント（推測ではなくデータに基づく）
"""


def build_dx_maturity_prompt(
    company_name: str,
    dx_data: dict[str, Any],
    news_summary: str,
) -> str:
    """Build prompt for DX maturity section."""
    indicators_text = ""
    for ind in dx_data.get("indicators", []):
        indicators_text += f"\n- {ind['name']}: {ind['value']} ({ind['status']})"

    return f"""以下のデータに基づいて、DX成熟度の評価を作成してください。

## 企業: {company_name}
## DXスコア: {dx_data['score']}/100

## DX指標{indicators_text}

## 関連ニュース
{news_summary}

## 出力形式
1. 現在のDX推進状況の評価
2. DX関連の取り組み（ニュースから確認できるもの）
3. DX推進に向けた示唆（具体的かつ実行可能なもの）

注意: データが限られている場合は、その旨を明記した上で、公開情報から読み取れる範囲で評価してください。
"""


def build_risk_opportunity_prompt(
    company_name: str,
    overall_score: dict[str, Any],
    profitability: dict[str, Any],
    safety: dict[str, Any],
    competitive: dict[str, Any],
    news_summary: str,
    industry: str,
) -> str:
    """Build prompt for risk and opportunity analysis."""
    return f"""以下のデータに基づいて、リスクと機会の分析を作成してください。

## 企業: {company_name}
## 業種: {industry}
## 総合スコア: {overall_score['score']}/100

## 各領域スコア
- 収益性: {profitability['score']}/100
- 安全性: {safety['score']}/100
- 競合ポジション: {competitive['score']}/100

## 直近ニュース
{news_summary}

## 出力形式
### 主要リスク
3-5項目のリスクを重要度順にリストアップ。各項目に:
- リスクの内容
- 影響度（高/中/低）
- 対応の方向性

### 成長機会
3-5項目の機会を期待度順にリストアップ。各項目に:
- 機会の内容
- 期待度（高/中/低）
- 活用の方向性
"""


def _tl_label(color: str) -> str:
    return {"green": "良好", "yellow": "注意", "red": "要改善"}.get(color, "不明")


def _format_metrics_for_prompt(
    profitability: dict[str, Any],
    safety: dict[str, Any],
    efficiency: dict[str, Any],
) -> str:
    """Format scoring results into text for prompts."""
    lines = ["### 収益性"]
    for m in profitability.get("metrics", []):
        lines.append(f"- {m['name']}: {m['value']}（業界平均: {m['benchmark']}、スコア: {m['score']}/100）")

    lines.append("\n### 安全性")
    for m in safety.get("metrics", []):
        lines.append(f"- {m['name']}: {m['value']}（基準: {m['benchmark']}、スコア: {m['score']}/100）")

    lines.append("\n### 効率性")
    for m in efficiency.get("metrics", []):
        lines.append(f"- {m['name']}: {m['value']}（業界平均: {m['benchmark']}、スコア: {m['score']}/100）")

    return "\n".join(lines)
