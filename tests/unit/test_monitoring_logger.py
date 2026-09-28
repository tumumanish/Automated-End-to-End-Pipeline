"""
Unit Tests: Monitoring Logger

Tests for the monitoring logger that persists metrics to JSON files.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timezone

from src.monitoring.monitoring_logger import MonitoringLogger
from src.monitoring.quality_metrics import BatchQualityMetrics
from src.monitoring.pipeline_metrics import PipelineExecutionMetric


class TestMonitoringLogger:
    """Tests for the MonitoringLogger."""

    @pytest.fixture
    def logger(self, tmp_path):
        return MonitoringLogger(log_dir=tmp_path)

    def test_log_quality_metrics(self, logger, tmp_path):
        """Quality metrics should be saved as JSON."""
        metrics = BatchQualityMetrics(
            batch_id="b001",
            dataset_name="test",
            source="csv",
            timestamp="2024-01-01T00:00:00",
            record_count=100,
            valid_count=95,
            invalid_count=5,
            freshness_score=90.0,
            completeness_score=95.0,
            accuracy_score=95.0,
            contract_adherence_score=100.0,
        )

        filepath = logger.log_quality_metrics(metrics)
        assert filepath.is_file()

        with open(filepath) as f:
            data = json.load(f)
        assert data["batch_id"] == "b001"
        assert data["freshness_score"] == 90.0

    def test_log_pipeline_metrics(self, logger, tmp_path):
        """Pipeline metrics should be saved as JSON."""
        metric = PipelineExecutionMetric(
            pipeline_name="etlt_plus_plus",
            execution_id="exec_001",
            status="SUCCESS",
            started_at="2024-01-01T00:00:00",
            completed_at="2024-01-01T00:01:00",
            duration_seconds=60.0,
            records_extracted=100,
        )

        filepath = logger.log_pipeline_metrics(metric)
        assert filepath.is_file()

        with open(filepath) as f:
            data = json.load(f)
        assert data["pipeline_name"] == "etlt_plus_plus"
        assert data["status"] == "SUCCESS"

    def test_log_alert(self, logger, tmp_path):
        """Alerts should be appended to a JSONL file."""
        logger.log_alert({"severity": "WARNING", "message": "test alert"})
        logger.log_alert({"severity": "CRITICAL", "message": "critical alert"})

        filepath = tmp_path / "errors" / "alerts.jsonl"
        assert filepath.is_file()

        lines = filepath.read_text().strip().split("\n")
        assert len(lines) == 2
