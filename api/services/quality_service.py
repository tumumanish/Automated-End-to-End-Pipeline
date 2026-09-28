"""
Service: quality_service
Purpose:
    Business logic layer for data quality API operations.
"""

import json
from pathlib import Path
from typing import List, Optional

from src.utils.file_utils import get_project_root


class QualityService:
    """Queries quality metrics and quarantine data from log files."""

    def __init__(self):
        self._root = get_project_root()

    def get_latest_metrics(self, dataset_name: Optional[str] = None) -> List[dict]:
        """
        Get latest quality metrics from log files.

        Args:
            dataset_name: Optional filter by dataset.

        Returns:
            List of quality metric dicts.
        """
        log_dir = self._root / "logs" / "validation"
        if not log_dir.is_dir():
            return []

        metrics = []
        for filepath in sorted(log_dir.glob("*_quality.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if dataset_name and data.get("dataset_name") != dataset_name:
                continue
            metrics.append(data)

        return metrics[:50]  # Return most recent 50

    def get_quality_history(self, dataset_name: str, limit: int = 30) -> List[dict]:
        """Get quality metrics trend for a dataset."""
        all_metrics = self.get_latest_metrics(dataset_name)
        return all_metrics[:limit]

    def get_quarantine_entries(self) -> List[dict]:
        """List quarantined batch entries."""
        quarantine_dir = self._root / "data" / "quarantine" / "validation_errors"
        if not quarantine_dir.is_dir():
            return []

        entries = []
        for dataset_dir in quarantine_dir.iterdir():
            if not dataset_dir.is_dir():
                continue
            for meta_file in dataset_dir.glob("*.json"):
                with open(meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                entries.append({
                    "batch_id": data.get("batch_id", ""),
                    "dataset": data.get("dataset", dataset_dir.name),
                    "invalid_count": data.get("invalid_record_count", 0),
                    "error_count": len(data.get("errors", [])),
                })

        return entries

    def get_quarantine_detail(self, batch_id: str) -> Optional[dict]:
        """Get quarantine details for a specific batch."""
        quarantine_dir = self._root / "data" / "quarantine" / "validation_errors"
        if not quarantine_dir.is_dir():
            return None

        for dataset_dir in quarantine_dir.iterdir():
            if not dataset_dir.is_dir():
                continue
            meta_file = dataset_dir / f"{batch_id}.json"
            if meta_file.is_file():
                with open(meta_file, "r", encoding="utf-8") as f:
                    return json.load(f)

        return None
