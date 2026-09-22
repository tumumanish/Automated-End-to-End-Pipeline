"""
FastAPI application — Pipeline Monitoring & Sample Data API.

This API provides:
    - Health check endpoint
    - Sample transaction data endpoint (development use only)
    - Pipeline monitoring endpoints (to be implemented in later phases)
"""

from fastapi import FastAPI

from api.routes import health, sample_data

app = FastAPI(
    title="Data Pipeline API",
    description="Pipeline monitoring and sample data for the Automated Data Pipeline & BI Architecture.",
    version="0.1.0",
)

# --- Register routes ---
app.include_router(health.router, tags=["Health"])
app.include_router(sample_data.router, prefix="/api/v1", tags=["Sample Data"])
