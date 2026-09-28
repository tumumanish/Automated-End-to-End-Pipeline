"""
API Schemas — Pydantic response models for lineage endpoints.
"""

from pydantic import BaseModel
from typing import Optional, List


class LineageEventResponse(BaseModel):
    """A single lineage event."""
    event_id: str
    batch_id: str
    pipeline_name: str
    stage: str
    source_system: str
    dataset_name: str
    contract_version: str
    input_record_count: int
    output_record_count: int
    timestamp: str
    metadata: dict


class LineageGraphResponse(BaseModel):
    """Lineage graph for a dataset or batch."""
    batch_id: str
    pipeline_name: str
    dataset_name: str
    source_system: str
    stages: List[dict]
    total_stages: int


class LineageBatchListResponse(BaseModel):
    """List of batches with lineage data."""
    batches: List[str]
    count: int
