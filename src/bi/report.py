"""
Module: bi.report
Purpose:
    Build a standalone, self-contained HTML report that depicts the outcome of
    the pipeline project: business KPIs, trends, product/regional/customer
    performance, data-quality scores, pipeline health, lineage, and the list of
    BI deliverables.

    The report uses no external CSS, JavaScript, fonts, or chart libraries. It
    can be opened directly from disk, served by the FastAPI app, printed to PDF,
    or attached to a project submission.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import pandas as pd

from src.bi.exporter import (
    DEFAULT_OUTPUT_DIR,
    compute_kpis,
)
from src.utils.file_utils import ensure_directory, get_project_root
from src.utils.logger import get_logger

logger = get_logger("bi.report")

DEFAULT_REPORT_PATH = get_project_root() / "dashboard" / "reports" / "project_outcome.html"

# Mapping of export filename prefixes to the logical dataset names used by the
# KPI functions.
_PREFIXES = ("analytics_", "monitoring_", "metadata_")


def _read_csv(path: Path) -> Optional[pd.DataFrame]:
    try:
        if not path.exists():
            return None
        return pd.read_csv(path)
    except Exception as exc:
        logger.warning("Could not read %s: %s", path, exc)
        return None


def _fmt_int(value: Any) -> str:
    try:
        return f"{int(round(float(value))):,}"
    except (TypeError, ValueError):
        return "0"


def _fmt_money(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "₹0"
    if number >= 1_00_00_000:
        return f"₹{number / 1_00_00_000:,.2f} Cr"
    if number >= 1_00_000:
        return f"₹{number / 1_00_000:,.2f} L"
    return f"₹{number:,.0f}"


def _fmt_pct(value: Any, digits: int = 1) -> str:
    try:
        return f"{float(value):.{digits}f}%"
    except (TypeError, ValueError):
        return "n/a"


def _fmt_score(value: Any) -> str:
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return "n/a"


def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _short_date(value: Any) -> str:
    text = str(value)
    return text[:10] if len(text) >= 10 else text


def _empty_state(message: str = "No data available for this section.") -> str:
    return f'<div class="empty">{_esc(message)}</div>'


def _line_chart(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    width: int = 960,
    height: int = 300,
    color: str = "#3f5b73",
) -> str:
    """Render a compact responsive SVG line chart."""
    points: List[Tuple[float, float]] = []
    clean: List[Tuple[str, float]] = []
    for label, value in zip(labels, values):
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = 0.0
        clean.append((str(label), number))

    if not clean:
        return _empty_state()

    max_value = max(value for _, value in clean) or 1.0
    pad_left, pad_right, pad_top, pad_bottom = 64, 20, 18, 42
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom
    count = len(clean)
    step = plot_w / max(count - 1, 1)

    for index, (_, value) in enumerate(clean):
        x = pad_left + index * step
        y = pad_top + plot_h - (value / max_value) * plot_h
        points.append((x, y))

    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)

    grid = []
    for tick in range(5):
        ratio = tick / 4
        y = pad_top + plot_h - ratio * plot_h
        tick_value = max_value * ratio
        grid.append(
            f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - pad_right}" y2="{y:.1f}" '
            'stroke="#e3e6e9" stroke-width="1"/>'
            f'<text x="{pad_left - 10}" y="{y + 4:.1f}" text-anchor="end" '
            f'class="chart-axis">{_esc(_fmt_money(tick_value))}</text>'
        )

    tick_indexes = sorted({0, count // 4, count // 2, (3 * count) // 4, count - 1})
    x_labels = []
    for index in tick_indexes:
        x = pad_left + index * step
        x_labels.append(
            f'<text x="{x:.1f}" y="{height - 16}" text-anchor="middle" class="chart-axis">'
            f"{_esc(_short_date(clean[index][0]))}</text>"
        )

    markers = []
    marker_step = max(1, count // 24)
    for index, (x, y) in enumerate(points):
        if index % marker_step == 0 or index == count - 1:
            label, value = clean[index]
            markers.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="{color}">'
                f"<title>{_esc(label)}: {_esc(_fmt_money(value))}</title></circle>"
            )

    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Daily revenue trend" class="chart">'
        + "".join(grid)
        + f'<polyline points="{polyline}" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
        + "".join(markers)
        + "".join(x_labels)
        + "</svg>"
    )


def _bar_chart(
    items: Sequence[Tuple[str, float]],
    *,
    width: int = 620,
    color: str = "#3f5b73",
    value_formatter=_fmt_money,
) -> str:
    """Render horizontal bars with labels and values as an inline SVG."""
    if not items:
        return _empty_state()

    label_width = 168
    value_width = 92
    bar_height = 24
    gap = 14
    top = 8
    height = top + len(items) * (bar_height + gap) + 6
    plot_width = width - label_width - value_width
    max_value = max(float(value) for _, value in items) or 1.0

    rows = []
    for index, (label, value) in enumerate(items):
        y = top + index * (bar_height + gap)
        bar_width = max(2.0, (float(value) / max_value) * plot_width)
        display_label = label if len(str(label)) <= 22 else f"{str(label)[:21]}…"
        rows.append(
            f'<text x="0" y="{y + 17}" class="bar-label">{_esc(display_label)}</text>'
            f'<rect x="{label_width}" y="{y}" width="{plot_width}" height="{bar_height}" '
            'rx="3" fill="#eceff1"/>'
            f'<rect x="{label_width}" y="{y}" width="{bar_width:.1f}" height="{bar_height}" '
            f'rx="3" fill="{color}">'
            f"<title>{_esc(label)}: {_esc(value_formatter(value))}</title></rect>"
            f'<text x="{width - 4}" y="{y + 17}" text-anchor="end" class="bar-value">'
            f"{_esc(value_formatter(value))}</text>"
        )

    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Horizontal bar chart" '
        f'style="width:100%;height:auto">{_join(rows)}</svg>'
    )


def _join(parts: Iterable[str]) -> str:
    return "".join(parts)


def _table(
    headers: Sequence[str],
    rows: Sequence[Sequence[Any]],
    *,
    numeric_columns: Sequence[int] = (),
    html_columns: Sequence[int] = (),
    class_name: str = "data-table",
) -> str:
    if not rows:
        return _empty_state()
    head = "".join(f"<th>{_esc(header)}</th>" for header in headers)
    body_rows = []
    for row in rows:
        cells = []
        for index, value in enumerate(row):
            css = ' class="num"' if index in numeric_columns else ""
            rendered = str(value) if index in html_columns else _esc(value)
            cells.append(f"<td{css}>{rendered}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    return (
        f'<div class="table-wrap"><table class="{class_name}"><thead><tr>{head}</tr></thead>'
        f"<tbody>{''.join(body_rows)}</tbody></table></div>"
    )


def _quality_bars(quality: Mapping[str, Any]) -> str:
    labels = [
        ("Freshness", quality.get("freshness")),
        ("Completeness", quality.get("completeness")),
        ("Accuracy", quality.get("accuracy")),
        ("Contract adherence", quality.get("contract_adherence")),
    ]
    if all(value is None for _, value in labels):
        return _empty_state("No quality metrics have been recorded yet.")

    parts = []
    for label, value in labels:
        score = 0.0 if value is None else max(0.0, min(100.0, float(value)))
        tone = "good" if score >= 95 else "warn" if score >= 80 else "bad"
        parts.append(
            f'<div class="meter-row"><span class="meter-label">{_esc(label)}</span>'
            f'<div class="meter-track"><div class="meter-fill {tone}" style="width:{score:.1f}%"></div></div>'
            f'<span class="meter-value">{_fmt_score(value)}</span></div>'
        )
    return "".join(parts)


class OutcomeReportBuilder:
    """Generate the standalone project outcome report from BI exports."""

    def __init__(self, exports_dir: Optional[Path | str] = None):
        self.exports_dir = Path(exports_dir) if exports_dir else DEFAULT_OUTPUT_DIR

    # ── Loading ─────────────────────────────────────────────

    def _load_manifest(self) -> Dict[str, Any]:
        path = self.exports_dir / "manifest.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Could not parse manifest: %s", exc)
            return {}

    def _load_frames(self) -> Dict[str, pd.DataFrame]:
        frames: Dict[str, pd.DataFrame] = {}
        for prefix in _PREFIXES:
            for path in sorted(self.exports_dir.glob(f"{prefix}*.csv")):
                name = path.stem[len(prefix):]
                frame = _read_csv(path)
                if frame is not None:
                    frames[name] = frame
        return frames

    def _load_kpis(self, frames: Mapping[str, pd.DataFrame]) -> Dict[str, Any]:
        path = self.exports_dir / "kpi_summary.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("Could not parse KPI summary: %s", exc)
        return compute_kpis(frames)

    # ── Public API ──────────────────────────────────────────

    def build(self) -> str:
        """Return the complete HTML report as a string."""
        frames = self._load_frames()
        kpis = self._load_kpis(frames)
        manifest = self._load_manifest()
        return self._render(frames, kpis, manifest)

    def write(self, output_path: Optional[Path | str] = None) -> Path:
        """Write the report to disk and return its path."""
        target = Path(output_path) if output_path else DEFAULT_REPORT_PATH
        ensure_directory(target.parent)
        target.write_text(self.build(), encoding="utf-8")
        logger.info("Project outcome report written to %s", target)
        return target

    # ── Rendering ───────────────────────────────────────────

    def _render(
        self,
        frames: Mapping[str, pd.DataFrame],
        kpis: Mapping[str, Any],
        manifest: Mapping[str, Any],
    ) -> str:
        daily = frames.get("v_daily_sales")
        products = frames.get("v_product_performance")
        regions = frames.get("v_regional_analysis")
        customers = frames.get("v_customer_segments")
        quality_metrics = frames.get("batch_quality_metrics")
        pipelines = frames.get("pipeline_metrics")
        alerts = frames.get("alert_log")

        generated_at = str(kpis.get("generated_at") or manifest.get("generated_at") or "")
        backend = str(kpis.get("backend") or manifest.get("backend") or "unknown")
        date_range = kpis.get("date_range") or {}
        quality = kpis.get("quality") or {}
        pipeline = kpis.get("pipeline") or {}

        summary = self._summary_text(kpis)
        overview_cards = self._kpi_cards(kpis)
        daily_section = self._daily_section(daily)
        monthly_section = self._monthly_section(daily)
        product_section = self._product_section(products)
        region_section = self._region_section(regions)
        customer_section = self._customer_section(customers)
        quality_section = self._quality_section(quality, quality_metrics, alerts)
        pipeline_section = self._pipeline_section(pipeline, pipelines)
        warehouse_section = self._warehouse_section(kpis, manifest)
        deliverables_section = self._deliverables_section(manifest)
        process_section = self._process_section()

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Project Outcome Report — Automated Data Pipeline &amp; BI Architecture</title>
<style>
  :root {{
    --ink: #1f2933;
    --muted: #5c6672;
    --line: #d8dde3;
    --card: #ffffff;
    --bg: #f4f5f7;
    --brand: #3f5b73;
    --brand-dark: #2b3f51;
    --accent: #5f7a8a;
    --good: #2f6b4f;
    --warn: #8a6a2f;
    --bad: #a14545;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif;
    font-size: 15px;
    line-height: 1.55;
  }}
  .page {{ max-width: 1180px; margin: 0 auto; padding: 28px 22px 60px; }}
  header.hero {{
    background: var(--card);
    color: var(--ink);
    border: 1px solid var(--line);
    border-top: 4px solid var(--brand);
    border-radius: 10px;
    padding: 30px 34px;
  }}
  header.hero h1 {{ margin: 0 0 8px; font-size: 28px; letter-spacing: -0.3px; color: var(--ink); }}
  header.hero p {{ margin: 0; color: var(--muted); max-width: 820px; }}
  .hero-meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }}
  .pill {{
    display: inline-flex; align-items: center; gap: 6px;
    background: #f8f9fa; border: 1px solid var(--line);
    color: #3f4a56; padding: 5px 10px; border-radius: 6px; font-size: 12.5px;
  }}
  .dot {{ width: 7px; height: 7px; border-radius: 50%; background: var(--good); display: inline-block; }}
  h2 {{ font-size: 19px; margin: 34px 0 14px; letter-spacing: -0.2px; }}
  h2 .num {{
    display: inline-flex; width: 26px; height: 26px; border-radius: 6px;
    background: #eef1f4; color: var(--brand); font-size: 13px;
    align-items: center; justify-content: center; margin-right: 9px; vertical-align: 2px;
  }}
  .grid {{ display: grid; gap: 16px; }}
  .grid.kpi {{ grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); }}
  .grid.two {{ grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); }}
  .card {{
    background: var(--card); border: 1px solid var(--line); border-radius: 8px;
    padding: 18px 20px;
  }}
  .kpi-card {{ position: relative; overflow: hidden; }}
  .kpi-card::after {{
    content: ""; position: absolute; inset: 0 auto 0 0; width: 3px;
    background: var(--brand);
  }}
  .kpi-label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .6px; }}
  .kpi-value {{ font-size: 25px; font-weight: 700; margin-top: 4px; letter-spacing: -0.4px; }}
  .kpi-sub {{ color: var(--muted); font-size: 12.5px; margin-top: 3px; }}
  .summary {{
    background: #f8f9fa; border: 1px solid var(--line); border-left: 4px solid var(--brand);
    border-radius: 8px; padding: 18px 22px; color: var(--ink);
  }}
  .summary strong {{ color: var(--brand-dark); }}
  .chart {{ width: 100%; height: auto; display: block; }}
  .chart-axis {{ fill: #7a838e; font-size: 11px; }}
  .bar-label {{ fill: #3f4a56; font-size: 12.5px; }}
  .bar-value {{ fill: var(--ink); font-size: 12.5px; font-weight: 600; }}
  .section-note {{ color: var(--muted); font-size: 13px; margin: -6px 0 12px; }}
  .empty {{
    padding: 22px; border: 1px dashed #c3cbd3; border-radius: 8px;
    color: var(--muted); text-align: center; background: #f8f9fa;
  }}
  .table-wrap {{ overflow-x: auto; }}
  table.data-table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
  table.data-table th {{
    text-align: left; font-size: 11.5px; text-transform: uppercase; letter-spacing: .5px;
    color: var(--muted); border-bottom: 2px solid var(--line); padding: 8px 10px;
  }}
  table.data-table td {{ padding: 8px 10px; border-bottom: 1px solid #eceff1; }}
  table.data-table tr:hover td {{ background: #f8f9fa; }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .badge {{
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 11.5px; font-weight: 600; letter-spacing: .2px;
  }}
  .badge.success {{ background: #edf4f0; color: var(--good); }}
  .badge.failed {{ background: #f7eded; color: var(--bad); }}
  .badge.running {{ background: #f6f1e7; color: var(--warn); }}
  .meter-row {{ display: grid; grid-template-columns: 150px 1fr 52px; gap: 10px; align-items: center; margin: 10px 0; }}
  .meter-label {{ color: #3f4a56; font-size: 13px; }}
  .meter-track {{ height: 8px; border-radius: 4px; background: #e8ebee; overflow: hidden; }}
  .meter-fill {{ height: 100%; border-radius: 4px; }}
  .meter-fill.good {{ background: var(--good); }}
  .meter-fill.warn {{ background: var(--warn); }}
  .meter-fill.bad {{ background: var(--bad); }}
  .meter-value {{ text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }}
  .flow {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: stretch; margin: 6px 0 4px; }}
  .flow-step {{
    flex: 1 1 135px; background: #f8f9fa; border: 1px solid var(--line);
    border-radius: 6px; padding: 11px 12px; position: relative;
  }}
  .flow-step .step-name {{ font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .4px; }}
  .flow-step .step-count {{ font-size: 19px; font-weight: 700; margin-top: 2px; }}
  .flow-arrow {{ align-self: center; color: #9aa3ac; font-size: 18px; }}
  ul.clean {{ margin: 8px 0 0; padding-left: 20px; }}
  ul.clean li {{ margin: 5px 0; }}
  .callout {{ border-radius: 8px; padding: 16px 18px; border: 1px solid var(--line); background: #f8f9fa; color: #3f4a56; }}
  .callout h3 {{ margin: 0 0 6px; font-size: 14px; text-transform: uppercase; letter-spacing: .5px; }}
  .callout ul {{ margin: 0; padding-left: 18px; }}
  footer {{ margin-top: 36px; padding-top: 16px; border-top: 1px solid var(--line); color: var(--muted); font-size: 12.5px; }}
  .two-col {{ display: grid; grid-template-columns: 1.15fr .85fr; gap: 16px; }}
  @media (max-width: 900px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
  @media print {{
    body {{ background: #fff; font-size: 12px; }}
    .page {{ max-width: none; padding: 0; }}
    header.hero {{ border-radius: 0; }}
    .card {{ break-inside: avoid; }}
    h2 {{ break-after: avoid; }}
    a {{ color: inherit; text-decoration: none; }}
  }}
</style>
</head>
<body>
<div class="page">

  <header class="hero">
    <h1>Project Outcome Report</h1>
    <p>Automated End-to-End Data Pipeline &amp; BI Architecture — a verified view of business
    performance, data quality, pipeline health, and the analytical deliverables produced by the
    ETLT++ / ELTL++ lakehouse.</p>
    <div class="hero-meta">
      <span class="pill"><span class="dot"></span>Warehouse: {_esc(backend)}</span>
      <span class="pill">Data window: {_esc(date_range.get("start") or "n/a")} → {_esc(date_range.get("end") or "n/a")}</span>
      <span class="pill">Generated: {_esc(generated_at or "n/a")}</span>
      <span class="pill">Deliverables: {_esc(len(manifest.get("datasets", [])))} datasets</span>
    </div>
  </header>

  <h2><span class="num">1</span>Executive Summary</h2>
  <div class="summary">{summary}</div>
  <div class="grid kpi" style="margin-top:16px">{overview_cards}</div>

  <h2><span class="num">2</span>Revenue and Demand Trend</h2>
  <div class="two-col">
    <div class="card">
      <h3 style="margin:0 0 4px;font-size:15px">Daily revenue</h3>
      <p class="section-note">Total transaction value per calendar day from <code>analytics.v_daily_sales</code>.</p>
      {daily_section}
    </div>
    <div class="card">
      <h3 style="margin:0 0 4px;font-size:15px">Monthly revenue</h3>
      <p class="section-note">Daily sales rolled up to calendar month.</p>
      {monthly_section}
    </div>
  </div>

  <h2><span class="num">3</span>Product Performance</h2>
  <div class="card">
    <p class="section-note">Revenue by product (top 10) with the underlying product table.</p>
    {product_section}
  </div>

  <h2><span class="num">4</span>Regional Performance</h2>
  <div class="card">
    <p class="section-note">Revenue by region from <code>analytics.v_regional_analysis</code>.</p>
    {region_section}
  </div>

  <h2><span class="num">5</span>Customer Segments</h2>
  <div class="card">
    <p class="section-note">Spend concentration by segment and the highest-value customers.</p>
    {customer_section}
  </div>

  <h2><span class="num">6</span>Data Quality and Pipeline Health</h2>
  <div class="two-col">
    <div class="card">
      <h3 style="margin:0 0 4px;font-size:15px">Quality scorecard</h3>
      <p class="section-note">Average of recorded batch scores (0–100).</p>
      {quality_section}
    </div>
    <div class="card">
      <h3 style="margin:0 0 4px;font-size:15px">Execution history</h3>
      <p class="section-note">Latest pipeline runs and outcome.</p>
      {pipeline_section}
    </div>
  </div>

  <h2><span class="num">7</span>Warehouse and Lineage</h2>
  <div class="card">
    <p class="section-note">End-to-end flow with observed record counts from this run.</p>
    {warehouse_section}
  </div>

  <h2><span class="num">8</span>BI Deliverables</h2>
  <div class="card">
    <p class="section-note">Every CSV below is a curated, BI-ready extract. Open the report from
    <code>dashboard/reports/</code> or from the API to download the files.</p>
    {deliverables_section}
  </div>

  <h2><span class="num">9</span>How This Outcome Was Produced</h2>
  <div class="card">{process_section}</div>

  <h2><span class="num">10</span>Conclusions and Scope</h2>
  <div class="card">
    <ul class="clean">
      <li>The pipeline produces a complete, queryable star schema and five analytical views from
      raw transaction files, with contract validation, quarantine, SCD Type-2 history, and lineage.</li>
      <li>Business performance is reproducible from the exported extracts; the KPI summary is the
      single source of truth for headline numbers used in this report.</li>
      <li>Data quality and pipeline health are evidenced by persisted monitoring tables, not by
      static claims in documentation.</li>
      <li>The deliverables are intentionally tool-agnostic. Power BI and Tableau can bind to the
      CSV extracts (or the PostgreSQL analytics views when available) using the instructions in
      <code>dashboard/README.md</code>.</li>
    </ul>
    <div class="callout" style="margin-top:16px">
      <h3>Scope and limitations</h3>
      <ul>
        <li>This build ran against the <strong>{_esc(backend)}</strong> warehouse backend. When PostgreSQL is
        available, the same views and exports are used without code changes.</li>
        <li>Power BI (<code>.pbix</code>) and Tableau (<code>.twbx</code>) binaries are not shipped; the
        CSV extracts, field documentation, and connection guides are the portable substitutes.</li>
        <li>All monetary values are shown in Indian Rupees (₹) because the sample dataset is
        India-based. The pipeline itself is currency-agnostic.</li>
      </ul>
    </div>
  </div>

  <footer>
    Generated by <code>scripts/generate_project_report.py</code> from
    <code>{_esc(self.exports_dir)}</code>. No external chart library or network connection is required.
  </footer>
</div>
</body>
</html>
"""

    # ── Section builders ────────────────────────────────────

    def _summary_text(self, kpis: Mapping[str, Any]) -> str:
        date_range = kpis.get("date_range") or {}
        start = date_range.get("start") or "the start of the dataset"
        end = date_range.get("end") or "the latest available date"
        top_product = kpis.get("top_product") or {}
        top_region = kpis.get("top_region") or {}
        pipeline = kpis.get("pipeline") or {}
        quality = kpis.get("quality") or {}

        product_text = (
            f"<strong>{_esc(top_product.get('label'))}</strong> was the leading product at "
            f"{_esc(_fmt_money(top_product.get('value')))} in revenue"
            if top_product
            else "Product-level revenue could not be derived"
        )
        region_text = (
            f"<strong>{_esc(top_region.get('label'))}</strong> was the strongest region"
            if top_region
            else "regional performance is unavailable"
        )
        success_rate = pipeline.get("success_rate")
        pipeline_text = (
            f"{_esc(_fmt_pct(success_rate))} of {_esc(pipeline.get('total', 0))} recorded executions succeeded"
            if success_rate is not None
            else "pipeline execution history is not yet available"
        )
        quality_text = (
            f"the average quality score was <strong>{_esc(_fmt_score(quality.get('overall')))} / 100</strong>"
            if quality.get("overall") is not None
            else "quality scoring has not been recorded"
        )

        return (
            f"Between <strong>{_esc(start)}</strong> and <strong>{_esc(end)}</strong> the warehouse "
            f"records <strong>{_esc(_fmt_int(kpis.get('transactions')))} transactions</strong> worth "
            f"<strong>{_esc(_fmt_money(kpis.get('revenue')))}</strong>, covering "
            f"<strong>{_esc(_fmt_int(kpis.get('units_sold')))} units</strong> and "
            f"<strong>{_esc(_fmt_int(kpis.get('active_customers')))} customers</strong>. "
            f"{product_text}; {region_text}. On the operational side, {pipeline_text}, and "
            f"{quality_text}."
        )

    def _kpi_cards(self, kpis: Mapping[str, Any]) -> str:
        pipeline = kpis.get("pipeline") or {}
        quality = kpis.get("quality") or {}
        cards = [
            ("Total revenue", _fmt_money(kpis.get("revenue")), "All completed transaction value"),
            ("Transactions", _fmt_int(kpis.get("transactions")), "Line items in the warehouse"),
            ("Units sold", _fmt_int(kpis.get("units_sold")), "Total quantity across transactions"),
            ("Avg order value", _fmt_money(kpis.get("avg_order_value")), "Revenue ÷ transactions"),
            ("Active customers", _fmt_int(kpis.get("active_customers")), "Distinct current customers"),
            ("Products", _fmt_int(kpis.get("products")), "Distinct current products"),
            (
                "Quality score",
                _fmt_score(quality.get("overall")) if quality.get("overall") is not None else "n/a",
                "Average of four quality dimensions",
            ),
            (
                "Pipeline success",
                _fmt_pct(pipeline.get("success_rate")) if pipeline.get("success_rate") is not None else "n/a",
                f"{_fmt_int(pipeline.get('success', 0))} of {_fmt_int(pipeline.get('total', 0))} runs",
            ),
        ]
        return "".join(
            f'<div class="card kpi-card"><div class="kpi-label">{_esc(label)}</div>'
            f'<div class="kpi-value">{_esc(value)}</div>'
            f'<div class="kpi-sub">{_esc(sub)}</div></div>'
            for label, value, sub in cards
        )

    def _daily_section(self, daily: Optional[pd.DataFrame]) -> str:
        if daily is None or daily.empty or "total_sales" not in daily.columns:
            return _empty_state("Run the warehouse load and BI export to populate daily sales.")
        working = daily.copy()
        if "full_date" in working.columns:
            working = working.sort_values("full_date")
            labels = working["full_date"].astype(str).tolist()
        else:
            labels = [str(index) for index in range(len(working))]
        values = pd.to_numeric(working["total_sales"], errors="coerce").fillna(0).tolist()
        return _line_chart(labels, values)

    def _monthly_section(self, daily: Optional[pd.DataFrame]) -> str:
        if daily is None or daily.empty or "total_sales" not in daily.columns:
            return _empty_state()
        working = daily.copy()
        working["total_sales"] = pd.to_numeric(working["total_sales"], errors="coerce").fillna(0)
        if "full_date" in working.columns:
            dates = pd.to_datetime(working["full_date"], errors="coerce")
            working = working.assign(_month=dates.dt.to_period("M").astype(str))
            working = working[working["_month"] != "NaT"]
            grouped = working.groupby("_month")["total_sales"].sum().sort_index()
        else:
            grouped = working["total_sales"]
        items = [(str(month), float(value)) for month, value in grouped.items()]
        return _bar_chart(items, color="#3f5b73")

    def _product_section(self, products: Optional[pd.DataFrame]) -> str:
        if products is None or products.empty or "total_revenue" not in products.columns:
            return _empty_state()
        working = products.copy()
        working["total_revenue"] = pd.to_numeric(working["total_revenue"], errors="coerce").fillna(0)
        working = working.sort_values("total_revenue", ascending=False)
        top = working.head(10)
        label_col = "product_name" if "product_name" in top.columns else "product_id"
        items = [
            (str(row.get(label_col, "unknown")), float(row.get("total_revenue", 0)))
            for _, row in top.iterrows()
        ]
        rows = []
        for _, row in top.iterrows():
            rows.append(
                [
                    row.get("product_id", ""),
                    row.get("product_name", ""),
                    row.get("category", ""),
                    _fmt_int(row.get("units_sold", 0)),
                    _fmt_money(row.get("total_revenue", 0)),
                    _fmt_money(row.get("avg_unit_price", 0)),
                ]
            )
        return (
            _bar_chart(items, color="#5f7a8a")
            + '<div style="height:14px"></div>'
            + _table(
                ["Product ID", "Product", "Category", "Units", "Revenue", "Avg unit price"],
                rows,
                numeric_columns=(3, 4, 5),
            )
        )

    def _region_section(self, regions: Optional[pd.DataFrame]) -> str:
        if regions is None or regions.empty or "total_sales" not in regions.columns:
            return _empty_state()
        working = regions.copy()
        working["total_sales"] = pd.to_numeric(working["total_sales"], errors="coerce").fillna(0)
        working = working.sort_values("total_sales", ascending=False)
        top = working.head(10)
        items = [
            (str(row.get("region", row.get("location_name", "unknown"))), float(row.get("total_sales", 0)))
            for _, row in top.iterrows()
        ]
        rows = []
        for _, row in top.iterrows():
            rows.append(
                [
                    row.get("region", ""),
                    row.get("city", ""),
                    row.get("state", ""),
                    _fmt_int(row.get("unique_customers", 0)),
                    _fmt_int(row.get("transaction_count", 0)),
                    _fmt_money(row.get("total_sales", 0)),
                    _fmt_money(row.get("avg_transaction_value", 0)),
                ]
            )
        return (
            _bar_chart(items, color="#3f6b55")
            + '<div style="height:14px"></div>'
            + _table(
                ["Region", "City", "State", "Customers", "Transactions", "Sales", "Avg value"],
                rows,
                numeric_columns=(3, 4, 5, 6),
            )
        )

    def _customer_section(
        self,
        customers: Optional[pd.DataFrame],
    ) -> str:
        if customers is None or customers.empty:
            return _empty_state()

        segment_items: List[Tuple[str, float]] = []
        segment_rows: List[List[Any]] = []
        if {"segment", "total_spend"}.issubset(customers.columns):
            working = customers.copy()
            working["total_spend"] = pd.to_numeric(working["total_spend"], errors="coerce").fillna(0)
            grouped = (
                working.groupby("segment", dropna=False)
                .agg(customers=("customer_id", "nunique"), spend=("total_spend", "sum"))
                .sort_values("spend", ascending=False)
            )
            segment_items = [(str(name), float(row["spend"])) for name, row in grouped.iterrows()]
            segment_rows = [
                [name, _fmt_int(row["customers"]), _fmt_money(row["spend"])]
                for name, row in grouped.iterrows()
            ]

        top_rows: List[List[Any]] = []
        if {"customer_name", "total_spend"}.issubset(customers.columns):
            top = customers.assign(
                total_spend=pd.to_numeric(customers["total_spend"], errors="coerce").fillna(0)
            ).sort_values("total_spend", ascending=False).head(10)
            top_rows = [
                [
                    row.get("customer_id", ""),
                    row.get("customer_name", ""),
                    row.get("segment", ""),
                    _fmt_int(row.get("transaction_count", 0)),
                    _fmt_money(row.get("total_spend", 0)),
                ]
                for _, row in top.iterrows()
            ]

        return (
            _bar_chart(segment_items, color="#6b7280")
            + '<div style="height:14px"></div>'
            + _table(["Segment", "Customers", "Total spend"], segment_rows, numeric_columns=(1, 2))
            + '<div style="height:18px"></div>'
            + '<h4 style="margin:0 0 6px;font-size:14px">Top customers by spend</h4>'
            + _table(
                ["Customer ID", "Name", "Segment", "Transactions", "Spend"],
                top_rows,
                numeric_columns=(3, 4),
            )
        )

    def _quality_section(
        self,
        quality: Mapping[str, Any],
        quality_metrics: Optional[pd.DataFrame],
        alerts: Optional[pd.DataFrame],
    ) -> str:
        parts = [_quality_bars(quality)]
        if quality.get("overall") is not None:
            parts.append(
                f'<p class="section-note" style="margin-top:12px">Overall score '
                f'<strong>{_fmt_score(quality.get("overall"))} / 100</strong> across '
                f'{_fmt_int(quality.get("batches", 0))} recorded batches.</p>'
            )

        severity_counts: Dict[str, int] = {}
        if alerts is not None and not alerts.empty and "severity" in alerts.columns:
            severity_counts = {
                str(k): int(v)
                for k, v in alerts["severity"].astype(str).str.upper().value_counts().items()
            }
        if severity_counts:
            chips = " ".join(
                f'<span class="badge {"failed" if key in ("HIGH", "CRITICAL") else "running"}">'
                f"{_esc(key)}: {count}</span>"
                for key, count in severity_counts.items()
            )
            parts.append(f'<p class="section-note" style="margin-top:14px">Alerts: {chips}</p>')
        else:
            parts.append('<p class="section-note" style="margin-top:14px">No alerts recorded.</p>')

        if quality_metrics is not None and not quality_metrics.empty:
            recent = quality_metrics.tail(6)
            columns = [
                column
                for column in ["batch_id", "dataset_name", "metric_timestamp", "pipeline_status"]
                if column in recent.columns
            ]
            if columns:
                rows = [[row.get(column, "") for column in columns] for _, row in recent.iterrows()]
                parts.append('<div style="height:10px"></div>')
                parts.append(_table([column.replace("_", " ").title() for column in columns], rows))
        return "".join(parts)

    def _pipeline_section(
        self,
        pipeline: Mapping[str, Any],
        pipelines: Optional[pd.DataFrame],
    ) -> str:
        if pipeline.get("total"):
            parts = [
                f'<p class="section-note">Success rate <strong>{_fmt_pct(pipeline.get("success_rate"))}</strong> · '
                f'average duration <strong>{_fmt_score(pipeline.get("avg_duration_seconds"))}s</strong></p>'
            ]
        else:
            parts = []

        if pipelines is None or pipelines.empty:
            parts.append(_empty_state("No pipeline executions recorded yet."))
            return "".join(parts)

        working = pipelines.copy()
        if "started_at" in working.columns:
            working = working.assign(
                _started=pd.to_datetime(working["started_at"], errors="coerce")
            ).sort_values("_started", ascending=False)
        else:
            working = working.iloc[::-1]

        rows = []
        for _, row in working.head(10).iterrows():
            status = str(row.get("status", "UNKNOWN")).upper()
            css = "success" if status == "SUCCESS" else "failed" if status == "FAILED" else "running"
            rows.append(
                [
                    _esc(_short_date(row.get("started_at", ""))),
                    _esc(row.get("pipeline_name", "")),
                    f'<span class="badge {css}">{_esc(status)}</span>',
                    _fmt_int(row.get("records_valid", 0)),
                    f"{_fmt_score(row.get('duration_seconds', 0))}s",
                ]
            )

        head = "".join(
            f"<th>{_esc(header)}</th>"
            for header in ["Started", "Pipeline", "Status", "Valid rows", "Duration"]
        )
        body = "".join(
            "<tr>"
            + "".join(
                f'<td class="num">{cell}</td>' if index >= 3 else f"<td>{cell}</td>"
                for index, cell in enumerate(row)
            )
            + "</tr>"
            for row in rows
        )
        parts.append(
            f'<div class="table-wrap"><table class="data-table"><thead><tr>{head}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>"
        )
        return "".join(parts)

    def _warehouse_section(
        self,
        kpis: Mapping[str, Any],
        manifest: Mapping[str, Any],
    ) -> str:
        counts = kpis.get("warehouse") or {}
        dataset_rows = {
            dataset.get("name"): dataset.get("rows", 0)
            for dataset in manifest.get("datasets", [])
        }

        def count(label: str, value: Any) -> str:
            return (
                f'<div class="flow-step"><div class="step-name">{_esc(label)}</div>'
                f'<div class="step-count">{_fmt_int(value)}</div></div>'
            )

        steps = [
            count("Raw input", counts.get("stg_transactions", 0)),
            '<div class="flow-arrow">→</div>',
            count("Staging rows", counts.get("stg_transactions", 0)),
            '<div class="flow-arrow">→</div>',
            count("Fact rows", counts.get("fact_transactions", 0)),
            '<div class="flow-arrow">→</div>',
            count("Daily view rows", dataset_rows.get("v_daily_sales", 0)),
            '<div class="flow-arrow">→</div>',
            count("BI exports", len(manifest.get("datasets", []))),
        ]
        dimension_rows = [
            ["dim_customer", counts.get("dim_customer", 0)],
            ["dim_product", counts.get("dim_product", 0)],
            ["dim_location", counts.get("dim_location", 0)],
            ["dim_date", counts.get("dim_date", 0)],
        ]

        return (
            '<div class="flow">' + "".join(steps) + "</div>"
            + '<div style="height:16px"></div>'
            + _table(
                ["Dimension", "Rows"],
                [[name, _fmt_int(value)] for name, value in dimension_rows],
                numeric_columns=(1,),
            )
            + '<p class="section-note" style="margin-top:12px">Lineage is also persisted per batch in '
            '<code>metadata.lineage_events</code> and exported as '
            '<code>metadata_lineage_events.csv</code>.</p>'
        )

    def _deliverables_section(self, manifest: Mapping[str, Any]) -> str:
        datasets = manifest.get("datasets") or []
        if not datasets:
            return _empty_state("Run scripts/export_bi_data.py to generate the BI extracts.")

        rows = []
        for dataset in datasets:
            filename = dataset.get("file")
            if filename:
                link = f'<a href="../exports/{_esc(filename)}">{_esc(filename)}</a>'
            else:
                link = "<em>unavailable</em>"
            rows.append(
                [
                    dataset.get("schema", ""),
                    dataset.get("name", ""),
                    dataset.get("description", ""),
                    _fmt_int(dataset.get("rows", 0)),
                    link,
                ]
            )
        return _table(
            ["Schema", "Dataset", "Description", "Rows", "File"],
            rows,
            numeric_columns=(3,),
            html_columns=(4,),
        )

    def _process_section(self) -> str:
        return """
        <div class="flow">
          <div class="flow-step"><div class="step-name">1 · Ingest</div><div class="step-count">Raw</div>
            <div class="section-note" style="margin:2px 0 0">CSV / Excel / API → data/raw</div></div>
          <div class="flow-arrow">→</div>
          <div class="flow-step"><div class="step-name">2 · Validate</div><div class="step-count">Contract</div>
            <div class="section-note" style="margin:2px 0 0">Types, ranges, nulls, quarantine</div></div>
          <div class="flow-arrow">→</div>
          <div class="flow-step"><div class="step-name">3 · Curate</div><div class="step-count">SCD2</div>
            <div class="section-note" style="margin:2px 0 0">Clean, dedupe, version → Parquet</div></div>
          <div class="flow-arrow">→</div>
          <div class="flow-step"><div class="step-name">4 · Model</div><div class="step-count">Star</div>
            <div class="section-note" style="margin:2px 0 0">Staging → dimensions → fact</div></div>
          <div class="flow-arrow">→</div>
          <div class="flow-step"><div class="step-name">5 · Publish</div><div class="step-count">BI</div>
            <div class="section-note" style="margin:2px 0 0">Views → CSV + HTML report</div></div>
        </div>
        <p class="section-note" style="margin-top:14px">Reproduce with:</p>
        <pre style="background:#1f242b;color:#e5e7eb;padding:14px 16px;border-radius:6px;overflow:auto;font-size:12.5px;font-family:Consolas,'Courier New',monospace"><code>python scripts/setup_database.py
python scripts/run_pipeline.py --pipeline etlt_plus_plus --source csv --file tests/fixtures/sample_transactions.csv
python scripts/load_warehouse.py
python scripts/export_bi_data.py
python scripts/generate_project_report.py</code></pre>
        """
