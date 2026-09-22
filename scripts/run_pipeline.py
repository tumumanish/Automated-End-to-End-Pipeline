#!/usr/bin/env python
"""
Script: run_pipeline
Purpose:
    Execute a data pipeline from the command line using the PipelineRunner.

Usage:
    python scripts/run_pipeline.py --pipeline etlt_plus_plus --source csv --file tests/fixtures/sample_transactions.csv
"""

import argparse
import sys
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logging, get_logger
from src.pipelines.pipeline_runner import PipelineRunner

setup_logging()
logger = get_logger("cli")

def main() -> None:
    parser = argparse.ArgumentParser(description="Run data pipeline.")
    parser.add_argument("--pipeline", required=True,
                        choices=["etlt_plus_plus"],
                        help="The pipeline architecture to execute")
    parser.add_argument("--source", required=True,
                        choices=["csv", "excel", "api", "database"],
                        help="Source type")
    parser.add_argument("--file", help="File path (for csv/excel)")
    parser.add_argument("--url", help="API URL (for api source)")
    parser.add_argument("--dataset", default="transactions",
                        help="Dataset name (default: transactions)")
    parser.add_argument("--contract-version", default="1.0",
                        help="Version of the data contract to validate against")
    args = parser.parse_args()

    # --- Resolve source arguments ---
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

    print(f"\n{'=' * 50}")
    print(f" PIPELINE EXECUTION — Phase 4")
    print(f"{'=' * 50}")
    print(f" Architecture : {args.pipeline.upper()}")
    print(f" Source       : {args.source}")
    print(f" Dataset      : {args.dataset}")
    print(f" Contract     : v{args.contract_version}")
    print(f"{'=' * 50}\n")

    # Run the pipeline
    runner = PipelineRunner()
    result = runner.run(
        pipeline_name=args.pipeline,
        source=args.source,
        dataset=args.dataset,
        contract_version=args.contract_version,
        **kwargs
    )

    print(f"\n{'—' * 50}")
    print(f" EXECUTION COMPLETED")
    print(f"{'—' * 50}")
    print(json.dumps(result, indent=2))
    print(f"{'—' * 50}\n")

    if result["status"] == "FAILED":
        sys.exit(1)

if __name__ == "__main__":
    main()
