#!/usr/bin/env python
"""
Script: load_warehouse
Purpose:
    Load the latest curated data into the dimensional warehouse.

Usage:
    python scripts/load_warehouse.py
    python scripts/load_warehouse.py --dataset transactions --batch exec_abc123
"""

import argparse
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logging, get_logger
from src.warehouse.staging.staging_loader import StagingLoader
from src.warehouse.views.view_manager import ViewManager

setup_logging()
logger = get_logger("cli.load_warehouse")


def main():
    parser = argparse.ArgumentParser(description="Load curated data into the warehouse.")
    parser.add_argument("--dataset", default="transactions", help="Dataset name (default: transactions)")
    parser.add_argument("--batch",   default=None,           help="Specific batch_id parquet file to load (optional)")
    args = parser.parse_args()

    print(f"\n{'=' * 50}")
    print(f" WAREHOUSE LOAD")
    print(f"{'=' * 50}")
    print(f" Dataset : {args.dataset}")
    print(f" Batch   : {args.batch or 'latest'}")
    print(f"{'=' * 50}\n")

    loader = StagingLoader()

    try:
        if args.batch:
            parquet_path = PROJECT_ROOT / "data" / "curated" / args.dataset / f"{args.batch}.parquet"
            if not parquet_path.exists():
                print(f"ERROR: Parquet file not found: {parquet_path}")
                sys.exit(1)
            results = loader.load_from_parquet(parquet_path, args.batch, args.dataset)
        else:
            results = loader.load_latest_curated(args.dataset)

        if not results:
            print("No curated data found to load.")
            sys.exit(0)

        # Refresh analytical views
        ViewManager().create_views()

        print(f"\n{'—' * 50}")
        print(f" WAREHOUSE LOAD COMPLETED")
        print(f"{'—' * 50}")
        print(json.dumps(results, indent=2))
        print(f"{'—' * 50}\n")

    except Exception as exc:
        logger.error(f"Warehouse load failed: {exc}", exc_info=True)
        print(f"\nERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
