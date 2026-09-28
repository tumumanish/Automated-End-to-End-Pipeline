"""
Unit Tests: Lineage Module

Tests for lineage tracking, storage, and metadata collection.
"""

import pytest
import tempfile
from pathlib import Path

import pandas as pd

from src.lineage.lineage_tracker import LineageTracker, LineageEvent
from src.lineage.lineage_store import LineageStore
from src.lineage.metadata_collector import MetadataCollector


# ──────────────────────────────────────────────────
# LineageTracker Tests
# ──────────────────────────────────────────────────

class TestLineageTracker:
    """Tests for the LineageTracker."""

    def test_record_event(self):
        """Recording a lineage event should add it to the tracker."""
        tracker = LineageTracker(
            batch_id="b001",
            pipeline_name="etlt_plus_plus",
            dataset_name="transactions",
            source_system="csv",
        )
        event = tracker.record("extract", input_count=0, output_count=100)

        assert isinstance(event, LineageEvent)
        assert event.stage == "extract"
        assert event.input_record_count == 0
        assert event.output_record_count == 100
        assert event.batch_id == "b001"

    def test_multiple_events_in_order(self):
        """Events should be stored in recording order."""
        tracker = LineageTracker("b001", "etlt_plus_plus", "tx", "csv")
        tracker.record("extract", output_count=100)
        tracker.record("validate", input_count=100, output_count=95)
        tracker.record("transform", input_count=95, output_count=95)

        events = tracker.get_events()
        assert len(events) == 3
        assert events[0].stage == "extract"
        assert events[1].stage == "validate"
        assert events[2].stage == "transform"

    def test_lineage_summary(self):
        """Summary should contain batch/pipeline info and stage list."""
        tracker = LineageTracker("b001", "etlt_plus_plus", "tx", "csv", "1.0")
        tracker.record("extract", output_count=100)
        tracker.record("validate", input_count=100, output_count=90)

        summary = tracker.get_lineage_summary()
        assert summary["batch_id"] == "b001"
        assert summary["pipeline_name"] == "etlt_plus_plus"
        assert summary["total_stages"] == 2
        assert len(summary["stages"]) == 2

    def test_metadata_in_event(self):
        """Custom metadata should be attached to lineage events."""
        tracker = LineageTracker("b001", "etlt", "tx", "api")
        event = tracker.record("extract", metadata={"url": "http://example.com"})
        assert event.metadata["url"] == "http://example.com"


# ──────────────────────────────────────────────────
# LineageStore Tests
# ──────────────────────────────────────────────────

class TestLineageStore:
    """Tests for the LineageStore."""

    @pytest.fixture
    def store(self, tmp_path):
        return LineageStore(store_dir=tmp_path)

    def _make_events(self, batch_id="b001", pipeline="etlt", dataset="tx"):
        return [
            LineageEvent(
                event_id=f"evt_{i}",
                batch_id=batch_id,
                pipeline_name=pipeline,
                stage=stage,
                dataset_name=dataset,
                input_record_count=100,
                output_record_count=95,
                timestamp="2024-01-01T00:00:00+00:00",
            )
            for i, stage in enumerate(["extract", "validate", "transform"])
        ]

    def test_save_and_load(self, store):
        """Events should be saved and reloaded correctly."""
        events = self._make_events()
        store.save_events(events)

        loaded = store.load_events("b001")
        assert len(loaded) == 3
        assert loaded[0].stage == "extract"
        assert loaded[2].stage == "transform"

    def test_load_nonexistent(self, store):
        """Loading a non-existent batch should return empty list."""
        assert store.load_events("no_batch") == []

    def test_query_by_dataset(self, store):
        """Query by dataset should return matching events."""
        events = self._make_events(dataset="sales")
        store.save_events(events)

        results = store.query_by_dataset("sales")
        assert len(results) == 3

    def test_get_all_batches(self, store):
        """Should list all batches with lineage data."""
        store.save_events(self._make_events(batch_id="b001"))
        store.save_events(self._make_events(batch_id="b002"))

        batches = store.get_all_batches()
        assert "b001" in batches
        assert "b002" in batches


# ──────────────────────────────────────────────────
# MetadataCollector Tests
# ──────────────────────────────────────────────────

class TestMetadataCollector:
    """Tests for the MetadataCollector."""

    def test_collect_dataset_metadata(self):
        """Should collect correct metadata from a DataFrame."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", None],
            "amount": [100.0, 200.0, 300.0],
        })

        meta = MetadataCollector.collect_dataset_metadata(df, "test", "extract")
        assert meta.dataset_name == "test"
        assert meta.stage == "extract"
        assert meta.row_count == 3
        assert meta.column_count == 3
        assert "id" in meta.columns
        assert meta.null_counts["name"] == 1
        assert meta.null_counts["id"] == 0

    def test_create_pipeline_metadata(self):
        """Should create pipeline metadata with correct fields."""
        meta = MetadataCollector.create_pipeline_metadata(
            execution_id="exec_001",
            pipeline_name="etlt_plus_plus",
            source_type="csv",
            dataset_name="transactions",
            total_stages=5,
        )
        assert meta.execution_id == "exec_001"
        assert meta.status == "RUNNING"
        assert meta.total_stages == 5

    def test_finalise_pipeline_metadata(self):
        """Should update pipeline metadata on finalisation."""
        meta = MetadataCollector.create_pipeline_metadata(
            "exec_001", "etlt", "csv", "tx", 4,
        )
        meta = MetadataCollector.finalise_pipeline_metadata(
            meta, status="SUCCESS", duration=5.5, stages_completed=4,
        )
        assert meta.status == "SUCCESS"
        assert meta.duration_seconds == 5.5
        assert meta.completed_at is not None
