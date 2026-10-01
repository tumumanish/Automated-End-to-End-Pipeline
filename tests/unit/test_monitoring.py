"""
Unit Tests: Monitoring Module

Tests for individual quality monitors: Freshness, Completeness,
Accuracy, and Contract Adherence.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.monitoring.freshness import FreshnessMonitor
from src.monitoring.completeness import CompletenessMonitor
from src.monitoring.accuracy import AccuracyMonitor
from src.monitoring.contract_adherence import ContractAdherenceMonitor
from src.monitoring.pipeline_metrics import PipelineMetricsTracker
from src.contracts.validation_result import ValidationResult


# ──────────────────────────────────────────────────
# Freshness Monitor Tests
# ──────────────────────────────────────────────────

class TestFreshnessMonitor:
    """Tests for FreshnessMonitor."""

    def test_perfect_freshness(self):
        """Data just ingested should have score ~100."""
        monitor = FreshnessMonitor(max_age_hours=24.0)
        now = datetime.now(timezone.utc)
        score = monitor.calculate_score(now)
        assert score >= 99.0

    def test_expired_freshness(self):
        """Data older than max_age should have score 0."""
        monitor = FreshnessMonitor(max_age_hours=24.0)
        old_time = datetime.now(timezone.utc) - timedelta(hours=48)
        score = monitor.calculate_score(old_time)
        assert score == 0.0

    def test_half_life_freshness(self):
        """Data at half the max age should have score ~50."""
        monitor = FreshnessMonitor(max_age_hours=24.0)
        half_old = datetime.now(timezone.utc) - timedelta(hours=12)
        score = monitor.calculate_score(half_old)
        assert 45.0 <= score <= 55.0

    def test_is_fresh(self):
        """is_fresh should return True for recent data."""
        monitor = FreshnessMonitor(max_age_hours=24.0)
        assert monitor.is_fresh(datetime.now(timezone.utc)) is True

    def test_is_not_fresh(self):
        """is_fresh should return False for expired data."""
        monitor = FreshnessMonitor(max_age_hours=1.0)
        old = datetime.now(timezone.utc) - timedelta(hours=2)
        assert monitor.is_fresh(old) is False

    def test_naive_datetime_handled(self):
        """Naive datetimes should be handled without error."""
        monitor = FreshnessMonitor(max_age_hours=24.0)
        naive = datetime.utcnow()
        score = monitor.calculate_score(naive)
        assert 0.0 <= score <= 100.0


# ──────────────────────────────────────────────────
# Completeness Monitor Tests
# ──────────────────────────────────────────────────

class TestCompletenessMonitor:
    """Tests for CompletenessMonitor."""

    def test_fully_complete_data(self):
        """DataFrame with no nulls should score 100."""
        monitor = CompletenessMonitor()
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        assert monitor.calculate_score(df) == 100.0

    def test_empty_dataframe(self):
        """Empty DataFrame should score 0."""
        monitor = CompletenessMonitor()
        assert monitor.calculate_score(pd.DataFrame()) == 0.0

    def test_partial_nulls(self):
        """DataFrame with some nulls should score between 0 and 100."""
        monitor = CompletenessMonitor()
        df = pd.DataFrame({"a": [1, None, 3], "b": ["x", "y", None]})
        score = monitor.calculate_score(df)
        # 4/6 cells are non-null = 66.67
        assert 65.0 <= score <= 68.0

    def test_per_field_scores(self):
        """per_field_scores should return individual column scores."""
        monitor = CompletenessMonitor()
        df = pd.DataFrame({"a": [1, 2, None], "b": ["x", "y", "z"]})
        scores = monitor.per_field_scores(df)
        assert scores["a"] == pytest.approx(66.67, abs=0.1)
        assert scores["b"] == 100.0

    def test_is_complete_passes(self):
        """is_complete should be True when above threshold."""
        monitor = CompletenessMonitor(min_percent=90.0)
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        assert monitor.is_complete(df) == True

    def test_is_complete_fails(self):
        """is_complete should be False when below threshold."""
        monitor = CompletenessMonitor(min_percent=90.0)
        df = pd.DataFrame({"a": [1, None, None], "b": [None, None, None]})
        assert monitor.is_complete(df) == False

    def test_get_incomplete_fields(self):
        """get_incomplete_fields should return only fields below threshold."""
        monitor = CompletenessMonitor(min_percent=90.0)
        df = pd.DataFrame({"a": [1, None, 3], "b": ["x", "y", "z"]})
        incomplete = monitor.get_incomplete_fields(df)
        assert "a" in incomplete
        assert "b" not in incomplete


# ──────────────────────────────────────────────────
# Accuracy Monitor Tests
# ──────────────────────────────────────────────────

class TestAccuracyMonitor:
    """Tests for AccuracyMonitor."""

    def _make_result(self, total, valid):
        return ValidationResult(
            dataset="test",
            contract_version="1.0",
            total_records=total,
            valid_records=valid,
            invalid_records=total - valid,
            status="PASS" if valid == total else "FAIL",
        )

    def test_perfect_accuracy(self):
        """All valid records should score 100."""
        monitor = AccuracyMonitor()
        result = self._make_result(100, 100)
        assert monitor.calculate_score(result) == 100.0

    def test_zero_accuracy(self):
        """No valid records should score 0."""
        monitor = AccuracyMonitor()
        result = self._make_result(100, 0)
        assert monitor.calculate_score(result) == 0.0

    def test_partial_accuracy(self):
        """Partial validity should produce proportional score."""
        monitor = AccuracyMonitor()
        result = self._make_result(100, 90)
        assert monitor.calculate_score(result) == 90.0

    def test_empty_dataset_accuracy(self):
        """Empty dataset should default to 100."""
        monitor = AccuracyMonitor()
        result = self._make_result(0, 0)
        assert monitor.calculate_score(result) == 100.0

    def test_calculate_from_counts(self):
        """calculate_from_counts should work with raw numbers."""
        monitor = AccuracyMonitor()
        assert monitor.calculate_from_counts(200, 190) == 95.0

    def test_is_accurate_passes(self):
        """is_accurate should return True when above threshold."""
        monitor = AccuracyMonitor(min_percent=95.0)
        result = self._make_result(100, 98)
        assert monitor.is_accurate(result) is True

    def test_is_accurate_fails(self):
        """is_accurate should return False when below threshold."""
        monitor = AccuracyMonitor(min_percent=95.0)
        result = self._make_result(100, 90)
        assert monitor.is_accurate(result) is False


# ──────────────────────────────────────────────────
# Contract Adherence Monitor Tests
# ──────────────────────────────────────────────────

class TestContractAdherenceMonitor:
    """Tests for ContractAdherenceMonitor."""

    def test_all_batches_pass(self):
        """All passing batches should score 100."""
        monitor = ContractAdherenceMonitor()
        monitor.record_batch("b1", passed=True)
        monitor.record_batch("b2", passed=True)
        assert monitor.calculate_score() == 100.0

    def test_no_batches_recorded(self):
        """No recorded batches should default to 100."""
        monitor = ContractAdherenceMonitor()
        assert monitor.calculate_score() == 100.0

    def test_partial_adherence(self):
        """Mixed pass/fail should produce proportional score."""
        monitor = ContractAdherenceMonitor()
        monitor.record_batch("b1", passed=True)
        monitor.record_batch("b2", passed=False)
        assert monitor.calculate_score() == 50.0

    def test_is_adherent(self):
        """is_adherent should reflect the threshold check."""
        monitor = ContractAdherenceMonitor(min_percent=90.0)
        for i in range(10):
            monitor.record_batch(f"b{i}", passed=True)
        assert monitor.is_adherent() is True

    def test_is_not_adherent(self):
        """is_adherent should be False when below threshold."""
        monitor = ContractAdherenceMonitor(min_percent=90.0)
        for i in range(5):
            monitor.record_batch(f"pass_{i}", passed=True)
        for i in range(5):
            monitor.record_batch(f"fail_{i}", passed=False)
        assert monitor.is_adherent() is False

    def test_get_failed_batches(self):
        """get_failed_batches should return only failures."""
        monitor = ContractAdherenceMonitor()
        monitor.record_batch("b1", passed=True)
        monitor.record_batch("b2", passed=False, details="schema mismatch")
        monitor.record_batch("b3", passed=False, details="null violation")

        failed = monitor.get_failed_batches()
        assert len(failed) == 2
        assert failed[0]["batch_id"] == "b2"

    def test_reset_clears_history(self):
        """reset should clear all recorded batches."""
        monitor = ContractAdherenceMonitor()
        monitor.record_batch("b1", passed=True)
        monitor.reset()
        assert monitor.calculate_score() == 100.0

    def test_calculate_from_counts(self):
        """calculate_from_counts should work with raw numbers."""
        monitor = ContractAdherenceMonitor()
        assert monitor.calculate_from_counts(10, 9) == 90.0


# ──────────────────────────────────────────────────
# Pipeline Metrics Tracker Tests
# ──────────────────────────────────────────────────

class TestPipelineMetricsTracker:
    """Tests for PipelineMetricsTracker."""

    def test_record_and_retrieve_executions(self):
        """Recording executions should make them retrievable."""
        tracker = PipelineMetricsTracker()
        tracker.record_execution("etlt_plus_plus", "e1", "SUCCESS", "t1", 2.0)
        tracker.record_execution("etlt_plus_plus", "e2", "FAILED", "t2", 1.0)

        executions = tracker.get_executions("etlt_plus_plus")
        assert len(executions) == 2

    def test_success_rate(self):
        """Success rate should be calculated correctly."""
        tracker = PipelineMetricsTracker()
        tracker.record_execution("p", "e1", "SUCCESS", "t1", 1.0)
        tracker.record_execution("p", "e2", "SUCCESS", "t2", 2.0)
        tracker.record_execution("p", "e3", "FAILED", "t3", 0.5)

        assert tracker.get_success_rate("p") == pytest.approx(66.67, abs=0.1)

    def test_avg_duration(self):
        """Average duration should be calculated correctly."""
        tracker = PipelineMetricsTracker()
        tracker.record_execution("p", "e1", "SUCCESS", "t1", 2.0)
        tracker.record_execution("p", "e2", "SUCCESS", "t2", 4.0)

        assert tracker.get_avg_duration("p") == 3.0

    def test_throughput(self):
        """Throughput should be avg records per execution."""
        tracker = PipelineMetricsTracker()
        tracker.record_execution("p", "e1", "SUCCESS", "t1", 1.0, records_extracted=100)
        tracker.record_execution("p", "e2", "SUCCESS", "t2", 1.0, records_extracted=200)

        assert tracker.get_throughput("p") == 150.0

    def test_empty_tracker_defaults(self):
        """Empty tracker should return safe default values."""
        tracker = PipelineMetricsTracker()
        assert tracker.get_success_rate() == 100.0
        assert tracker.get_avg_duration() == 0.0
        assert tracker.get_throughput() == 0.0
