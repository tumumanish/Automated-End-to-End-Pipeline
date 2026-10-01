#!/usr/bin/env python
"""
Module: manual_pipeline
Purpose:
    Enhanced manual pipeline trigger for on-demand execution.
    Supports pipeline selection, source selection, dry-run mode,
    and warehouse loading.

Usage:
    python orchestration/jobs/manual_pipeline.py --pipeline etlt_plus_plus --source csv --file tests/fixtures/sample_transactions.csv
    python orchestration/jobs/manual_pipeline.py --pipeline etlt_plus_plus --source csv --file tests/fixtures/sample_transactions.csv --load-warehouse
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logging, get_logger
from src.pipelines.pipeline_runner import PipelineRunner

setup_logging()
logger = get_logger("orchestration")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manual pipeline trigger.")
    parser.add_argument("--pipeline", required=True,
                        choices=["etlt_plus_plus", "eltl_plus_plus", "etlt", "eltl"],
                        help="Pipeline architecture to execute")
    parser.add_argument("--source", required=True,
                        choices=["csv", "excel", "api", "database"],
                        help="Source type")
    parser.add_argument("--file", help="File path (for csv/excel)")
    parser.add_argument("--url", help="API URL (for api source)")
    parser.add_argument("--dataset", default="transactions", help="Dataset name")
    parser.add_argument("--contract-version", default="1.0", help="Contract version")
    parser.add_argument("--load-warehouse", action="store_true",
                        help="Also load results into warehouse after pipeline")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print configuration without executing")
    args = parser.parse_args()

    # Build source kwargs
    kwargs = {}
    if args.source in ("csv", "excel"):
        if not args.file:
            print("ERROR: --file is required for csv/excel source.")
            sys.exit(1)
        kwargs["file_path"] = args.file
    elif args.source == "api":
        if not args.url:
            print("ERROR: --url is required for api source.")
            sys.exit(1)
        kwargs["url"] = args.url

    config = {
        "pipeline": args.pipeline,
        "source": args.source,
        "dataset": args.dataset,
        "contract_version": args.contract_version,
        "load_warehouse": args.load_warehouse,
        "kwargs": kwargs,
    }

    print(f"\n{'=' * 60}")
    print(f" MANUAL PIPELINE TRIGGER")
    print(f"{'=' * 60}")
    print(json.dumps(config, indent=2))
    print(f"{'=' * 60}\n")

    if args.dry_run:
        print("[DRY RUN] Would execute with the above configuration.")
        return

    # Execute pipeline
    runner = PipelineRunner()
    result = runner.run(
        pipeline_name=args.pipeline,
        source=args.source,
        dataset=args.dataset,
        contract_version=args.contract_version,
        **kwargs,
    )

    print(f"\n{'—' * 60}")
    print(json.dumps(result, indent=2))
    print(f"{'—' * 60}\n")

    # Optionally load warehouse
    if args.load_warehouse and result["status"] == "SUCCESS":
        print("Loading warehouse...")
        from src.warehouse.staging.staging_loader import StagingLoader
        wh_loader = StagingLoader()
        wh_result = wh_loader.run(
            dataset=args.dataset,
            batch_id=result["execution_id"],
        )
        print(f"Warehouse load: {wh_result.get('status')}")

    if result["status"] == "FAILED":
        sys.exit(1)


if __name__ == "__main__":
    main()
