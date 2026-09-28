"""
API Schemas — Pydantic response models for pipeline endpoints.
"""

from pydantic import BaseModel
from typing import Optional, List


class PipelineInfo(BaseModel):
    """Basic pipeline information."""
    name: str
    class_name: str
    enabled: bool = True


class PipelineListResponse(BaseModel):
    """Response for GET /pipelines."""
    pipelines: List[PipelineInfo]
    count: int


class ExecutionRequest(BaseModel):
    """Request body for POST /pipelines/{name}/run."""
    source: str
    dataset: str = "transactions"
    contract_version: str = "1.0"
    file_path: Optional[str] = None
    url: Optional[str] = None


class ExecutionSummary(BaseModel):
    """Summary of a single pipeline execution."""
    pipeline: str
    execution_id: str
    status: str
    duration_seconds: float
    details: dict


class ExecutionListResponse(BaseModel):
    """Response for GET /pipelines/executions."""
    executions: List[dict]
    count: int
