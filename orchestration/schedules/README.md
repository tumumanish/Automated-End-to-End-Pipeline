# Orchestration Schedules

## Overview

This directory contains schedule definitions for automated pipeline execution. Schedules define **when** and **how** pipelines are triggered without manual intervention.

## Files

| File | Purpose |
|------|---------|
| `daily_pipeline.py` | Python-based daily scheduler using `schedule` or `APScheduler` |
| `pipeline_schedule.yaml` | YAML configuration defining cron-like schedule rules |

## Schedule Configuration (`pipeline_schedule.yaml`)

```yaml
schedules:
  daily_etlt:
    pipeline: etlt_plus_plus
    cron: "0 2 * * *"    # 2:00 AM daily
    source: csv
    dataset: transactions
    contract_version: "1.0"

  daily_warehouse:
    job: warehouse_load
    cron: "0 4 * * *"    # 4:00 AM daily (after pipeline)
```

## Usage

### Running the Daily Scheduler

```powershell
# Start the scheduler process (runs in foreground)
python orchestration/schedules/daily_pipeline.py

# Or use the manual trigger for one-off runs
python orchestration/jobs/manual_pipeline.py --pipeline etlt_plus_plus --source csv --file <path>
```

### Production Deployment Options

| Method | Tool | Notes |
|--------|------|-------|
| **Windows Task Scheduler** | `schtasks` | Native Windows; create a task pointing to `daily_pipeline.py` |
| **Cron (Linux/WSL)** | `crontab -e` | Add: `0 2 * * * cd /path/to/project && python orchestration/schedules/daily_pipeline.py --once` |
| **Docker Compose** | `docker-compose.yml` | Add a scheduler service with restart policy |
| **GitHub Actions** | `.github/workflows/` | Use `schedule` trigger with cron expression |
| **APScheduler** | Python library | Built into `daily_pipeline.py` for in-process scheduling |

## Adding a New Schedule

1. Add the schedule definition to `pipeline_schedule.yaml`
2. Implement the trigger logic in `daily_pipeline.py` (or create a new scheduler file)
3. Test with `--dry-run` flag before enabling in production
4. Monitor execution via the API: `GET /api/v1/pipelines/executions/recent`

## Monitoring

- Pipeline execution logs: `logs/pipeline/`
- Quality metrics logs: `logs/validation/`
- Alerts: `logs/errors/alerts.jsonl`
- API dashboard: `http://localhost:8000/docs`
