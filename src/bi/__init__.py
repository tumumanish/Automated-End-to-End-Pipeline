"""
Package: bi
Purpose:
    Tool-agnostic Business Intelligence deliverables.

    The BI layer in this project deliberately produces open, portable assets
    (CSV extracts, a KPI summary, a manifest, and a standalone HTML report)
    instead of binary Power BI / Tableau workbooks. Any BI tool can consume
    the exports, and the HTML report can be presented directly.
"""

from src.bi.exporter import BIExporter, compute_kpis
from src.bi.report import OutcomeReportBuilder

__all__ = ["BIExporter", "OutcomeReportBuilder", "compute_kpis"]
