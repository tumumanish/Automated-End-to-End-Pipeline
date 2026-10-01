#!/usr/bin/env python
"""
Script: load_warehouse
Purpose:
    Post-pipeline script to load curated data into the warehouse
    star schema (dimensions + facts + views).

Usage:
    python scripts/load_warehouse.py
    python scripts/load_warehouse.py --dataset transactions --batch-id exec_abc123
"""

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# ---------------------------------------------------------------------------

from src.utils.logger import setup_logging, get_logger
from src.warehouse.staging.staging_loader import StagingLoader
from src.warehouse.views.view_manager import ViewManager

setup_logging()
logger = get_logger("warehouse")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load curated data into the data warehouse.")
    parser.add_argument(
        "--dataset", default="transactions",
        help="Dataset name (default: transactions)",
    )
    parser.add_argument(
        "--batch-id", default=None,
        help="Specific batch ID to load (default: all batches)",
    )
    parser.add_argument(
        "--refresh-views", action="store_true", default=True,
        help="Refresh analytical views after loading (default: True)",
    )
    args = parser.parse_args()

    print(f"\n{'=' * 60}")
    print(f" WAREHOUSE LOAD")
    print(f"{'=' * 60}")
    print(f" Dataset  : {args.dataset}")
    print(f" Batch    : {args.batch_id or 'ALL'}")
    print(f"{'=' * 60}\n")

    # Run the warehouse load pipeline
    loader = StagingLoader()
    result = loader.run(dataset=args.dataset, batch_id=args.batch_id)

    # Refresh analytical views
    if args.refresh_views:
        print("\nRefreshing analytical views...")
        view_mgr = ViewManager()
        view_mgr.refresh_views()
        views = view_mgr.list_views()
        print(f"  Active views: {views}")

    print(f"\n{'—' * 60}")
    print(f" WAREHOUSE LOAD COMPLETE")
    print(f"{'—' * 60}")
    print(f" Status        : {result.get('status', 'UNKNOWN')}")
    print(f" Records staged: {result.get('records_staged', 0)}")
    print(f" Facts loaded  : {result.get('facts', {}).get('loaded', 0)}")
    print(f"{'—' * 60}\n")

    if result.get("status") != "SUCCESS":
        sys.exit(1)


if __name__ == "__main__":
    main()
