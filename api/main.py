"""
FastAPI application — Pipeline Monitoring & Sample Data API.

This API provides:
    - Health check endpoint
    - Sample transaction data endpoint (development use only)
    - Pipeline management endpoints (list, run, status)
    - Data quality monitoring endpoints
    - Data lineage query endpoints
    - Warehouse query endpoints
    - BI deliverables (exports manifest, downloads, outcome report)
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse

from api.routes import health, sample_data, pipelines, data_quality, lineage, warehouse, bi
from api.security import install_security_middleware


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Release database connections when the API shuts down."""
    yield
    from src.storage.postgres.connection import dispose_engine

    dispose_engine()


app = FastAPI(
    title="Data Pipeline API",
    description="Pipeline monitoring and sample data for the Automated Data Pipeline & BI Architecture.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Security (opt-in via PIPELINE_API_KEY / API_RATE_LIMIT_PER_MINUTE) ---
install_security_middleware(app)

# --- Register routes ---
app.include_router(health.router, tags=["Health"])
app.include_router(sample_data.router, prefix="/api/v1", tags=["Sample Data"])
app.include_router(pipelines.router, prefix="/api/v1", tags=["Pipelines"])
app.include_router(data_quality.router, prefix="/api/v1", tags=["Data Quality"])
app.include_router(lineage.router, prefix="/api/v1", tags=["Lineage"])
app.include_router(warehouse.router, prefix="/api/v1", tags=["Warehouse"])
app.include_router(bi.router, prefix="/api/v1", tags=["Business Intelligence"])

_DASHBOARD_FILE = Path(__file__).resolve().parent.parent / "dashboard" / "web" / "index.html"
_REPORT_FILE = Path(__file__).resolve().parent.parent / "dashboard" / "reports" / "project_outcome.html"


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
def get_dashboard():
    """Serve the interactive Showcase Control Center UI."""
    if _DASHBOARD_FILE.exists():
        return FileResponse(_DASHBOARD_FILE)
    return HTMLResponse("<h1>Data Pipeline API Online</h1><p>Visit <a href='/docs'>/docs</a> for API</p>")


@app.get("/reports/project-outcome", response_class=HTMLResponse, tags=["Business Intelligence"])
def get_project_outcome_report():
    """Serve the generated standalone project outcome report."""
    if _REPORT_FILE.exists():
        return FileResponse(_REPORT_FILE, media_type="text/html")
    return HTMLResponse(
        "<h1>Outcome report not generated yet</h1>"
        "<p>Run <code>python scripts/export_bi_data.py</code> and then "
        "<code>python scripts/generate_project_report.py</code>.</p>",
        status_code=404,
    )


@app.get("/exports/{filename}", tags=["Business Intelligence"])
def download_project_export(filename: str):
    """Download a generated BI export (CSV/JSON) referenced by the report."""
    from api.routes.bi import EXPORTS_DIR, _safe_file

    return FileResponse(_safe_file(EXPORTS_DIR, filename), filename=filename)

