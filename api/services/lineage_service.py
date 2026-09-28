"""
Service: lineage_service
Purpose:
    Business logic layer for lineage API operations.
"""

from typing import List, Optional

from src.lineage.lineage_store import LineageStore


class LineageService:
    """Queries lineage data from the lineage store."""

    def __init__(self):
        self._store = LineageStore()

    def get_lineage_by_batch(self, batch_id: str) -> Optional[dict]:
        """
        Get the lineage graph for a specific batch.

        Returns:
            Lineage summary dict or None.
        """
        events = self._store.load_events(batch_id)
        if not events:
            return None

        return {
            "batch_id": batch_id,
            "pipeline_name": events[0].pipeline_name,
            "dataset_name": events[0].dataset_name,
            "source_system": events[0].source_system,
            "stages": [
                {
                    "stage": e.stage,
                    "input_record_count": e.input_record_count,
                    "output_record_count": e.output_record_count,
                    "timestamp": e.timestamp,
                    "metadata": e.metadata,
                }
                for e in events
            ],
            "total_stages": len(events),
        }

    def get_lineage_by_dataset(self, dataset_name: str) -> List[dict]:
        """
        Get lineage events for a dataset across all batches.

        Returns:
            List of lineage event dicts.
        """
        events = self._store.query_by_dataset(dataset_name)
        return [e.to_dict() for e in events]

    def list_batches(self) -> List[str]:
        """List all batch IDs with lineage data."""
        return self._store.get_all_batches()
