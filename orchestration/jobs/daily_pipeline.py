"""
Module: daily_pipeline
Purpose:
    Scheduled daily pipeline execution job with status reporting,
    monitoring integration, and error recovery.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import get_logger
from orchestration.schedules.daily_pipeline import run_daily_pipeline

logger = get_logger("orchestration.jobs.daily")


def execute_daily_job(load_warehouse: bool = False) -> dict:
    """
    Execute daily pipeline run with structured logging and reporting.

    Args:
        load_warehouse: Whether to stage and load facts into the warehouse.

    Returns:
        dict with status, execution_id, and timing.
    """
    logger.info("==========================================")
    logger.info("Executing Automated Daily Pipeline Job")
    logger.info("==========================================")
    try:
        result = run_daily_pipeline(load_warehouse=load_warehouse)
        logger.info(
            "Daily job completed with status: %s (Execution ID: %s, Duration: %.2fs)",
            result.get("status"),
            result.get("execution_id"),
            result.get("duration_seconds", 0.0),
        )
        return result
    except Exception as exc:
        logger.error("Daily pipeline job encountered an unhandled error: %s", exc, exc_info=True)
        return {
            "status": "FAILED",
            "error": str(exc),
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run daily pipeline job.")
    parser.add_argument("--load-warehouse", action="store_true", help="Load into warehouse")
    args = parser.parse_args()

    res = execute_daily_job(load_warehouse=args.load_warehouse)
    sys.exit(0 if res.get("status") == "SUCCESS" else 1)
