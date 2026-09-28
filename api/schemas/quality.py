"""
API Schemas — Pydantic response models for data quality endpoints.
"""

from pydantic import BaseModel
from typing import Optional, List


class QualityMetricsResponse(BaseModel):
    """Quality metrics for a batch or dataset."""
    batch_id: str
    dataset_name: str
    source: str
    timestamp: str
    record_count: int
    valid_count: int
    invalid_count: int
    freshness_score: float
    completeness_score: float
    accuracy_score: float
    contract_adherence_score: float
    overall_score: float
    pipeline_status: str


class QualityHistoryResponse(BaseModel):
    """Quality trend over time."""
    dataset_name: str
    metrics: List[dict]
    count: int


class QuarantineEntry(BaseModel):
    """A quarantined batch entry."""
    batch_id: str
    dataset: str
    invalid_count: int
    error_count: int
    timestamp: Optional[str] = None


class QuarantineListResponse(BaseModel):
    """Response for GET /quality/quarantine."""
    entries: List[QuarantineEntry]
    count: int


class AlertResponse(BaseModel):
    """A single alert entry."""
    severity: str
    category: str
    message: str
    timestamp: str
    batch_id: str
    metric_name: str
    metric_value: float
    threshold_value: float
