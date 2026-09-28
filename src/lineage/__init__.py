"""
Package: lineage
Tracks data lineage — origin, transformations, and destination of datasets.

Modules:
    - lineage_tracker: Record lineage events at each pipeline stage
    - metadata_collector: Collect metadata about datasets and transformations
    - lineage_store: Persist and query lineage records
"""

from src.lineage.lineage_tracker import LineageTracker, LineageEvent
from src.lineage.lineage_store import LineageStore
from src.lineage.metadata_collector import MetadataCollector, DatasetMetadata, PipelineMetadata

__all__ = [
    "LineageTracker",
    "LineageEvent",
    "LineageStore",
    "MetadataCollector",
    "DatasetMetadata",
    "PipelineMetadata",
]
