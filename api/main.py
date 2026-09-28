"""
FastAPI application — Pipeline Monitoring & Sample Data API.

This API provides:
    - Health check endpoint
    - Sample transaction data endpoint (development use only)
    - Pipeline management endpoints (list, run, status)
    - Data quality monitoring endpoints
    - Data lineage query endpoints
"""

from fastapi import FastAPI

from api.routes import health, sample_data, pipelines, data_quality, lineage

app = FastAPI(
    title="Data Pipeline API",
    description="Pipeline monitoring and sample data for the Automated Data Pipeline & BI Architecture.",
    version="1.0.0",
)

# --- Register routes ---
app.include_router(health.router, tags=["Health"])
app.include_router(sample_data.router, prefix="/api/v1", tags=["Sample Data"])
app.include_router(pipelines.router, prefix="/api/v1", tags=["Pipelines"])
app.include_router(data_quality.router, prefix="/api/v1", tags=["Data Quality"])
app.include_router(lineage.router, prefix="/api/v1", tags=["Lineage"])
