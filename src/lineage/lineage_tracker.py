"""
Module: lineage_tracker
Purpose:
    Record lineage events at each pipeline stage to answer:
    - Where did this dataset come from?
    - Which source produced it?
    - Which pipeline processed it?
    - Which transformations were applied?
    - Which version of the contract was used?
    - Which batch generated the dataset?
    - Which warehouse table contains the final data?
"""

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List

from src.utils.logger import get_logger
from src.utils.timestamps import utc_now

logger = get_logger("lineage")


@dataclass
class LineageEvent:
    """Represents a single lineage event at one pipeline stage."""
    event_id: str
    batch_id: str
    pipeline_name: str
    stage: str
    source_system: str = ""
    dataset_name: str = ""
    contract_version: str = ""
    input_record_count: int = 0
    output_record_count: int = 0
    timestamp: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class LineageTracker:
    """
    Records lineage events at each stage of a pipeline execution.

    Usage:
        tracker = LineageTracker(batch_id, pipeline_name, dataset_name, source)
        tracker.record("extract", input_count=0, output_count=100, metadata={...})
        tracker.record("validate", input_count=100, output_count=95)
        events = tracker.get_events()
    """

    def __init__(
        self,
        batch_id: str,
        pipeline_name: str,
        dataset_name: str,
        source_system: str = "",
        contract_version: str = "",
    ):
        self._batch_id = batch_id
        self._pipeline_name = pipeline_name
        self._dataset_name = dataset_name
        self._source_system = source_system
        self._contract_version = contract_version
        self._events: List[LineageEvent] = []

    @staticmethod
    def _generate_event_id() -> str:
        return f"evt_{uuid.uuid4().hex[:12]}"

    def record(
        self,
        stage: str,
        input_count: int = 0,
        output_count: int = 0,
        metadata: Optional[dict] = None,
    ) -> LineageEvent:
        """
        Record a lineage event for a pipeline stage.

        Args:
            stage: Stage name (e.g., 'extract', 'validate', 'transform', 'store').
            input_count: Number of records entering the stage.
            output_count: Number of records leaving the stage.
            metadata: Arbitrary metadata about the stage execution.

        Returns:
            The created LineageEvent.
        """
        event = LineageEvent(
            event_id=self._generate_event_id(),
            batch_id=self._batch_id,
            pipeline_name=self._pipeline_name,
            stage=stage,
            source_system=self._source_system,
            dataset_name=self._dataset_name,
            contract_version=self._contract_version,
            input_record_count=input_count,
            output_record_count=output_count,
            timestamp=utc_now().isoformat(),
            metadata=metadata or {},
        )
        self._events.append(event)

        logger.info(
            "Lineage event | batch=%s stage=%s in=%d out=%d",
            self._batch_id, stage, input_count, output_count,
        )
        return event

    def get_events(self) -> List[LineageEvent]:
        """Return all recorded lineage events in order."""
        return list(self._events)

    def get_lineage_summary(self) -> dict:
        """Return a summary of the full lineage chain."""
        return {
            "batch_id": self._batch_id,
            "pipeline_name": self._pipeline_name,
            "dataset_name": self._dataset_name,
            "source_system": self._source_system,
            "contract_version": self._contract_version,
            "stages": [
                {
                    "stage": e.stage,
                    "input": e.input_record_count,
                    "output": e.output_record_count,
                    "timestamp": e.timestamp,
                }
                for e in self._events
            ],
            "total_stages": len(self._events),
        }
