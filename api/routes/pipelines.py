"""
Route: /api/v1/pipelines
Purpose:
    Pipeline management endpoints — list, get details, run, view executions.
"""

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.services.pipeline_service import PipelineService

router = APIRouter()
_service = PipelineService()


@router.get("/pipelines")
def list_pipelines():
    """List all registered pipelines."""
    pipelines = _service.list_pipelines()
    return {"pipelines": pipelines, "count": len(pipelines)}


@router.get("/pipelines/{name}")
def get_pipeline(name: str):
    """Get details for a specific pipeline."""
    pipeline = _service.get_pipeline(name)
    if pipeline is None:
        raise HTTPException(status_code=404, detail=f"Pipeline '{name}' not found")
    return pipeline


@router.post("/pipelines/{name}/run")
def run_pipeline(name: str, source: str, dataset: str = "transactions", contract_version: str = "1.0", file_path: str = None, url: str = None):
    """
    Execute a pipeline by name.

    Args:
        name: Pipeline name (etlt_plus_plus, eltl_plus_plus).
        source: Source type (csv, excel, api, database).
        dataset: Dataset name.
        contract_version: Contract version.
        file_path: File path (for csv/excel).
        url: URL (for api source).
    """
    pipeline = _service.get_pipeline(name)
    if pipeline is None:
        raise HTTPException(status_code=404, detail=f"Pipeline '{name}' not found")

    try:
        result = _service.run_pipeline(
            pipeline_name=name,
            source=source,
            dataset=dataset,
            contract_version=contract_version,
            file_path=file_path,
            url=url,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(exc)}")


@router.get("/pipelines/executions/recent")
def get_recent_executions(pipeline_name: str = None, limit: int = 20):
    """Get recent pipeline execution metrics."""
    from src.monitoring.pipeline_metrics import PipelineMetricsTracker

    tracker = PipelineMetricsTracker()
    executions = tracker.get_executions(pipeline_name=pipeline_name, limit=limit)
    return {
        "executions": [e.to_dict() for e in executions],
        "count": len(executions),
    }
