"""
Unit Tests: Checkpoint Manager

Tests for checkpoint save/restore, listing, deletion, and cleanup.
"""

import json
import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.checkpoint_manager import CheckpointManager, Checkpoint


class TestCheckpoint:
    """Tests for the Checkpoint dataclass."""

    def test_checkpoint_creation(self):
        """A Checkpoint should hold all required fields."""
        cp = Checkpoint(
            execution_id="exec_001",
            pipeline_name="etlt_plus_plus",
            last_completed_stage="extract",
            timestamp="2026-01-01T00:00:00Z",
            state={"extracted_count": 100},
        )
        assert cp.execution_id == "exec_001"
        assert cp.pipeline_name == "etlt_plus_plus"
        assert cp.last_completed_stage == "extract"
        assert cp.state["extracted_count"] == 100

    def test_checkpoint_to_dict(self):
        """to_dict should produce a serialisable dictionary."""
        cp = Checkpoint(
            execution_id="exec_002",
            pipeline_name="eltl",
            last_completed_stage="validate",
            timestamp="2026-01-01T12:00:00Z",
            state={"valid": 50, "invalid": 5},
        )
        d = cp.to_dict()
        assert d["execution_id"] == "exec_002"
        assert d["state"]["valid"] == 50


class TestCheckpointManager:
    """Tests for the CheckpointManager."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a CheckpointManager with a temp directory."""
        return CheckpointManager(checkpoint_dir=tmp_path)

    def test_save_creates_file(self, manager, tmp_path):
        """Saving a checkpoint should create a JSON file on disk."""
        path = manager.save(
            execution_id="exec_100",
            pipeline_name="etlt_plus_plus",
            stage="extract",
            state={"count": 42},
        )
        assert path.is_file()
        assert path.suffix == ".json"

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["execution_id"] == "exec_100"
        assert data["last_completed_stage"] == "extract"
        assert data["state"]["count"] == 42

    def test_restore_returns_checkpoint(self, manager):
        """Restoring a saved checkpoint should return the Checkpoint object."""
        manager.save("exec_200", "etlt_plus_plus", "validate", {"valid": 90})

        cp = manager.restore("exec_200", "etlt_plus_plus")
        assert cp is not None
        assert isinstance(cp, Checkpoint)
        assert cp.execution_id == "exec_200"
        assert cp.last_completed_stage == "validate"
        assert cp.state["valid"] == 90

    def test_restore_nonexistent_returns_none(self, manager):
        """Restoring a non-existent checkpoint should return None."""
        cp = manager.restore("nonexistent_exec", "etlt_plus_plus")
        assert cp is None

    def test_get_latest(self, manager):
        """get_latest should return the most recently saved checkpoint."""
        import time
        manager.save("exec_a", "etlt_plus_plus", "extract", {"step": 1})
        time.sleep(0.05)
        manager.save("exec_b", "etlt_plus_plus", "validate", {"step": 2})
        time.sleep(0.05)
        manager.save("exec_c", "etlt_plus_plus", "transform", {"step": 3})

        latest = manager.get_latest("etlt_plus_plus")
        assert latest is not None
        assert latest.execution_id == "exec_c"
        assert latest.last_completed_stage == "transform"

    def test_get_latest_no_checkpoints(self, manager):
        """get_latest should return None when no checkpoints exist."""
        assert manager.get_latest("nonexistent_pipeline") is None

    def test_list_checkpoints(self, manager):
        """list_checkpoints should return all checkpoints for a pipeline."""
        manager.save("exec_1", "eltl", "extract", {})
        manager.save("exec_2", "eltl", "validate", {})
        manager.save("exec_3", "eltl", "transform", {})

        cps = manager.list_checkpoints("eltl")
        assert len(cps) == 3

    def test_list_checkpoints_empty(self, manager):
        """list_checkpoints should return empty list for unknown pipeline."""
        cps = manager.list_checkpoints("unknown_pipeline")
        assert cps == []

    def test_delete_removes_checkpoint(self, manager):
        """delete should remove the checkpoint file."""
        manager.save("exec_del", "etlt", "extract", {})
        assert manager.restore("exec_del", "etlt") is not None

        deleted = manager.delete("exec_del", "etlt")
        assert deleted is True
        assert manager.restore("exec_del", "etlt") is None

    def test_delete_nonexistent_returns_false(self, manager):
        """delete should return False for non-existent checkpoint."""
        assert manager.delete("nonexistent", "etlt") is False

    def test_cleanup_keeps_recent(self, manager):
        """cleanup should keep only the N most recent checkpoints."""
        for i in range(5):
            manager.save(f"exec_{i}", "etlt_plus_plus", f"stage_{i}", {"i": i})

        removed = manager.cleanup("etlt_plus_plus", keep_last=2)
        assert removed == 3

        remaining = manager.list_checkpoints("etlt_plus_plus")
        assert len(remaining) == 2

    def test_cleanup_no_removal_needed(self, manager):
        """cleanup should remove nothing when within retention limit."""
        manager.save("exec_only", "eltl", "extract", {})

        removed = manager.cleanup("eltl", keep_last=5)
        assert removed == 0

    def test_save_overwrites_same_execution(self, manager):
        """Saving with same execution_id should overwrite the file."""
        manager.save("exec_ow", "etlt_plus_plus", "extract", {"step": 1})
        manager.save("exec_ow", "etlt_plus_plus", "validate", {"step": 2})

        cp = manager.restore("exec_ow", "etlt_plus_plus")
        assert cp.last_completed_stage == "validate"
        assert cp.state["step"] == 2

    def test_different_pipelines_isolated(self, manager):
        """Checkpoints from different pipelines should be isolated."""
        manager.save("exec_1", "pipeline_a", "extract", {"p": "a"})
        manager.save("exec_1", "pipeline_b", "extract", {"p": "b"})

        cp_a = manager.restore("exec_1", "pipeline_a")
        cp_b = manager.restore("exec_1", "pipeline_b")

        assert cp_a.state["p"] == "a"
        assert cp_b.state["p"] == "b"
