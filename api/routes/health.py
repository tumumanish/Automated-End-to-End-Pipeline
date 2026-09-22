"""
Route: /health
Purpose:
    Health check endpoint.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """Return application health status."""
    return {"status": "healthy", "service": "data-pipeline-api"}
