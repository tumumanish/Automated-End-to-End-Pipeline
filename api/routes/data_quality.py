"""
Route: /api/v1/quality
Purpose:
    Data quality monitoring endpoints — metrics, trends, quarantine, alerts.
"""

import sys
from pathlib import Path

from fastapi import APIRouter, Query

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.services.quality_service import QualityService

router = APIRouter()
_service = QualityService()


@router.get("/quality/metrics")
def get_quality_metrics(dataset: str = None):
    """
    Get latest quality metrics.

    Args:
        dataset: Optional filter by dataset name.
    """
    metrics = _service.get_latest_metrics(dataset_name=dataset)
    return {"metrics": metrics, "count": len(metrics)}


@router.get("/quality/metrics/{dataset_name}")
def get_dataset_quality(dataset_name: str, limit: int = Query(default=30, ge=1, le=100)):
    """Get quality metric history for a specific dataset."""
    history = _service.get_quality_history(dataset_name, limit=limit)
    return {
        "dataset_name": dataset_name,
        "metrics": history,
        "count": len(history),
    }


@router.get("/quality/quarantine")
def get_quarantine_entries():
    """List all quarantined batches."""
    entries = _service.get_quarantine_entries()
    return {"entries": entries, "count": len(entries)}


@router.get("/quality/quarantine/{batch_id}")
def get_quarantine_detail(batch_id: str):
    """Get quarantine details for a specific batch."""
    from fastapi import HTTPException

    detail = _service.get_quarantine_detail(batch_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"No quarantine data for batch '{batch_id}'")
    return detail


@router.get("/quality/alerts")
def get_alerts(severity: str = None, limit: int = Query(default=20, ge=1, le=100)):
    """Get recent quality alerts."""
    from src.monitoring.alert_manager import AlertManager

    mgr = AlertManager()
    alerts = mgr.get_alerts(severity=severity)
    alerts = alerts[-limit:]
    return {
        "alerts": [a.to_dict() for a in alerts],
        "count": len(alerts),
    }
