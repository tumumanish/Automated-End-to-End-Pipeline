#!/usr/bin/env python
"""
Module: warehouse_load_job
Purpose:
    Scheduled warehouse refresh job — reads curated data
    and loads it into the dimensional warehouse.

Usage:
    python orchestration/jobs/warehouse_load_job.py
    python orchestration/jobs/warehouse_load_job.py --dataset transactions
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logging, get_logger
from src.warehouse.staging.staging_loader import StagingLoader
from src.warehouse.views.view_manager import ViewManager

setup_logging()
logger = get_logger("orchestration.warehouse")


def main() -> None:
    parser = argparse.ArgumentParser(description="Warehouse load job.")
    parser.add_argument("--dataset", default="transactions", help="Dataset to load")
    parser.add_argument("--batch-id", default=None, help="Specific batch ID (default: all)")
    args = parser.parse_args()

    logger.info("Warehouse load job started | dataset=%s batch=%s", args.dataset, args.batch_id)

    loader = StagingLoader()
    result = loader.run(dataset=args.dataset, batch_id=args.batch_id)

    # Refresh views
    view_mgr = ViewManager()
    view_mgr.refresh_views()

    logger.info("Warehouse load job completed | status=%s", result.get("status"))
    print(f"Warehouse load: {result.get('status')} | Facts loaded: {result.get('facts', {}).get('loaded', 0)}")

    if result.get("status") != "SUCCESS":
        sys.exit(1)


if __name__ == "__main__":
    main()
