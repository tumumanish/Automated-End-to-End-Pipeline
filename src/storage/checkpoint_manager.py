"""
Module: checkpoint_manager
Purpose:
    Save and restore pipeline checkpoints for recovery and replayability.
    Checkpoints capture the pipeline state after each completed stage so
    execution can be resumed from the last successful point.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from src.utils.file_utils import get_project_root, ensure_directory
from src.utils.logger import get_logger
from src.utils.timestamps import utc_now

logger = get_logger("storage.checkpoint")


@dataclass
class Checkpoint:
    """Represents a pipeline execution checkpoint."""
    execution_id: str
    pipeline_name: str
    last_completed_stage: str
    timestamp: str  # ISO-format string for JSON serialisation
    state: dict     # Serialisable pipeline state (paths, counts, etc.)

    def to_dict(self) -> dict:
        return asdict(self)


class CheckpointManager:
    """
    Manages pipeline checkpoints on the local filesystem.

    Storage pattern:
        data/staging/checkpoints/<pipeline_name>/<execution_id>.json
    """

    def __init__(self, checkpoint_dir: Path | None = None):
        self._root = checkpoint_dir or (get_project_root() / "data" / "staging" / "checkpoints")
        ensure_directory(self._root)

    def save(
        self,
        execution_id: str,
        pipeline_name: str,
        stage: str,
        state: dict,
    ) -> Path:
        """
        Save a checkpoint after a pipeline stage completes.

        Args:
            execution_id: Current execution identifier.
            pipeline_name: Name of the pipeline.
            stage: The stage that just completed.
            state: Serialisable dict capturing current pipeline state.

        Returns:
            Path to the saved checkpoint file.
        """
        pipeline_dir = ensure_directory(self._root / pipeline_name)
        checkpoint = Checkpoint(
            execution_id=execution_id,
            pipeline_name=pipeline_name,
            last_completed_stage=stage,
            timestamp=utc_now().isoformat(),
            state=state,
        )

        filepath = pipeline_dir / f"{execution_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(checkpoint.to_dict(), f, indent=2, default=str)

        logger.info(
            "Checkpoint saved | exec=%s pipeline=%s stage=%s",
            execution_id, pipeline_name, stage,
        )
        return filepath

    def restore(self, execution_id: str, pipeline_name: str) -> Optional[Checkpoint]:
        """
        Restore a checkpoint for a specific execution.

        Args:
            execution_id: The execution to restore.
            pipeline_name: Pipeline name.

        Returns:
            Checkpoint object or None if not found.
        """
        filepath = self._root / pipeline_name / f"{execution_id}.json"
        if not filepath.is_file():
            logger.debug("No checkpoint found for exec=%s", execution_id)
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(
            "Checkpoint restored | exec=%s stage=%s",
            execution_id, data.get("last_completed_stage"),
        )
        return Checkpoint(**data)

    def get_latest(self, pipeline_name: str) -> Optional[Checkpoint]:
        """
        Get the most recent checkpoint for a pipeline.

        Args:
            pipeline_name: Pipeline name.

        Returns:
            Latest Checkpoint or None.
        """
        pipeline_dir = self._root / pipeline_name
        if not pipeline_dir.is_dir():
            return None

        checkpoint_files = sorted(pipeline_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not checkpoint_files:
            return None

        with open(checkpoint_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)

        return Checkpoint(**data)

    def list_checkpoints(self, pipeline_name: str) -> List[Checkpoint]:
        """
        List all checkpoints for a pipeline, newest first.

        Args:
            pipeline_name: Pipeline name.

        Returns:
            List of Checkpoint objects.
        """
        pipeline_dir = self._root / pipeline_name
        if not pipeline_dir.is_dir():
            return []

        checkpoints = []
        for filepath in sorted(pipeline_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            checkpoints.append(Checkpoint(**data))

        return checkpoints

    def delete(self, execution_id: str, pipeline_name: str) -> bool:
        """Delete a specific checkpoint."""
        filepath = self._root / pipeline_name / f"{execution_id}.json"
        if filepath.is_file():
            filepath.unlink()
            logger.info("Checkpoint deleted | exec=%s", execution_id)
            return True
        return False

    def cleanup(self, pipeline_name: str, keep_last: int = 10) -> int:
        """
        Remove old checkpoints, keeping only the most recent N.

        Args:
            pipeline_name: Pipeline name.
            keep_last: Number of recent checkpoints to retain.

        Returns:
            Number of checkpoints removed.
        """
        pipeline_dir = self._root / pipeline_name
        if not pipeline_dir.is_dir():
            return 0

        files = sorted(pipeline_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        to_remove = files[keep_last:]
        for f in to_remove:
            f.unlink()

        if to_remove:
            logger.info(
                "Checkpoint cleanup | pipeline=%s removed=%d kept=%d",
                pipeline_name, len(to_remove), keep_last,
            )
        return len(to_remove)
