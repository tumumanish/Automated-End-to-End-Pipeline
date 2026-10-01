"""
Unit Tests: Alert Manager

Tests for threshold-based alert evaluation, alert severity, and alert querying.
"""

import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.monitoring.alert_manager import AlertManager, Alert, AlertSeverity
from src.monitoring.quality_metrics import BatchQualityMetrics


def _make_metrics(**overrides) -> BatchQualityMetrics:
    """Helper to create BatchQualityMetrics with sensible defaults."""
    defaults = dict(
        batch_id="b_test",
        dataset_name="transactions",
        source="csv",
        timestamp="2026-01-01T00:00:00Z",
        record_count=100,
        valid_count=95,
        invalid_count=5,
        quarantined_count=5,
        freshness_score=90.0,
        completeness_score=98.0,
        accuracy_score=95.0,
        contract_adherence_score=100.0,
        pipeline_status="SUCCESS",
        processing_duration_seconds=2.0,
    )
    defaults.update(overrides)
    return BatchQualityMetrics(**defaults)


class TestAlertSeverity:
    """Tests for the AlertSeverity enum."""

    def test_severity_values(self):
        assert AlertSeverity.INFO.value == "INFO"
        assert AlertSeverity.WARNING.value == "WARNING"
        assert AlertSeverity.CRITICAL.value == "CRITICAL"


class TestAlertDataclass:
    """Tests for the Alert dataclass."""

    def test_alert_to_dict(self):
        alert = Alert(
            severity="WARNING",
            category="data_quality",
            message="accuracy low",
            timestamp="2026-01-01T00:00:00Z",
            batch_id="b001",
            metric_name="accuracy",
            metric_value=80.0,
            threshold_value=98.0,
        )
        d = alert.to_dict()
        assert d["severity"] == "WARNING"
        assert d["metric_value"] == 80.0


class TestAlertManager:
    """Tests for the AlertManager."""

    def test_no_alerts_when_all_above_thresholds(self):
        """No alerts should fire when all metrics are above thresholds."""
        mgr = AlertManager()
        metrics = _make_metrics(
            freshness_score=100.0,
            completeness_score=100.0,
            accuracy_score=100.0,
            contract_adherence_score=100.0,
        )
        alerts = mgr.evaluate(metrics)
        assert len(alerts) == 0

    def test_warning_on_accuracy_below_warning_threshold(self):
        """A WARNING alert should fire when accuracy is below warning but above critical."""
        mgr = AlertManager(accuracy_warning=98.0, accuracy_critical=90.0)
        metrics = _make_metrics(accuracy_score=95.0)
        alerts = mgr.evaluate(metrics)

        accuracy_alerts = [a for a in alerts if a.metric_name == "accuracy"]
        assert len(accuracy_alerts) == 1
        assert accuracy_alerts[0].severity == "WARNING"

    def test_critical_on_accuracy_below_critical_threshold(self):
        """A CRITICAL alert should fire when accuracy is below critical threshold."""
        mgr = AlertManager(accuracy_critical=90.0)
        metrics = _make_metrics(accuracy_score=80.0)
        alerts = mgr.evaluate(metrics)

        accuracy_alerts = [a for a in alerts if a.metric_name == "accuracy"]
        assert len(accuracy_alerts) == 1
        assert accuracy_alerts[0].severity == "CRITICAL"

    def test_freshness_warning(self):
        """A warning should fire for low freshness score."""
        mgr = AlertManager(freshness_warning=50.0, freshness_critical=25.0)
        metrics = _make_metrics(freshness_score=40.0)
        alerts = mgr.evaluate(metrics)

        freshness_alerts = [a for a in alerts if a.metric_name == "freshness"]
        assert len(freshness_alerts) == 1
        assert freshness_alerts[0].severity == "WARNING"

    def test_completeness_critical(self):
        """A critical alert should fire for very low completeness."""
        mgr = AlertManager(completeness_critical=85.0)
        metrics = _make_metrics(completeness_score=70.0)
        alerts = mgr.evaluate(metrics)

        comp_alerts = [a for a in alerts if a.metric_name == "completeness"]
        assert len(comp_alerts) == 1
        assert comp_alerts[0].severity == "CRITICAL"

    def test_contract_adherence_warning(self):
        """A warning should fire when contract adherence drops."""
        mgr = AlertManager(adherence_warning=99.0, adherence_critical=95.0)
        metrics = _make_metrics(contract_adherence_score=97.0)
        alerts = mgr.evaluate(metrics)

        adh_alerts = [a for a in alerts if a.metric_name == "contract_adherence"]
        assert len(adh_alerts) == 1
        assert adh_alerts[0].severity == "WARNING"

    def test_pipeline_failure_alert(self):
        """A CRITICAL alert should fire when pipeline_status is FAILED."""
        mgr = AlertManager()
        metrics = _make_metrics(pipeline_status="FAILED")
        alerts = mgr.evaluate(metrics)

        pipe_alerts = [a for a in alerts if a.category == "pipeline"]
        assert len(pipe_alerts) == 1
        assert pipe_alerts[0].severity == "CRITICAL"

    def test_multiple_alerts_can_fire(self):
        """Multiple metrics below threshold should produce multiple alerts."""
        mgr = AlertManager(
            freshness_critical=50.0,
            completeness_critical=85.0,
            accuracy_critical=90.0,
        )
        metrics = _make_metrics(
            freshness_score=10.0,
            completeness_score=60.0,
            accuracy_score=50.0,
        )
        alerts = mgr.evaluate(metrics)
        assert len(alerts) >= 3

    def test_get_alerts_returns_all(self):
        """get_alerts should return all accumulated alerts."""
        mgr = AlertManager(accuracy_warning=98.0)
        m1 = _make_metrics(batch_id="b1", accuracy_score=95.0)
        m2 = _make_metrics(batch_id="b2", accuracy_score=94.0)

        mgr.evaluate(m1)
        mgr.evaluate(m2)

        all_alerts = mgr.get_alerts()
        assert len(all_alerts) >= 2

    def test_get_alerts_filtered_by_severity(self):
        """get_alerts with severity filter should only return matching alerts."""
        mgr = AlertManager(accuracy_warning=98.0, accuracy_critical=90.0)
        metrics = _make_metrics(accuracy_score=85.0)  # below critical
        mgr.evaluate(metrics)

        critical = mgr.get_alerts(severity="CRITICAL")
        assert all(a.severity == "CRITICAL" for a in critical)

    def test_get_recent_alerts(self):
        """get_recent_alerts should respect the limit parameter."""
        mgr = AlertManager(accuracy_warning=100.0)

        for i in range(10):
            mgr.evaluate(_make_metrics(batch_id=f"b_{i}", accuracy_score=90.0))

        recent = mgr.get_recent_alerts(limit=3)
        assert len(recent) == 3

    def test_clear_alerts(self):
        """clear_alerts should empty the alert history."""
        mgr = AlertManager(accuracy_warning=100.0)
        mgr.evaluate(_make_metrics(accuracy_score=50.0))
        assert len(mgr.get_alerts()) > 0

        mgr.clear_alerts()
        assert len(mgr.get_alerts()) == 0

    def test_alert_contains_metric_details(self):
        """Alert should contain metric value and threshold for debugging."""
        mgr = AlertManager(freshness_warning=50.0, freshness_critical=25.0)
        metrics = _make_metrics(freshness_score=30.0)
        alerts = mgr.evaluate(metrics)

        freshness_alert = [a for a in alerts if a.metric_name == "freshness"][0]
        assert freshness_alert.metric_value == 30.0
        assert freshness_alert.threshold_value == 50.0
        assert freshness_alert.batch_id == "b_test"
