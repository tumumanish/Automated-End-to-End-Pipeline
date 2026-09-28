"""
Integration Tests: Monitoring Pipeline

Tests that the monitoring pipeline correctly captures metrics during pipeline execution.
"""

import sys
from pathlib import Path

import pytest
import pandas as pd
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.monitoring.quality_metrics import QualityMetricsCalculator, BatchQualityMetrics
from src.monitoring.pipeline_metrics import PipelineMetricsTracker
from src.monitoring.alert_manager import AlertManager
from src.monitoring.monitoring_logger import MonitoringLogger
from src.contracts.validation_result import ValidationResult


class TestMonitoringPipelineIntegration:
    """Integration tests for the full monitoring workflow."""

    def test_full_monitoring_workflow(self, tmp_path):
        """Test complete monitoring flow: calculate → alert → log."""
        # 1. Calculate quality metrics
        calc = QualityMetricsCalculator()
        df = pd.DataFrame({"a": [1, 2, None], "b": ["x", "y", "z"]})
        val_result = ValidationResult(
            dataset="test", contract_version="1.0",
            total_records=3, valid_records=2, invalid_records=1,
            status="FAIL",
        )

        metrics = calc.calculate(
            batch_id="b_int_001",
            dataset_name="test",
            source="csv",
            df=df,
            validation_result=val_result,
            ingestion_time=datetime.now(timezone.utc),
        )

        assert isinstance(metrics, BatchQualityMetrics)
        assert metrics.record_count == 3
        assert metrics.accuracy_score < 100.0

        # 2. Evaluate alerts
        alert_mgr = AlertManager(accuracy_warning=98.0, accuracy_critical=60.0)
        alerts = alert_mgr.evaluate(metrics)
        # accuracy = 66.67 which is below 98 warning but above 60 critical → WARNING
        accuracy_alerts = [a for a in alerts if a.metric_name == "accuracy"]
        assert len(accuracy_alerts) >= 1

        # 3. Log metrics
        mon_logger = MonitoringLogger(log_dir=tmp_path)
        filepath = mon_logger.log_quality_metrics(metrics)
        assert filepath.is_file()

    def test_pipeline_metrics_tracking(self):
        """Test pipeline metrics accumulation across runs."""
        tracker = PipelineMetricsTracker()

        tracker.record_execution("etlt_plus_plus", "e1", "SUCCESS", "t1", 5.0, records_extracted=100)
        tracker.record_execution("etlt_plus_plus", "e2", "SUCCESS", "t2", 3.0, records_extracted=200)
        tracker.record_execution("etlt_plus_plus", "e3", "FAILED", "t3", 1.0, records_extracted=50)

        assert tracker.get_success_rate("etlt_plus_plus") == pytest.approx(66.67, abs=0.1)
        assert tracker.get_avg_duration("etlt_plus_plus") == 3.0
        assert tracker.get_throughput("etlt_plus_plus") == pytest.approx(116.67, abs=0.1)

        executions = tracker.get_executions("etlt_plus_plus")
        assert len(executions) == 3
