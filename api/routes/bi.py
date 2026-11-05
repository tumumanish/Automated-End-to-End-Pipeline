"""
Route: /api/v1/bi
Purpose:
    Expose the generated BI deliverables: manifest/KPI metadata, downloadable
    CSV extracts, and the generated outcome report.

    The files are produced by ``scripts/export_bi_data.py`` and
    ``scripts/generate_project_report.py``. If they have not been generated
    yet, the endpoints return an empty/helpful response instead of failing.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.file_utils import get_project_root

router = APIRouter()

EXPORTS_DIR = get_project_root() / "dashboard" / "exports"
REPORTS_DIR = get_project_root() / "dashboard" / "reports"
REPORT_FILE = REPORTS_DIR / "project_outcome.html"

_ALLOWED_SUFFIXES = {".csv", ".json", ".html"}


def _safe_file(directory: Path, filename: str) -> Path:
    """Resolve a file inside ``directory`` and reject traversal attempts."""
    if not filename or Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if Path(filename).suffix.lower() not in _ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    path = (directory / filename).resolve()
    try:
        path.relative_to(directory.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")
    return path


def _read_manifest() -> dict:
    path = EXPORTS_DIR / "manifest.json"
    if not path.exists():
        return {"datasets": [], "files": [], "errors": [], "generated_at": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not read manifest: {exc}")


@router.get("/bi/exports")
def list_bi_exports():
    """Return the BI export manifest (datasets, row counts, files)."""
    manifest = _read_manifest()
    manifest["count"] = len(manifest.get("datasets", []))
    return manifest


@router.get("/bi/exports/{filename}")
def download_bi_export(filename: str):
    """Download a single generated CSV/JSON extract."""
    path = _safe_file(EXPORTS_DIR, filename)
    media_type = "application/json" if path.suffix.lower() == ".json" else "text/csv"
    return FileResponse(path, filename=path.name, media_type=media_type)


@router.get("/bi/report")
def get_bi_report_info():
    """Return metadata about the generated outcome report."""
    exists = REPORT_FILE.is_file()
    stat = REPORT_FILE.stat() if exists else None
    return {
        "available": exists,
        "path": str(REPORT_FILE),
        "url": "/reports/project-outcome",
        "size_bytes": stat.st_size if stat else 0,
        "generated_at": (
            datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            if stat
            else None
        ),
    }
