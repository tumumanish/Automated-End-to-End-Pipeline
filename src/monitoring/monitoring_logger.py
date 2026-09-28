"""
Module: monitoring_logger
Purpose:
    Persist quality metrics and pipeline metrics to JSON log files
    and (when available) to the monitoring PostgreSQL schema.
"""

import json
from pathlib import Path
from typing import Optional

from src.monitoring.quality_metrics import BatchQualityMetrics
from src.monitoring.pipeline_metrics import PipelineExecutionMetric
from src.utils.file_utils import get_project_root, ensure_directory
from src.utils.logger import get_logger

logger = get_logger("monitoring.logger")


class MonitoringLogger:
    """
    Writes structured monitoring data to JSON log files.

    File patterns:
      - logs/pipeline/<execution_id>_metrics.json
      - logs/validation/<batch_id>_quality.json
    """

    def __init__(self, log_dir: Path | None = None):
        self._root = log_dir or (get_project_root() / "logs")

    def log_quality_metrics(self, metrics: BatchQualityMetrics) -> Path:
        """
        Persist batch quality metrics to a JSON file.

        Args:
            metrics: The quality metrics to persist.

        Returns:
            Path to the saved file.
        """
        out_dir = ensure_directory(self._root / "validation")
        filepath = out_dir / f"{metrics.batch_id}_quality.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metrics.to_dict(), f, indent=2, default=str)

        logger.info("Quality metrics logged -> %s", filepath)
        return filepath

    def log_pipeline_metrics(self, metric: PipelineExecutionMetric) -> Path:
        """
        Persist pipeline execution metrics to a JSON file.

        Args:
            metric: The pipeline execution metric to persist.

        Returns:
            Path to the saved file.
        """
        out_dir = ensure_directory(self._root / "pipeline")
        filepath = out_dir / f"{metric.execution_id}_metrics.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metric.to_dict(), f, indent=2, default=str)

        logger.info("Pipeline metrics logged -> %s", filepath)
        return filepath

    def log_alert(self, alert_data: dict) -> Path:
        """
        Append an alert to the alerts log file.

        Args:
            alert_data: Alert dictionary to log.

        Returns:
            Path to the alerts log file.
        """
        out_dir = ensure_directory(self._root / "errors")
        filepath = out_dir / "alerts.jsonl"

        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert_data, default=str) + "\n")

        return filepath
