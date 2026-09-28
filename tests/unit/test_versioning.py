"""
Unit Tests: Versioning Module

Tests for data versioning, record hashing, and checkpoint management.
"""

import pytest
import tempfile
from pathlib import Path

import pandas as pd

from src.utils.hashing import hash_record, hash_dataframe, hash_batch
from src.storage.versioning import DataVersionManager, VersionStore, VersionedRecord
from src.storage.checkpoint_manager import CheckpointManager, Checkpoint


# ──────────────────────────────────────────────────
# Hashing Tests
# ──────────────────────────────────────────────────

class TestHashing:
    """Tests for the hashing utility module."""

    def test_hash_record_deterministic(self):
        """Same record should always produce the same hash."""
        row = {"name": "Alice", "age": 30, "city": "Delhi"}
        h1 = hash_record(row)
        h2 = hash_record(row)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest

    def test_hash_record_different_values(self):
        """Different records should produce different hashes."""
        r1 = {"name": "Alice", "age": 30}
        r2 = {"name": "Bob", "age": 25}
        assert hash_record(r1) != hash_record(r2)

    def test_hash_record_excludes_meta_columns(self):
        """Metadata columns should be excluded from hash by default."""
        r1 = {"name": "Alice", "age": 30}
        r2 = {"name": "Alice", "age": 30, "batch_id": "b001", "execution_id": "e001"}
        assert hash_record(r1) == hash_record(r2)

    def test_hash_record_custom_exclude(self):
        """Custom exclusion columns should be respected."""
        r1 = {"name": "Alice", "age": 30, "temp": "x"}
        r2 = {"name": "Alice", "age": 30, "temp": "y"}
        assert hash_record(r1, exclude_columns=["temp"]) == hash_record(r2, exclude_columns=["temp"])

    def test_hash_dataframe(self):
        """DataFrame should get a hash column appended."""
        df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})
        result = hash_dataframe(df)
        assert "_record_hash" in result.columns
        assert len(result) == 2
        assert result["_record_hash"].iloc[0] != result["_record_hash"].iloc[1]

    def test_hash_batch(self):
        """Batch hash should be deterministic."""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        h1 = hash_batch(df)
        h2 = hash_batch(df)
        assert h1 == h2


# ──────────────────────────────────────────────────
# Versioning Tests
# ──────────────────────────────────────────────────

class TestVersioning:
    """Tests for SCD Type 2 data versioning."""

    def _make_df(self, records):
        return pd.DataFrame(records)

    def test_new_records_inserted(self):
        """New records should be inserted with is_current=True."""
        mgr = DataVersionManager()
        df = self._make_df([
            {"transaction_id": "T001", "amount": 100},
            {"transaction_id": "T002", "amount": 200},
        ])

        stats = mgr.apply_versioning(df, "transactions", "csv", "b001", "transaction_id")
        assert stats["new"] == 2
        assert stats["changed"] == 0
        assert stats["unchanged"] == 0

        snapshot = mgr.get_current_snapshot("transactions")
        assert len(snapshot) == 2

    def test_unchanged_records_skipped(self):
        """Identical re-ingestion should skip records."""
        mgr = DataVersionManager()
        df = self._make_df([{"transaction_id": "T001", "amount": 100}])

        mgr.apply_versioning(df, "transactions", "csv", "b001", "transaction_id")
        stats = mgr.apply_versioning(df, "transactions", "csv", "b002", "transaction_id")

        assert stats["unchanged"] == 1
        assert stats["new"] == 0
        assert stats["changed"] == 0

    def test_changed_records_versioned(self):
        """Changed records should create new version and expire old one."""
        mgr = DataVersionManager()

        df1 = self._make_df([{"transaction_id": "T001", "amount": 100}])
        mgr.apply_versioning(df1, "transactions", "csv", "b001", "transaction_id")

        df2 = self._make_df([{"transaction_id": "T001", "amount": 150}])
        stats = mgr.apply_versioning(df2, "transactions", "csv", "b002", "transaction_id")

        assert stats["changed"] == 1
        history = mgr.store.get_version_history("T001", "transactions")
        assert len(history) == 2
        assert history[0].is_current is False
        assert history[1].is_current is True

    def test_rollback_batch(self):
        """Rollback should remove batch records and re-activate previous."""
        mgr = DataVersionManager()

        df1 = self._make_df([{"transaction_id": "T001", "amount": 100}])
        mgr.apply_versioning(df1, "transactions", "csv", "b001", "transaction_id")

        df2 = self._make_df([{"transaction_id": "T001", "amount": 150}])
        mgr.apply_versioning(df2, "transactions", "csv", "b002", "transaction_id")

        rolled = mgr.rollback_batch("b002", "transactions")
        assert rolled == 1

        snapshot = mgr.get_current_snapshot("transactions")
        assert len(snapshot) == 1
        assert snapshot[0].batch_id == "b001"


# ──────────────────────────────────────────────────
# Checkpoint Tests
# ──────────────────────────────────────────────────

class TestCheckpointManager:
    """Tests for checkpoint management."""

    @pytest.fixture
    def mgr(self, tmp_path):
        return CheckpointManager(checkpoint_dir=tmp_path)

    def test_save_and_restore(self, mgr):
        """Save a checkpoint and restore it."""
        mgr.save("exec_001", "etlt_plus_plus", "extract", {"count": 100})
        cp = mgr.restore("exec_001", "etlt_plus_plus")

        assert cp is not None
        assert cp.execution_id == "exec_001"
        assert cp.last_completed_stage == "extract"
        assert cp.state["count"] == 100

    def test_restore_nonexistent(self, mgr):
        """Restoring a non-existent checkpoint returns None."""
        cp = mgr.restore("no_such_exec", "no_pipeline")
        assert cp is None

    def test_get_latest(self, mgr):
        """Get latest checkpoint for a pipeline."""
        import time
        mgr.save("exec_001", "etlt_plus_plus", "extract", {"step": 1})
        time.sleep(0.05)  # Ensure different mtime
        mgr.save("exec_002", "etlt_plus_plus", "validate", {"step": 2})

        latest = mgr.get_latest("etlt_plus_plus")
        assert latest is not None
        assert latest.execution_id == "exec_002"

    def test_delete(self, mgr):
        """Delete a checkpoint."""
        mgr.save("exec_001", "etlt_plus_plus", "extract", {})
        assert mgr.delete("exec_001", "etlt_plus_plus") is True
        assert mgr.restore("exec_001", "etlt_plus_plus") is None

    def test_cleanup_keeps_recent(self, mgr):
        """Cleanup should keep only the N most recent checkpoints."""
        for i in range(5):
            mgr.save(f"exec_{i:03d}", "etlt_plus_plus", "extract", {"i": i})

        removed = mgr.cleanup("etlt_plus_plus", keep_last=2)
        assert removed == 3

        remaining = mgr.list_checkpoints("etlt_plus_plus")
        assert len(remaining) == 2
