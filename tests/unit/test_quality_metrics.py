"""
Unit Tests: Quality Metrics Module

Tests for data quality monitoring — freshness, completeness, accuracy, adherence.
"""

import pytest
from datetime import datetime, timezone, timedelta

import pandas as pd

from src.monitoring.freshness import FreshnessMonitor
from src.monitoring.completeness import CompletenessMonitor
from src.monitoring.accuracy import AccuracyMonitor
from src.monitoring.contract_adherence import ContractAdherenceMonitor
from src.monitoring.quality_metrics import QualityMetricsCalculator, BatchQualityMetrics
from src.monitoring.alert_manager import AlertManager, AlertSeverity
from src.contracts.validation_result import ValidationResult


# ──────────────────────────────────────────────────
# Freshness Tests
# ──────────────────────────────────────────────────

class TestFreshness:
    """Tests for freshness monitoring."""

    def test_fresh_data_scores_100(self):
        """Just-ingested data should score ~100."""
        monitor = FreshnessMonitor(max_age_hours=24.0)
        now = datetime.now(timezone.utc)
        score = monitor.calculate_score(now)
        assert score >= 99.0

    def test_stale_data_scores_0(self):
        """Data older than max_age should score 0."""
        monitor = FreshnessMonitor(max_age_hours=24.0)
        old = datetime.now(timezone.utc) - timedelta(hours=48)
        score = monitor.calculate_score(old)
        assert score == 0.0

    def test_half_age_scores_50(self):
        """Data at half the max age should score ~50."""
        monitor = FreshnessMonitor(max_age_hours=24.0)
        half = datetime.now(timezone.utc) - timedelta(hours=12)
        score = monitor.calculate_score(half)
        assert 45.0 <= score <= 55.0

    def test_is_fresh(self):
        """is_fresh should return True for recent data."""
        monitor = FreshnessMonitor(max_age_hours=24.0)
        assert monitor.is_fresh(datetime.now(timezone.utc)) is True
        old = datetime.now(timezone.utc) - timedelta(hours=48)
        assert monitor.is_fresh(old) is False


# ──────────────────────────────────────────────────
# Completeness Tests
# ──────────────────────────────────────────────────

class TestCompleteness:
    """Tests for completeness monitoring."""

    def test_complete_data_scores_100(self):
        """DataFrame with no nulls should score 100."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        monitor = CompletenessMonitor()
        assert monitor.calculate_score(df) == 100.0

    def test_partial_nulls(self):
        """DataFrame with some nulls should score < 100."""
        df = pd.DataFrame({"a": [1, None, 3], "b": ["x", "y", None]})
        monitor = CompletenessMonitor()
        score = monitor.calculate_score(df)
        # 4 out of 6 cells are non-null = 66.67
        assert 60.0 <= score <= 70.0

    def test_empty_dataframe(self):
        """Empty DataFrame should score 0."""
        df = pd.DataFrame()
        monitor = CompletenessMonitor()
        assert monitor.calculate_score(df) == 0.0

    def test_per_field_scores(self):
        """Per-field scores should identify incomplete fields."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [None, None, "z"]})
        monitor = CompletenessMonitor()
        scores = monitor.per_field_scores(df)
        assert scores["a"] == 100.0
        assert scores["b"] == pytest.approx(33.33, abs=0.1)

    def test_get_incomplete_fields(self):
        """Should return fields below threshold."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [None, None, "z"]})
        monitor = CompletenessMonitor(min_percent=95.0)
        incomplete = monitor.get_incomplete_fields(df)
        assert "b" in incomplete
        assert "a" not in incomplete


# ──────────────────────────────────────────────────
# Accuracy Tests
# ──────────────────────────────────────────────────

class TestAccuracy:
    """Tests for accuracy monitoring."""

    def _make_result(self, total, valid, invalid):
        return ValidationResult(
            dataset="test",
            contract_version="1.0",
            total_records=total,
            valid_records=valid,
            invalid_records=invalid,
            status="PASS" if invalid == 0 else "FAIL",
        )

    def test_perfect_accuracy(self):
        """All valid records should score 100."""
        monitor = AccuracyMonitor()
        result = self._make_result(100, 100, 0)
        assert monitor.calculate_score(result) == 100.0

    def test_partial_accuracy(self):
        """Mix of valid/invalid should produce correct score."""
        monitor = AccuracyMonitor()
        result = self._make_result(100, 90, 10)
        assert monitor.calculate_score(result) == 90.0

    def test_is_accurate(self):
        """is_accurate should respect threshold."""
        monitor = AccuracyMonitor(min_percent=95.0)
        good = self._make_result(100, 96, 4)
        bad = self._make_result(100, 90, 10)
        assert monitor.is_accurate(good) is True
        assert monitor.is_accurate(bad) is False


# ──────────────────────────────────────────────────
# Contract Adherence Tests
# ──────────────────────────────────────────────────

class TestContractAdherence:
    """Tests for contract adherence monitoring."""

    def test_all_passed(self):
        """All batches passed should score 100."""
        monitor = ContractAdherenceMonitor()
        monitor.record_batch("b1", passed=True)
        monitor.record_batch("b2", passed=True)
        assert monitor.calculate_score() == 100.0

    def test_mixed_results(self):
        """Mixed pass/fail should produce correct score."""
        monitor = ContractAdherenceMonitor()
        monitor.record_batch("b1", passed=True)
        monitor.record_batch("b2", passed=False)
        assert monitor.calculate_score() == 50.0

    def test_get_failed_batches(self):
        """Should return failed batch details."""
        monitor = ContractAdherenceMonitor()
        monitor.record_batch("b1", passed=True)
        monitor.record_batch("b2", passed=False, details="schema mismatch")
        failed = monitor.get_failed_batches()
        assert len(failed) == 1
        assert failed[0]["batch_id"] == "b2"

    def test_empty_history_scores_100(self):
        """No recorded batches should default to 100."""
        monitor = ContractAdherenceMonitor()
        assert monitor.calculate_score() == 100.0


# ──────────────────────────────────────────────────
# Aggregate Quality Metrics Tests
# ──────────────────────────────────────────────────

class TestQualityMetrics:
    """Tests for the unified QualityMetricsCalculator."""

    def test_calculate_metrics(self):
        """Full quality calculation should produce valid metrics."""
        calc = QualityMetricsCalculator()
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        val_result = ValidationResult(
            dataset="test", contract_version="1.0",
            total_records=3, valid_records=3, invalid_records=0,
            status="PASS",
        )

        metrics = calc.calculate(
            batch_id="b001",
            dataset_name="test",
            source="csv",
            df=df,
            validation_result=val_result,
            ingestion_time=datetime.now(timezone.utc),
        )

        assert isinstance(metrics, BatchQualityMetrics)
        assert metrics.freshness_score >= 99.0
        assert metrics.completeness_score == 100.0
        assert metrics.accuracy_score == 100.0
        assert metrics.overall_score > 0

    def test_overall_score_weighting(self):
        """Overall score should be a weighted average."""
        metrics = BatchQualityMetrics(
            batch_id="b1", dataset_name="test", source="csv",
            timestamp="now",
            freshness_score=100.0,
            completeness_score=100.0,
            accuracy_score=100.0,
            contract_adherence_score=100.0,
        )
        assert metrics.overall_score == 100.0


# ──────────────────────────────────────────────────
# Alert Manager Tests
# ──────────────────────────────────────────────────

class TestAlertManager:
    """Tests for alert generation."""

    def test_no_alerts_for_good_data(self):
        """Perfect metrics should generate no alerts."""
        mgr = AlertManager()
        metrics = BatchQualityMetrics(
            batch_id="b1", dataset_name="test", source="csv",
            timestamp="now",
            freshness_score=100.0, completeness_score=100.0,
            accuracy_score=100.0, contract_adherence_score=100.0,
            pipeline_status="SUCCESS",
        )
        alerts = mgr.evaluate(metrics)
        assert len(alerts) == 0

    def test_warning_alert(self):
        """Below-warning metrics should generate WARNING alerts."""
        mgr = AlertManager(accuracy_warning=98.0, accuracy_critical=90.0)
        metrics = BatchQualityMetrics(
            batch_id="b1", dataset_name="test", source="csv",
            timestamp="now",
            freshness_score=100.0, completeness_score=100.0,
            accuracy_score=95.0, contract_adherence_score=100.0,
            pipeline_status="SUCCESS",
        )
        alerts = mgr.evaluate(metrics)
        accuracy_alerts = [a for a in alerts if a.metric_name == "accuracy"]
        assert len(accuracy_alerts) == 1
        assert accuracy_alerts[0].severity == "WARNING"

    def test_critical_alert(self):
        """Below-critical metrics should generate CRITICAL alerts."""
        mgr = AlertManager(completeness_critical=85.0)
        metrics = BatchQualityMetrics(
            batch_id="b1", dataset_name="test", source="csv",
            timestamp="now",
            freshness_score=100.0, completeness_score=80.0,
            accuracy_score=100.0, contract_adherence_score=100.0,
            pipeline_status="SUCCESS",
        )
        alerts = mgr.evaluate(metrics)
        completeness_alerts = [a for a in alerts if a.metric_name == "completeness"]
        assert len(completeness_alerts) == 1
        assert completeness_alerts[0].severity == "CRITICAL"

    def test_pipeline_failure_alert(self):
        """Failed pipeline status should generate CRITICAL alert."""
        mgr = AlertManager()
        metrics = BatchQualityMetrics(
            batch_id="b1", dataset_name="test", source="csv",
            timestamp="now",
            freshness_score=100.0, completeness_score=100.0,
            accuracy_score=100.0, contract_adherence_score=100.0,
            pipeline_status="FAILED",
        )
        alerts = mgr.evaluate(metrics)
        pipeline_alerts = [a for a in alerts if a.category == "pipeline"]
        assert len(pipeline_alerts) == 1
        assert pipeline_alerts[0].severity == "CRITICAL"
