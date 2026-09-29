"""
Module: manual_pipeline
Purpose:
    Manual pipeline trigger for on-demand execution with pipeline selection,
    source selection, and dry-run mode.

Usage:
    python orchestration/jobs/manual_pipeline.py --pipeline etlt_plus_plus --source csv --file <path>
    python orchestration/jobs/manual_pipeline.py --pipeline eltl_plus_plus --source csv --file <path> --dry-run
"""

import sys
import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logging, get_logger
from src.pipelines.pipeline_runner import PipelineRunner

setup_logging()
logger = get_logger("orchestration.manual")

SUPPORTED_PIPELINES = ["etlt_plus_plus", "eltl_plus_plus"]


def main():
    parser = argparse.ArgumentParser(description="Manual pipeline trigger.")
    parser.add_argument("--pipeline", required=True, choices=SUPPORTED_PIPELINES)
    parser.add_argument("--source",   required=True, choices=["csv", "excel", "api", "database"])
    parser.add_argument("--file",     default=None,  help="File path for csv/excel source")
    parser.add_argument("--url",      default=None,  help="API URL for api source")
    parser.add_argument("--dataset",  default="transactions")
    parser.add_argument("--contract-version", default="1.0")
    parser.add_argument("--dry-run",  action="store_true", help="Validate inputs without executing")
    args = parser.parse_args()

    print(f"\n{'=' * 55}")
    print(f"  MANUAL PIPELINE TRIGGER")
    print(f"{'=' * 55}")
    print(f"  Pipeline : {args.pipeline}")
    print(f"  Source   : {args.source}")
    print(f"  Dataset  : {args.dataset}")
    print(f"  Contract : v{args.contract_version}")
    print(f"  Dry Run  : {args.dry_run}")
    print(f"{'=' * 55}\n")

    if args.dry_run:
        print("DRY RUN — pipeline would execute with the above parameters.")
        print("No data will be processed.")
        return

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

    runner = PipelineRunner()
    result = runner.run(
        pipeline_name=args.pipeline,
        source=args.source,
        dataset=args.dataset,
        contract_version=args.contract_version,
        **kwargs
    )

    print(f"\n{'—' * 55}")
    print(f"  EXECUTION RESULT")
    print(f"{'—' * 55}")
    print(json.dumps(result, indent=2, default=str))
    print(f"{'—' * 55}\n")

    if result.get("status") not in ("SUCCESS",):
        sys.exit(1)


if __name__ == "__main__":
    main()
