"""
Unit Tests: BI Deliverables

Covers the tool-agnostic BI export pipeline and the standalone outcome report:
CSV extraction, KPI computation, manifest generation, HTML rendering, and the
API file-serving guardrails.
"""

import json
import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi import HTTPException

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.routes.bi import _safe_file
from src.bi.exporter import BIExporter, compute_kpis
from src.bi.report import OutcomeReportBuilder


class FakeLoader:
    """Minimal PostgresLoader stand-in backed by in-memory DataFrames."""

    def __init__(self, frames, counts=None):
        self.frames = frames
        self.counts = counts or {}
        self.is_sqlite = True

    def query(self, sql):
        for name, frame in self.frames.items():
            if f" {name}" in sql or f".{name}" in sql:
                return frame.copy()
        raise RuntimeError(f"Unknown dataset in query: {sql}")

    def table_row_count(self, table_name, schema):
        return int(self.counts.get(table_name, 0))


def _frames():
    return {
        "v_daily_sales": pd.DataFrame(
            {
                "full_date": ["2025-01-01", "2025-01-02", "2025-02-01"],
                "total_sales": [100.0, 200.0, 300.0],
                "total_quantity": [1, 2, 3],
                "transaction_count": [1, 2, 3],
            }
        ),
        "v_product_performance": pd.DataFrame(
            {
                "product_id": ["P1", "P2"],
                "product_name": ["Laptop", "Mouse"],
                "category": ["Electronics", "Accessories"],
                "total_revenue": [500.0, 100.0],
                "units_sold": [5, 10],
                "avg_unit_price": [100.0, 10.0],
            }
        ),
        "v_regional_analysis": pd.DataFrame(
            {
                "region": ["North", "South"],
                "city": ["Delhi", "Chennai"],
                "state": ["Delhi", "Tamil Nadu"],
                "total_sales": [450.0, 150.0],
                "unique_customers": [3, 2],
                "transaction_count": [4, 2],
                "avg_transaction_value": [112.5, 75.0],
            }
        ),
        "v_customer_segments": pd.DataFrame(
            {
                "customer_id": ["C1", "C2"],
                "customer_name": ["Asha", "Ravi"],
                "segment": ["Consumer", "Corporate"],
                "total_spend": [400.0, 200.0],
                "transaction_count": [4, 2],
            }
        ),
        "v_transaction_detail": pd.DataFrame({"transaction_id": ["T1", "T2"]}),
        "pipeline_metrics": pd.DataFrame(
            {
                "pipeline_name": ["etlt_plus_plus", "eltl_plus_plus"],
                "execution_id": ["e1", "e2"],
                "status": ["SUCCESS", "SUCCESS"],
                "started_at": ["2025-01-01T00:00:00", "2025-01-02T00:00:00"],
                "duration_seconds": [1.0, 3.0],
                "records_valid": [10, 20],
            }
        ),
        "batch_quality_metrics": pd.DataFrame(
            {
                "batch_id": ["b1"],
                "dataset_name": ["transactions"],
                "metric_timestamp": ["2025-01-01T00:00:00"],
                "pipeline_status": ["SUCCESS"],
                "freshness_score": [100.0],
                "completeness_score": [98.0],
                "accuracy_score": [96.0],
                "contract_adherence_score": [94.0],
            }
        ),
        "alert_log": pd.DataFrame({"severity": ["WARNING", "CRITICAL"]}),
        "lineage_events": pd.DataFrame({"stage": ["ingest", "curate"]}),
    }


@pytest.fixture
def exported(tmp_path):
    loader = FakeLoader(
        _frames(),
        counts={"fact_transactions": 3, "dim_customer": 2, "dim_product": 2, "dim_location": 2, "dim_date": 3},
    )
    output_dir = tmp_path / "exports"
    manifest = BIExporter(loader=loader, output_dir=output_dir).export()
    return output_dir, manifest


class TestKpiComputation:
    def test_headline_metrics(self):
        kpis = compute_kpis(_frames(), {"fact_transactions": 6})
        assert kpis["revenue"] == 600.0
        assert kpis["transactions"] == 6
        assert kpis["units_sold"] == 6
        assert kpis["avg_order_value"] == 100.0
        assert kpis["active_customers"] == 2
        assert kpis["products"] == 2
        assert kpis["regions"] == 2
        assert kpis["top_product"]["label"] == "Laptop"
        assert kpis["top_region"]["label"] == "North"
        assert kpis["top_category"]["category"] == "Electronics"
        assert kpis["date_range"] == {"start": "2025-01-01", "end": "2025-02-01", "days": 3}
        assert kpis["warehouse"]["fact_transactions"] == 6

    def test_quality_and_pipeline(self):
        kpis = compute_kpis(_frames())
        assert kpis["quality"]["overall"] == 97.0
        assert kpis["quality"]["batches"] == 1
        assert kpis["pipeline"]["success_rate"] == 100.0
        assert kpis["pipeline"]["avg_duration_seconds"] == 2.0
        assert kpis["alerts"]["by_severity"] == {"WARNING": 1, "CRITICAL": 1}

    def test_empty_frames_are_safe(self):
        kpis = compute_kpis({})
        assert kpis["revenue"] == 0.0
        assert kpis["transactions"] == 0
        assert kpis["quality"]["overall"] is None
        assert kpis["pipeline"]["success_rate"] is None


class TestBIExporter:
    def test_writes_all_datasets(self, exported):
        output_dir, manifest = exported
        assert len(manifest["datasets"]) == 9
        assert manifest["backend"] == "sqlite"
        for dataset in manifest["datasets"]:
            assert (output_dir / dataset["file"]).exists()
        assert (output_dir / "kpi_summary.json").exists()
        assert (output_dir / "manifest.json").exists()

    def test_kpi_summary_matches_exports(self, exported):
        output_dir, _ = exported
        summary = json.loads((output_dir / "kpi_summary.json").read_text(encoding="utf-8"))
        assert summary["revenue"] == 600.0
        assert summary["top_product"]["label"] == "Laptop"
        assert summary["backend"] == "sqlite"

    def test_limit_is_applied(self, tmp_path):
        loader = FakeLoader(_frames())
        output_dir = tmp_path / "exports"
        manifest = BIExporter(loader=loader, output_dir=output_dir).export(limit=2)
        assert manifest["limit"] == 2
        detail = next(d for d in manifest["datasets"] if d["name"] == "v_transaction_detail")
        assert detail["rows"] == 2

    def test_missing_dataset_is_reported_not_fatal(self, tmp_path):
        frames = _frames()
        frames.pop("v_regional_analysis")
        loader = FakeLoader(frames)
        manifest = BIExporter(loader=loader, output_dir=tmp_path / "exports").export()
        region = next(d for d in manifest["datasets"] if d["name"] == "v_regional_analysis")
        assert region["status"] == "unavailable"
        assert any("v_regional_analysis" in error["dataset"] for error in manifest["errors"])


class TestOutcomeReport:
    def test_report_contains_kpis_and_charts(self, exported):
        output_dir, _ = exported
        html = OutcomeReportBuilder(exports_dir=output_dir).build()
        assert "<!DOCTYPE html>" in html
        assert "Project Outcome Report" in html
        assert "Executive Summary" in html
        assert "₹600" in html
        assert "Laptop" in html
        assert html.count("<svg") >= 3
        assert "Total revenue" in html
        assert "Data Quality" in html
        assert "BI Deliverables" in html

    def test_deliverable_links_are_real_anchors(self, exported):
        output_dir, _ = exported
        html = OutcomeReportBuilder(exports_dir=output_dir).build()
        assert '<a href="../exports/analytics_v_daily_sales.csv">' in html
        assert "&lt;a href" not in html

    def test_report_writes_file(self, exported, tmp_path):
        output_dir, _ = exported
        target = tmp_path / "report.html"
        path = OutcomeReportBuilder(exports_dir=output_dir).write(target)
        assert path == target
        assert target.stat().st_size > 5000

    def test_empty_exports_still_render(self, tmp_path):
        html = OutcomeReportBuilder(exports_dir=tmp_path / "missing").build()
        assert "Project Outcome Report" in html
        assert "No data available" in html


class TestExportFileGuard:
    def test_rejects_traversal(self, tmp_path):
        (tmp_path / "safe.csv").write_text("a,b\n1,2\n", encoding="utf-8")
        with pytest.raises(HTTPException):
            _safe_file(tmp_path, "../safe.csv")

    def test_rejects_unsupported_suffix(self, tmp_path):
        (tmp_path / "notes.exe").write_text("nope", encoding="utf-8")
        with pytest.raises(HTTPException):
            _safe_file(tmp_path, "notes.exe")

    def test_accepts_valid_file(self, tmp_path):
        target = tmp_path / "safe.csv"
        target.write_text("a,b\n1,2\n", encoding="utf-8")
        assert _safe_file(tmp_path, "safe.csv") == target.resolve()
