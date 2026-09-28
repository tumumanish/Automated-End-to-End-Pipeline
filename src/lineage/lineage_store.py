"""
Module: lineage_store
Purpose:
    Persist and query lineage records.
    Supports both file-based (JSON) and database-based persistence.
"""

import json
from pathlib import Path
from typing import List, Optional

from src.lineage.lineage_tracker import LineageEvent
from src.utils.file_utils import get_project_root, ensure_directory
from src.utils.logger import get_logger

logger = get_logger("lineage")


class LineageStore:
    """
    Persistent storage for lineage events.

    Supports:
      - File-based persistence (JSON files per batch)
      - In-memory querying by batch, dataset, or pipeline
    """

    def __init__(self, store_dir: Path | None = None):
        self._root = store_dir or (get_project_root() / "logs" / "lineage")
        ensure_directory(self._root)
        self._events: List[LineageEvent] = []

    def save_events(self, events: List[LineageEvent]) -> Path:
        """
        Persist a list of lineage events to a JSON file.

        Args:
            events: List of LineageEvent objects to persist.

        Returns:
            Path to the saved file.
        """
        if not events:
            return self._root

        batch_id = events[0].batch_id
        filepath = self._root / f"{batch_id}_lineage.json"

        payload = {
            "batch_id": batch_id,
            "pipeline": events[0].pipeline_name,
            "dataset": events[0].dataset_name,
            "event_count": len(events),
            "events": [e.to_dict() for e in events],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

        # Also keep in memory for querying
        self._events.extend(events)

        logger.info("Lineage saved | batch=%s events=%d -> %s", batch_id, len(events), filepath)
        return filepath

    def load_events(self, batch_id: str) -> List[LineageEvent]:
        """
        Load lineage events for a specific batch from file.

        Args:
            batch_id: The batch identifier.

        Returns:
            List of LineageEvent objects.
        """
        filepath = self._root / f"{batch_id}_lineage.json"
        if not filepath.is_file():
            return []

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        events = []
        for item in data.get("events", []):
            events.append(LineageEvent(**item))

        return events

    def query_by_dataset(self, dataset_name: str) -> List[LineageEvent]:
        """Query all lineage events for a dataset across batches."""
        # Search in-memory first
        results = [e for e in self._events if e.dataset_name == dataset_name]
        if results:
            return results

        # Fall back to scanning files
        results = []
        for filepath in self._root.glob("*_lineage.json"):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("dataset") == dataset_name:
                for item in data.get("events", []):
                    results.append(LineageEvent(**item))

        return results

    def query_by_pipeline(self, pipeline_name: str) -> List[LineageEvent]:
        """Query all lineage events for a specific pipeline."""
        results = [e for e in self._events if e.pipeline_name == pipeline_name]
        if results:
            return results

        results = []
        for filepath in self._root.glob("*_lineage.json"):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("pipeline") == pipeline_name:
                for item in data.get("events", []):
                    results.append(LineageEvent(**item))

        return results

    def get_all_batches(self) -> List[str]:
        """List all batch IDs with lineage data."""
        batches = set()
        for filepath in self._root.glob("*_lineage.json"):
            name = filepath.stem.replace("_lineage", "")
            batches.add(name)
        return sorted(batches)
