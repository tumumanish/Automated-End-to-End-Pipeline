#!/usr/bin/env python
"""
Module: daily_pipeline
Purpose:
    Scheduled daily pipeline execution — runs the ETLT++ pipeline
    on configured data sources and optionally loads the warehouse.

Usage:
    python orchestration/schedules/daily_pipeline.py
    python orchestration/schedules/daily_pipeline.py --load-warehouse
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logging, get_logger
from src.pipelines.pipeline_runner import PipelineRunner
from src.utils.config import get_settings

setup_logging()
logger = get_logger("orchestration.schedule")


def run_daily_pipeline(load_warehouse: bool = False) -> dict:
    """
    Execute the daily pipeline job.

    1. Runs the ETLT++ pipeline on the default dataset
    2. Optionally loads results into the warehouse

    Returns:
        Pipeline execution result dict.
    """
    logger.info("Daily pipeline job triggered")

    runner = PipelineRunner()
    result = runner.run(
        pipeline_name="etlt_plus_plus",
        source="csv",
        dataset="transactions",
        contract_version="1.0",
        file_path="tests/fixtures/sample_transactions.csv",
    )

    logger.info("Daily pipeline result: %s", result["status"])

    if load_warehouse and result["status"] == "SUCCESS":
        logger.info("Triggering warehouse load...")
        from src.warehouse.staging.staging_loader import StagingLoader
        wh_loader = StagingLoader()
        wh_result = wh_loader.run(
            dataset="transactions",
            batch_id=result["execution_id"],
        )
        logger.info("Warehouse load: %s", wh_result.get("status"))

    return result


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Daily pipeline scheduler.")
    parser.add_argument("--load-warehouse", action="store_true",
                        help="Load warehouse after pipeline")
    args = parser.parse_args()

    result = run_daily_pipeline(load_warehouse=args.load_warehouse)
    print(f"Pipeline: {result['status']} | Duration: {result['duration_seconds']}s")

    if result["status"] == "FAILED":
        sys.exit(1)


if __name__ == "__main__":
    main()
