"""PDF renderer - converts report data to a styled PDF using WeasyPrint."""
from __future__ import annotations

import html
from datetime import datetime
from typing import Any

from weasyprint import HTML


def render_pdf(report_data: dict[str, Any]) -> bytes:
    """Render a diagnosis report as a PDF.

    Args:
        report_data: The report_data JSONB from DiagnosisReport.

    Returns:
        PDF file contents as bytes.
    """
    html_content = _build_html(report_data)
    return HTML(string=html_content).write_pdf()


def _esc(text: Any) -> str:
    """Escape HTML entities."""
    return html.escape(str(text)) if text else ""


def _nl2br(text: Any) -> str:
    """Convert newlines to <br> and escape HTML."""
    if not text:
        return ""
    return html.escape(str(text)).replace("\n", "<br>")


def _traffic_light_color(tl: str | None) -> str:
    colors = {"green": "#22c55e", "yellow": "#eab308", "red": "#ef4444"}
    return colors.get(tl or "", "#6b7280")


def _score_bar(score: int | float | None, label: str, tl: str | None = None) -> str:
    s = int(score or 0)
    color = _traffic_light_color(tl) if tl else "#3b82f6"
    return f"""
    <div class="score-row">
      <span class="score-label">{_esc(label)}</span>
      <div class="score-bar-bg">
        <div class="score-bar-fill" style="width:{s}%;background:{color};"></div>
      </div>
      <span class="score-value">{s}点</span>
    </div>"""


def _build_html(data: dict[str, Any]) -> str:
    company = data.get("company", {})
    overall = data.get("overall_score", {})
    sections = data.get("sections", {})
    now = datetime.now().strftime("%Y年%m月%d日")

    # Overall score
    overall_score = overall.get("score", 0)
    overall_tl = overall.get("traffic_light", "")
    tl_color = _traffic_light_color(overall_tl)

    # Financial diagnosis
    fin = sections.get("financial_diagnosis", {})
    profitability = fin.get("profitability", {})
    safety = fin.get("safety", {})
    efficiency = fin.get("efficiency", {})

    # Competitive
    comp = sections.get("competitive_position", {})

    # DX
    dx = sections.get("dx_maturity", {})

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<style>
  @page {{
    size: A4;
    margin: 20mm 15mm;
  }}
  body {{
    font-family: "Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif;
    font-size: 10pt;
    line-height: 1.6;
    color: #1e293b;
  }}
  h1 {{
    font-size: 18pt;
    margin: 0 0 4pt;
    color: #0f172a;
  }}
  h2 {{
    font-size: 13pt;
    color: #1e40af;
    border-bottom: 2px solid #1e40af;
    padding-bottom: 4pt;
    margin-top: 20pt;
  }}
  .header {{
    text-align: center;
    margin-bottom: 16pt;
    padding-bottom: 12pt;
    border-bottom: 1px solid #cbd5e1;
  }}
  .header .date {{
    font-size: 9pt;
    color: #64748b;
  }}
  .header .subtitle {{
    font-size: 10pt;
    color: #64748b;
    margin-top: 2pt;
  }}
  .overall-box {{
    text-align: center;
    padding: 16pt;
    margin: 12pt 0;
    border: 2px solid {tl_color};
    border-radius: 8pt;
  }}
  .overall-score {{
    font-size: 36pt;
    font-weight: bold;
    color: {tl_color};
  }}
  .overall-summary {{
    margin-top: 8pt;
    font-size: 10pt;
    color: #475569;
  }}
  .score-row {{
    display: flex;
    align-items: center;
    margin: 6pt 0;
  }}
  .score-label {{
    width: 100pt;
    font-weight: bold;
    font-size: 9pt;
  }}
  .score-bar-bg {{
    flex: 1;
    height: 10pt;
    background: #e2e8f0;
    border-radius: 5pt;
    overflow: hidden;
  }}
  .score-bar-fill {{
    height: 100%;
    border-radius: 5pt;
  }}
  .score-value {{
    width: 40pt;
    text-align: right;
    font-size: 9pt;
    font-weight: bold;
  }}
  .narrative {{
    margin: 8pt 0;
    text-align: justify;
  }}
  .footer {{
    margin-top: 24pt;
    padding-top: 8pt;
    border-top: 1px solid #cbd5e1;
    font-size: 8pt;
    color: #94a3b8;
    text-align: center;
  }}
  .peer-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 8pt 0;
    font-size: 9pt;
  }}
  .peer-table th, .peer-table td {{
    border: 1px solid #cbd5e1;
    padding: 4pt 8pt;
    text-align: left;
  }}
  .peer-table th {{
    background: #f1f5f9;
    font-weight: bold;
  }}
</style>
</head>
<body>

<div class="header">
  <h1>{_esc(company.get('name', ''))} 経営診断レポート</h1>
  <div class="subtitle">業種: {_esc(company.get('industry', ''))}</div>
  <div class="date">生成日: {now}</div>
</div>

<div class="overall-box">
  <div class="overall-score">{overall_score}<span style="font-size:14pt">点</span></div>
  <div class="overall-summary">{_nl2br(overall.get('summary_text', ''))}</div>
</div>

<h2>エグゼクティブサマリー</h2>
<div class="narrative">{_nl2br(sections.get('executive_summary', {}).get('content', ''))}</div>

<h2>財務診断</h2>
{_score_bar(profitability.get('score'), '収益性', profitability.get('traffic_light'))}
{_score_bar(safety.get('score'), '安全性', safety.get('traffic_light'))}
{_score_bar(efficiency.get('score'), '効率性', efficiency.get('traffic_light'))}
<div class="narrative">{_nl2br(fin.get('narrative', ''))}</div>

<h2>競争力分析</h2>
{_score_bar(comp.get('score'), '競争力', comp.get('traffic_light'))}
{_build_peer_table(comp.get('ranking', []))}
<div class="narrative">{_nl2br(comp.get('narrative', ''))}</div>

<h2>DX成熟度</h2>
{_score_bar(dx.get('score'), 'DX成熟度', dx.get('traffic_light'))}
<div class="narrative">{_nl2br(dx.get('narrative', ''))}</div>

<h2>リスクと機会</h2>
<div class="narrative">{_nl2br(sections.get('risk_opportunity', {}).get('narrative', ''))}</div>

<div class="footer">
  本レポートは公開情報に基づく自動分析結果です。投資判断等の最終的な意思決定は、ご自身の責任にてお願いいたします。
</div>

</body>
</html>"""


def _build_peer_table(ranking: list[dict[str, Any]]) -> str:
    if not ranking:
        return ""
    rows = ""
    for r in ranking:
        rows += f"""<tr>
          <td>{_esc(r.get('name', ''))}</td>
          <td>{_esc(r.get('score', ''))}</td>
          <td>{_esc(r.get('revenue', ''))}</td>
        </tr>"""
    return f"""<table class="peer-table">
      <thead><tr><th>企業名</th><th>スコア</th><th>売上高</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""
