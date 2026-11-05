"""
Module: bi.exporter
Purpose:
    Export BI-ready datasets from the warehouse analytical views and the
    monitoring schema, plus a KPI summary and a manifest describing every
    generated file.

    The exports are intentionally tool-agnostic (plain CSV + JSON) so they can
    be loaded into Power BI, Tableau, Excel, or any other BI tool without
    requiring a live database connection. This also keeps the deliverable
    reproducible on machines where PostgreSQL is unavailable and the project
    is running against the SQLite fallback warehouse.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import pandas as pd

from src.storage.postgres.pg_loader import PostgresLoader
from src.utils.file_utils import ensure_directory, get_project_root
from src.utils.logger import get_logger

logger = get_logger("bi.exporter")

# Analytical views exposed to BI tools. Order is meaningful: it is the order
# used in the report and in the manifest.
ANALYTICS_VIEWS: Dict[str, str] = {
    "v_daily_sales": "Daily sales with calendar attributes",
    "v_product_performance": "Product revenue, units, and averages",
    "v_regional_analysis": "Regional sales and customer reach",
    "v_customer_segments": "Customer spend, frequency, and recency",
    "v_transaction_detail": "Denormalized transaction-level detail",
}

# Monitoring tables used by quality and pipeline-health dashboards.
MONITORING_TABLES: Dict[str, str] = {
    "pipeline_metrics": "Pipeline execution history",
    "batch_quality_metrics": "Per-batch data quality scores",
    "alert_log": "Alert history with severity",
}

LINEAGE_TABLE = "lineage_events"
DEFAULT_OUTPUT_DIR = get_project_root() / "dashboard" / "exports"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a scalar to float, tolerating None, NaN, and strings."""
    try:
        if value is None:
            return default
        if isinstance(value, float) and math.isnan(value):
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except (TypeError, ValueError):
        return default


def _column_sum(df: pd.DataFrame, column: str) -> float:
    if df is None or df.empty or column not in df.columns:
        return 0.0
    return _safe_float(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def _column_count(df: pd.DataFrame, column: str) -> int:
    if df is None or df.empty or column not in df.columns:
        return 0
    return int(df[column].nunique(dropna=True))


def _score(df: pd.DataFrame, column: str) -> Optional[float]:
    """Return the mean of a score column on a 0-100 scale, or None."""
    if df is None or df.empty or column not in df.columns:
        return None
    values = pd.to_numeric(df[column], errors="coerce").dropna()
    if values.empty:
        return None
    # Scores are stored on a 0-100 scale. Guard against 0-1 storage too.
    mean_value = float(values.mean())
    if 0.0 <= mean_value <= 1.0 and float(values.max()) <= 1.0:
        mean_value *= 100.0
    return round(mean_value, 2)


def _date_range(daily: pd.DataFrame) -> Dict[str, Optional[str]]:
    if daily is None or daily.empty or "full_date" not in daily.columns:
        return {"start": None, "end": None, "days": 0}
    values = pd.to_datetime(daily["full_date"], errors="coerce").dropna()
    if values.empty:
        return {"start": None, "end": None, "days": 0}
    start = values.min().date().isoformat()
    end = values.max().date().isoformat()
    return {"start": start, "end": end, "days": int(values.dt.date.nunique())}


def _top_row(df: pd.DataFrame, value_column: str, label_column: str) -> Optional[Dict[str, Any]]:
    if df is None or df.empty or value_column not in df.columns or label_column not in df.columns:
        return None
    working = df[[label_column, value_column]].copy()
    working[value_column] = pd.to_numeric(working[value_column], errors="coerce").fillna(0)
    if working.empty:
        return None
    row = working.sort_values(value_column, ascending=False).iloc[0]
    return {"label": str(row[label_column]), "value": round(_safe_float(row[value_column]), 2)}


def compute_kpis(
    frames: Mapping[str, pd.DataFrame],
    warehouse_counts: Optional[Mapping[str, int]] = None,
) -> Dict[str, Any]:
    """
    Compute headline KPIs from the exported datasets.

    This is a pure function (no database access) so it can be reused by the
    HTML report builder and unit-tested independently.
    """
    daily = frames.get("v_daily_sales", pd.DataFrame())
    products = frames.get("v_product_performance", pd.DataFrame())
    regions = frames.get("v_regional_analysis", pd.DataFrame())
    customers = frames.get("v_customer_segments", pd.DataFrame())
    quality = frames.get("batch_quality_metrics", pd.DataFrame())
    pipelines = frames.get("pipeline_metrics", pd.DataFrame())
    alerts = frames.get("alert_log", pd.DataFrame())

    revenue = _column_sum(daily, "total_sales")
    transactions = int(_column_sum(daily, "transaction_count"))
    units = int(_column_sum(daily, "total_quantity"))

    # Fall back to product/region totals if the daily view is unavailable.
    if revenue == 0.0:
        revenue = _column_sum(products, "total_revenue")
    if revenue == 0.0:
        revenue = _column_sum(regions, "total_sales")

    avg_order_value = revenue / transactions if transactions else 0.0

    category_totals: list[dict[str, Any]] = []
    if not products.empty and {"category", "total_revenue"}.issubset(products.columns):
        grouped = (
            products.assign(total_revenue=pd.to_numeric(products["total_revenue"], errors="coerce").fillna(0))
            .groupby("category", dropna=False)["total_revenue"]
            .sum()
            .sort_values(ascending=False)
        )
        category_totals = [
            {"category": str(name), "revenue": round(float(value), 2)}
            for name, value in grouped.items()
        ]

    quality_scores = {
        "freshness": _score(quality, "freshness_score"),
        "completeness": _score(quality, "completeness_score"),
        "accuracy": _score(quality, "accuracy_score"),
        "contract_adherence": _score(quality, "contract_adherence_score"),
    }
    present_scores = [value for value in quality_scores.values() if value is not None]
    overall_quality = round(sum(present_scores) / len(present_scores), 2) if present_scores else None

    pipeline_total = 0
    pipeline_success = 0
    pipeline_failed = 0
    avg_duration = 0.0
    last_execution = None
    if not pipelines.empty and "status" in pipelines.columns:
        pipeline_total = len(pipelines)
        statuses = pipelines["status"].astype(str).str.upper()
        pipeline_success = int((statuses == "SUCCESS").sum())
        pipeline_failed = int((statuses == "FAILED").sum())
        duration = pd.Series(dtype="float64")
        if "duration_seconds" in pipelines.columns:
            duration = pd.to_numeric(pipelines["duration_seconds"], errors="coerce").dropna()
        avg_duration = round(float(duration.mean()), 3) if not duration.empty else 0.0
        if "started_at" in pipelines.columns:
            ordered = pipelines.assign(
                _started=pd.to_datetime(pipelines["started_at"], errors="coerce")
            ).sort_values("_started")
            latest = ordered.iloc[-1]
            last_execution = {
                "execution_id": str(latest.get("execution_id", "")),
                "pipeline_name": str(latest.get("pipeline_name", "")),
                "status": str(latest.get("status", "")),
                "started_at": str(latest.get("started_at", "")),
                "duration_seconds": _safe_float(latest.get("duration_seconds", 0)),
            }

    alert_counts: Dict[str, int] = {}
    if not alerts.empty and "severity" in alerts.columns:
        alert_counts = {
            str(key): int(value)
            for key, value in alerts["severity"].astype(str).str.upper().value_counts().items()
        }

    return {
        "generated_at": _utc_now_iso(),
        "revenue": round(revenue, 2),
        "transactions": transactions,
        "units_sold": units,
        "avg_order_value": round(avg_order_value, 2),
        "active_customers": _column_count(customers, "customer_id"),
        "products": _column_count(products, "product_id"),
        "regions": _column_count(regions, "region"),
        "date_range": _date_range(daily),
        "top_product": _top_row(products, "total_revenue", "product_name"),
        "top_region": _top_row(regions, "total_sales", "region"),
        "top_category": category_totals[0] if category_totals else None,
        "category_breakdown": category_totals,
        "quality": {
            **quality_scores,
            "overall": overall_quality,
            "batches": int(len(quality)),
        },
        "pipeline": {
            "total": pipeline_total,
            "success": pipeline_success,
            "failed": pipeline_failed,
            "success_rate": round((pipeline_success / pipeline_total) * 100, 2) if pipeline_total else None,
            "avg_duration_seconds": avg_duration,
            "last_execution": last_execution,
        },
        "alerts": {
            "total": int(len(alerts)),
            "by_severity": alert_counts,
        },
        "warehouse": dict(warehouse_counts or {}),
    }


class BIExporter:
    """Export analytical views and monitoring tables to CSV/JSON."""

    def __init__(
        self,
        loader: Optional[PostgresLoader] = None,
        output_dir: Optional[Path | str] = None,
    ):
        self._loader = loader or PostgresLoader()
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR

    # ── Query helpers ───────────────────────────────────────

    def _query(self, sql: str) -> pd.DataFrame:
        return self._loader.query(sql)

    def _load_frame(self, schema: str, name: str, limit: int = 0) -> pd.DataFrame:
        sql = f"SELECT * FROM {schema}.{name}"
        if limit and limit > 0:
            sql += f" LIMIT {int(limit)}"
        return self._query(sql)

    def _warehouse_counts(self) -> Dict[str, int]:
        tables = {
            "stg_transactions": "staging",
            "dim_date": "warehouse",
            "dim_customer": "warehouse",
            "dim_product": "warehouse",
            "dim_location": "warehouse",
            "fact_transactions": "warehouse",
        }
        counts: Dict[str, int] = {}
        for table, schema in tables.items():
            try:
                counts[table] = int(self._loader.table_row_count(table, schema))
            except Exception as exc:  # table may not exist in a fresh warehouse
                logger.warning("Could not count %s.%s: %s", schema, table, exc)
                counts[table] = 0
        return counts

    # ── Public API ──────────────────────────────────────────

    def export(self, limit: int = 0) -> Dict[str, Any]:
        """
        Export all BI datasets and return the manifest.

        Args:
            limit: Optional row limit per dataset (0 or negative = all rows).
        """
        ensure_directory(self.output_dir)
        frames: Dict[str, pd.DataFrame] = {}
        datasets: list[Dict[str, Any]] = []
        errors: list[Dict[str, str]] = []

        for view, description in ANALYTICS_VIEWS.items():
            self._collect(
                frames=frames,
                datasets=datasets,
                errors=errors,
                schema="analytics",
                name=view,
                description=description,
                limit=limit,
            )

        for table, description in MONITORING_TABLES.items():
            self._collect(
                frames=frames,
                datasets=datasets,
                errors=errors,
                schema="monitoring",
                name=table,
                description=description,
                limit=limit,
            )

        self._collect(
            frames=frames,
            datasets=datasets,
            errors=errors,
            schema="metadata",
            name=LINEAGE_TABLE,
            description="Stage-by-stage lineage events",
            limit=limit,
        )

        kpis = compute_kpis(frames, self._warehouse_counts())
        kpis["backend"] = "sqlite" if self._loader.is_sqlite else "postgresql"

        summary_file = self.output_dir / "kpi_summary.json"
        summary_file.write_text(
            json.dumps(kpis, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

        manifest = {
            "generated_at": _utc_now_iso(),
            "backend": kpis["backend"],
            "output_dir": str(self.output_dir),
            "limit": int(limit) if limit and limit > 0 else None,
            "datasets": datasets,
            "errors": errors,
            "files": sorted(
                path.name for path in self.output_dir.glob("*") if path.is_file()
            ),
        }
        (self.output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

        logger.info(
            "BI export complete: %d datasets, %d rows, %d errors -> %s",
            len([d for d in datasets if d["rows"] > 0]),
            sum(d["rows"] for d in datasets),
            len(errors),
            self.output_dir,
        )
        return manifest

    def _collect(
        self,
        frames: Dict[str, pd.DataFrame],
        datasets: list[Dict[str, Any]],
        errors: list[Dict[str, str]],
        schema: str,
        name: str,
        description: str,
        limit: int,
    ) -> None:
        try:
            frame = self._load_frame(schema, name, limit=limit)
        except Exception as exc:
            logger.warning("Skipping %s.%s: %s", schema, name, exc)
            errors.append({"dataset": f"{schema}.{name}", "error": str(exc)})
            datasets.append(
                {
                    "name": name,
                    "schema": schema,
                    "description": description,
                    "file": None,
                    "rows": 0,
                    "columns": [],
                    "status": "unavailable",
                }
            )
            return

        frames[name] = frame
        filename = f"{schema}_{name}.csv"
        target = self.output_dir / filename
        # Always write the header, even for an empty result, so consumers can
        # bind the schema before data exists.
        frame.to_csv(target, index=False, encoding="utf-8")
        datasets.append(
            {
                "name": name,
                "schema": schema,
                "description": description,
                "file": filename,
                "rows": int(len(frame)),
                "columns": [str(column) for column in frame.columns],
                "status": "ready" if not frame.empty else "empty",
            }
        )
