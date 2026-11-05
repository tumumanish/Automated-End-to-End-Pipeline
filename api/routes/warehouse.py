"""
Route: /api/v1/warehouse
Purpose:
    Warehouse query and staging management endpoints — summary counts,
    star schema inspection, and analytical view querying for BI presentation.
"""

from pathlib import Path
import sys
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.postgres.pg_loader import PostgresLoader
from src.warehouse.views.view_manager import ViewManager
from src.warehouse.staging.staging_loader import StagingLoader

router = APIRouter()
_loader = PostgresLoader()
_view_mgr = ViewManager(_loader)


@router.get("/warehouse/summary")
def get_warehouse_summary():
    """Return record counts across staging, dimensions, facts, and views."""
    tables = {
        "stg_transactions": "staging",
        "dim_date": "warehouse",
        "dim_customer": "warehouse",
        "dim_product": "warehouse",
        "dim_location": "warehouse",
        "fact_transactions": "warehouse",
    }
    counts = {}
    for tbl, schema in tables.items():
        try:
            counts[tbl] = _loader.table_row_count(tbl, schema)
        except Exception:
            counts[tbl] = 0

    views = _view_mgr.list_views()

    return {
        "backend": "sqlite" if _loader.is_sqlite else "postgresql",
        "table_counts": counts,
        "views": views,
        "total_facts": counts.get("fact_transactions", 0),
        "total_dimensions": sum(
            counts.get(k, 0)
            for k in ["dim_customer", "dim_product", "dim_date", "dim_location"]
        ),
    }


@router.get("/warehouse/views")
def list_warehouse_views():
    """List all available analytical views."""
    views = _view_mgr.list_views()
    return {"views": views, "count": len(views)}


@router.get("/warehouse/data/{dataset_name}")
def get_warehouse_data(dataset_name: str, limit: int = Query(default=25, ge=1, le=100)):
    """
    Fetch sample records from a dimension, fact, or analytical view.
    Examples: 'v_daily_sales', 'v_product_performance', 'v_customer_segments',
              'dim_customer', 'fact_transactions'
    """
    try:
        # Check if it's an analytical view
        if dataset_name.startswith("v_"):
            df = _view_mgr.query_view(dataset_name, limit=limit)
        elif dataset_name in ["dim_customer", "dim_product", "dim_location", "dim_date", "fact_transactions"]:
            df = _loader.query(f"SELECT * FROM warehouse.{dataset_name} LIMIT {limit}")
        elif dataset_name == "stg_transactions":
            df = _loader.query(f"SELECT * FROM staging.stg_transactions LIMIT {limit}")
        else:
            df = _loader.query(f"SELECT * FROM {dataset_name} LIMIT {limit}")

        if df.empty:
            return {"dataset": dataset_name, "count": 0, "columns": [], "records": []}

        # Convert timestamps and NaNs to serializable format
        records = df.fillna("").to_dict(orient="records")
        return {
            "dataset": dataset_name,
            "count": len(records),
            "columns": df.columns.tolist(),
            "records": records,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to query warehouse: {exc}")


@router.post("/warehouse/load")
def trigger_warehouse_load(dataset: str = "transactions", batch_id: Optional[str] = None):
    """
    Trigger the warehouse load pipeline to ingest curated data into star schema
    and refresh all analytical views.
    """
    try:
        staging_loader = StagingLoader(_loader)
        result = staging_loader.run(dataset=dataset, batch_id=batch_id)
        _view_mgr.refresh_views()
        return {"status": "SUCCESS", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Warehouse load failed: {exc}")
