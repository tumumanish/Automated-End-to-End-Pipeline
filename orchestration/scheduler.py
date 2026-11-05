"""
Module: scheduler
Purpose:
    APScheduler-based background scheduler for automated recurring pipeline jobs.
    Reads cron definitions from pipeline_schedule.yaml and manages cron triggers.
"""

from __future__ import annotations

import sys
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from src.utils.logger import get_logger, setup_logging
from orchestration.jobs.daily_pipeline import execute_daily_job

setup_logging()
logger = get_logger("orchestration.scheduler")


def load_schedule_config() -> dict:
    """Load schedules from pipeline_schedule.yaml."""
    config_path = PROJECT_ROOT / "orchestration" / "schedules" / "pipeline_schedule.yaml"
    if not config_path.exists():
        logger.warning("Schedule config %s not found, using defaults", config_path)
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_scheduler() -> BlockingScheduler:
    """Configure and return an APScheduler BlockingScheduler."""
    scheduler = BlockingScheduler()
    config = load_schedule_config()
    schedules = config.get("schedules", {})

    daily_cfg = schedules.get("daily_full_pipeline", {})
    if daily_cfg.get("enabled", True):
        cron_expr = daily_cfg.get("cron", "0 2 * * *")
        # standard 5-part cron: minute hour day month day_of_week
        parts = cron_expr.split()
        if len(parts) == 5:
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
            )
        else:
            trigger = CronTrigger(hour=2, minute=0)

        scheduler.add_job(
            execute_daily_job,
            trigger=trigger,
            id="daily_full_pipeline",
            name="Daily ETLT++ Pipeline",
            replace_existing=True,
        )
        logger.info("Registered job 'daily_full_pipeline' with cron '%s'", cron_expr)

    return scheduler


def start_scheduler():
    """Start the blocking scheduler loop."""
    scheduler = build_scheduler()
    logger.info("Scheduler initialized. Starting job runner loop (Press Ctrl+C to stop)...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shutdown gracefully.")


if __name__ == "__main__":
    start_scheduler()
