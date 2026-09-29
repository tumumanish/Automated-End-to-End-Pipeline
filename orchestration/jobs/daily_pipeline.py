"""
Module: daily_pipeline
Purpose:
    Scheduled daily pipeline execution — runs ETLT++ pipeline on all
    available CSV sources then loads the warehouse.

Usage:
    python orchestration/jobs/daily_pipeline.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logging, get_logger
from src.pipelines.pipeline_runner import PipelineRunner
from src.warehouse.staging.staging_loader import StagingLoader
from src.warehouse.views.view_manager import ViewManager

setup_logging()
logger = get_logger("orchestration.daily")

RAW_CSV_DIR = PROJECT_ROOT / "data" / "raw" / "csv" / "transactions"
DATASET     = "transactions"
CONTRACT    = "1.0"
PIPELINE    = "etlt_plus_plus"


def main():
    started_at = datetime.now()
    print(f"\n{'=' * 55}")
    print(f"  DAILY PIPELINE JOB — {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 55}\n")

    runner  = PipelineRunner()
    results = []

    # Find unprocessed CSV files
    csv_files = sorted(RAW_CSV_DIR.glob("*.csv")) if RAW_CSV_DIR.exists() else []

    if not csv_files:
        logger.warning("No CSV files found for daily pipeline run.")
        print("No source files found. Exiting.")
        return

    for csv_file in csv_files:
        logger.info(f"Processing: {csv_file.name}")
        result = runner.run(
            pipeline_name=PIPELINE,
            source="csv",
            dataset=DATASET,
            contract_version=CONTRACT,
            file_path=str(csv_file),
        )
        results.append(result)
        status = result.get("status", "UNKNOWN")
        print(f"  [{status}] {csv_file.name} | exec={result.get('execution_id')} | {result.get('duration_seconds')}s")

    # Load warehouse after all pipeline runs
    print("\n  Loading warehouse...")
    try:
        loader = StagingLoader()
        wh_result = loader.load_latest_curated(DATASET)
        ViewManager().create_views()
        print(f"  Warehouse load: {wh_result}")
    except Exception as exc:
        logger.error(f"Warehouse load failed: {exc}")
        print(f"  Warehouse load FAILED: {exc}")

    duration = (datetime.now() - started_at).total_seconds()
    success_count = sum(1 for r in results if r.get("status") == "SUCCESS")

    print(f"\n{'—' * 55}")
    print(f"  Daily job complete | {success_count}/{len(results)} succeeded | {duration:.1f}s")
    print(f"{'—' * 55}\n")


if __name__ == "__main__":
    main()
