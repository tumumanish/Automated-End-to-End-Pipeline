"""
Module: db_writer (Monitoring & Lineage Database Persistence)
Purpose:
    Persist pipeline execution records, quality metrics, alert history,
    and data lineage events directly to persistent database tables.
    Supports both PostgreSQL and local SQLite warehouse storage transparently.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import text

from src.storage.postgres.pg_loader import PostgresLoader
from src.utils.logger import get_logger
from src.utils.timestamps import utc_now

logger = get_logger("monitoring.db_writer")


class MonitoringDBWriter:
    """
    Persists monitoring and lineage data to warehouse tables.
    """

    def __init__(self, loader: Optional[PostgresLoader] = None):
        self._loader = loader or PostgresLoader()

    def write_pipeline_execution(self, metric: Any) -> bool:
        """
        Persist a pipeline execution metric to monitoring.pipeline_metrics.
        """
        data = metric.to_dict() if hasattr(metric, "to_dict") else dict(metric)
        df = pd.DataFrame([{
            "pipeline_name": data.get("pipeline_name", "unknown"),
            "execution_id": data.get("execution_id", ""),
            "status": data.get("status", "UNKNOWN"),
            "started_at": data.get("started_at"),
            "completed_at": data.get("completed_at"),
            "duration_seconds": float(data.get("duration_seconds", 0.0)),
            "records_extracted": int(data.get("records_extracted", 0)),
            "records_valid": int(data.get("records_valid", 0)),
            "records_invalid": int(data.get("records_invalid", 0)),
            "records_transformed": int(data.get("records_transformed", 0)),
            "error_message": data.get("error_message"),
        }])

        try:
            self._loader.load_dataframe(df, "pipeline_metrics", "monitoring", if_exists="append")
            logger.info("Persisted pipeline execution %s to database", data.get("execution_id"))
            return True
        except Exception as exc:
            logger.warning("Failed to persist execution metrics to DB: %s", exc)
            return False

    def write_quality_metrics(self, metrics: Any) -> bool:
        """
        Persist batch data quality metrics to monitoring.batch_quality_metrics.
        """
        data = metrics.to_dict() if hasattr(metrics, "to_dict") else dict(metrics)
        df = pd.DataFrame([{
            "batch_id": data.get("batch_id", ""),
            "dataset_name": data.get("dataset_name", ""),
            "source": data.get("source", ""),
            "metric_timestamp": data.get("timestamp", utc_now()),
            "record_count": int(data.get("record_count", 0)),
            "valid_count": int(data.get("valid_count", 0)),
            "invalid_count": int(data.get("invalid_count", 0)),
            "quarantined_count": int(data.get("quarantined_count", 0)),
            "freshness_score": float(data.get("freshness_score", 0.0)),
            "completeness_score": float(data.get("completeness_score", 0.0)),
            "accuracy_score": float(data.get("accuracy_score", 0.0)),
            "contract_adherence_score": float(data.get("contract_adherence_score", 0.0)),
            "pipeline_status": data.get("pipeline_status", "UNKNOWN"),
            "processing_duration": float(data.get("processing_duration_seconds", 0.0)),
        }])

        try:
            self._loader.load_dataframe(df, "batch_quality_metrics", "monitoring", if_exists="append")
            logger.info("Persisted quality metrics for batch %s to database", data.get("batch_id"))
            return True
        except Exception as exc:
            logger.warning("Failed to persist quality metrics to DB: %s", exc)
            return False

    def write_alert(self, alert: Any) -> bool:
        """
        Persist an alert log record to monitoring.alert_log.
        """
        data = alert.to_dict() if hasattr(alert, "to_dict") else dict(alert)
        df = pd.DataFrame([{
            "alert_timestamp": data.get("timestamp", utc_now()),
            "severity": data.get("severity", "INFO"),
            "category": data.get("category", "General"),
            "message": data.get("message", ""),
            "batch_id": data.get("batch_id", ""),
            "dataset_name": data.get("dataset_name", ""),
            "metric_name": data.get("metric_name", ""),
            "metric_value": float(data.get("metric_value", 0.0)),
            "threshold_value": float(data.get("threshold_value", 0.0)),
            "acknowledged": False,
        }])

        try:
            self._loader.load_dataframe(df, "alert_log", "monitoring", if_exists="append")
            logger.info("Persisted alert [%s] to database", data.get("severity"))
            return True
        except Exception as exc:
            logger.warning("Failed to persist alert to DB: %s", exc)
            return False

    def write_lineage_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Persist a single lineage stage event to metadata.lineage_events.
        """
        meta_val = event_data.get("metadata", {})
        if isinstance(meta_val, dict):
            meta_str = json.dumps(meta_val)
        else:
            meta_str = str(meta_val)

        df = pd.DataFrame([{
            "event_id": event_data.get("event_id", ""),
            "batch_id": event_data.get("batch_id", ""),
            "pipeline_name": event_data.get("pipeline", event_data.get("pipeline_name", "etlt_plus_plus")),
            "stage": event_data.get("stage", ""),
            "source_system": event_data.get("source_system", ""),
            "dataset_name": event_data.get("dataset_name", "transactions"),
            "contract_version": event_data.get("contract_version", "1.0"),
            "input_record_count": int(event_data.get("input_record_count", 0)),
            "output_record_count": int(event_data.get("output_record_count", 0)),
            "event_timestamp": event_data.get("timestamp", utc_now()),
            "metadata": meta_str,
        }])

        try:
            self._loader.load_dataframe(df, "lineage_events", "metadata", if_exists="append")
            return True
        except Exception as exc:
            logger.warning("Failed to persist lineage event to DB: %s", exc)
            return False

    def get_recent_executions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent executions from monitoring.pipeline_metrics."""
        try:
            df = self._loader.query(
                f"SELECT * FROM monitoring.pipeline_metrics ORDER BY started_at DESC LIMIT {limit}"
            )
            return df.to_dict(orient="records")
        except Exception:
            return []

    def get_latest_quality_metrics(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent quality metrics from monitoring.batch_quality_metrics."""
        try:
            df = self._loader.query(
                f"SELECT * FROM monitoring.batch_quality_metrics ORDER BY metric_timestamp DESC LIMIT {limit}"
            )
            return df.to_dict(orient="records")
        except Exception:
            return []

    def get_recent_alerts(self, severity: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent alerts from monitoring.alert_log."""
        try:
            where_clause = f"WHERE severity = '{severity.upper()}'" if severity else ""
            df = self._loader.query(
                f"SELECT * FROM monitoring.alert_log {where_clause} ORDER BY alert_timestamp DESC LIMIT {limit}"
            )
            return df.to_dict(orient="records")
        except Exception:
            return []
