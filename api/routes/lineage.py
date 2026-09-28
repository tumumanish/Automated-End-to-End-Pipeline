"""
Route: /api/v1/lineage
Purpose:
    Data lineage endpoints — trace data flow by batch or dataset.
"""

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.services.lineage_service import LineageService

router = APIRouter()
_service = LineageService()


@router.get("/lineage/batches")
def list_lineage_batches():
    """List all batch IDs that have lineage data."""
    batches = _service.list_batches()
    return {"batches": batches, "count": len(batches)}


@router.get("/lineage/batch/{batch_id}")
def get_batch_lineage(batch_id: str):
    """
    Get the full lineage graph for a specific batch.

    Shows the complete data flow: Extract → Validate → Transform → Store
    with record counts at each stage.
    """
    lineage = _service.get_lineage_by_batch(batch_id)
    if lineage is None:
        raise HTTPException(status_code=404, detail=f"No lineage data for batch '{batch_id}'")
    return lineage


@router.get("/lineage/{dataset_name}")
def get_dataset_lineage(dataset_name: str):
    """
    Get all lineage events for a dataset across all batches.
    """
    events = _service.get_lineage_by_dataset(dataset_name)
    return {
        "dataset_name": dataset_name,
        "events": events,
        "count": len(events),
    }
