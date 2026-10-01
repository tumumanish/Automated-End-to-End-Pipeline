# Production Deployment Guide

## Automated End-to-End Data Pipeline & BI Architecture

> **Version:** 1.0 | **Last Updated:** October 2026

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Infrastructure Setup](#2-infrastructure-setup)
3. [Application Deployment](#3-application-deployment)
4. [Database Initialization](#4-database-initialization)
5. [Pipeline Configuration](#5-pipeline-configuration)
6. [API Server Deployment](#6-api-server-deployment)
7. [Scheduling & Orchestration](#7-scheduling--orchestration)
8. [BI Dashboard Connection](#8-bi-dashboard-connection)
9. [Monitoring & Alerting](#9-monitoring--alerting)
10. [Security Hardening](#10-security-hardening)
11. [Backup & Recovery](#11-backup--recovery)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

### Software Requirements

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.10+ | Core runtime |
| PostgreSQL | 16+ | Data warehouse & metadata |
| Docker | 24+ | Container runtime |
| Docker Compose | v2+ | Service orchestration |
| Git | Latest | Version control |

### Hardware Recommendations

| Environment | CPU | RAM | Storage |
|-------------|-----|-----|---------|
| Development | 2 cores | 4 GB | 20 GB |
| Staging | 4 cores | 8 GB | 50 GB |
| Production | 8+ cores | 16+ GB | 100+ GB SSD |

---

## 2. Infrastructure Setup

### Docker Compose (Recommended)

```powershell
# Clone the repository
git clone <repo-url>
cd Automated-End-to-End-Pipeline

# Start infrastructure services
docker-compose up -d

# Verify containers are running
docker ps
```

### Manual PostgreSQL Setup

If not using Docker:

```powershell
# Install PostgreSQL 16
# Create database and user
psql -U postgres -c "CREATE USER pipeline_user WITH PASSWORD 'pipeline_password';"
psql -U postgres -c "CREATE DATABASE pipeline_warehouse OWNER pipeline_user;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE pipeline_warehouse TO pipeline_user;"
```

---

## 3. Application Deployment

### Environment Setup

```powershell
# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with production values:
#   POSTGRES_HOST=<production-host>
#   POSTGRES_PASSWORD=<strong-password>
#   ENVIRONMENT=production
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_PORT` | Database port | `5432` |
| `POSTGRES_DB` | Database name | `pipeline_warehouse` |
| `POSTGRES_USER` | Database user | `pipeline_user` |
| `POSTGRES_PASSWORD` | Database password | `pipeline_password` |
| `ENVIRONMENT` | Runtime environment | `development` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

---

## 4. Database Initialization

```powershell
# Run all schema creation scripts in order
python scripts/setup_database.py
```

This executes the following SQL scripts:

1. `01_create_schemas.sql` — Creates `raw`, `staging`, `warehouse`, `analytics`, `metadata`, `monitoring` schemas
2. `02_create_raw_tables.sql` — Raw ingestion tables
3. `03_create_validation_tables.sql` — Validation audit tables
4. `03_create_staging_tables.sql` — Staging tables
5. `04_create_dimensions.sql` — Star schema dimension tables
6. `05_create_facts.sql` — Fact tables with foreign keys
7. `06_create_views.sql` — Analytical views for BI
8. `07_create_monitoring_tables.sql` — Quality metrics and pipeline metrics
9. `08_create_lineage_tables.sql` — Lineage events and data versions

---

## 5. Pipeline Configuration

### Pipeline Architectures

| Pipeline | Config Key | Pattern |
|----------|-----------|---------|
| ETLT++ | `etlt_plus_plus` | Extract → Validate → Raw → Transform → Curated |
| ELTL++ | `eltl_plus_plus` | Extract → Raw (immutable) → Validate → Transform → Curated |
| Basic ETLT | `etlt` | Extract → Validate → Raw → Transform → Curated (no monitoring) |
| Basic ELTL | `eltl` | Extract → Raw → Validate → Transform → Curated (no monitoring) |

### Running a Pipeline

```powershell
# CLI execution
python scripts/run_pipeline.py \
  --pipeline etlt_plus_plus \
  --source csv \
  --file data/input/transactions.csv \
  --dataset transactions \
  --contract-version 1.0

# Via orchestration
python orchestration/jobs/manual_pipeline.py \
  --pipeline etlt_plus_plus \
  --source csv \
  --file data/input/transactions.csv \
  --load-warehouse
```

---

## 6. API Server Deployment

### Development

```powershell
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```powershell
# Install production ASGI server
pip install gunicorn uvicorn[standard]

# Run with multiple workers
gunicorn api.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/api_access.log \
  --error-logfile logs/api_error.log
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/pipelines` | GET | List registered pipelines |
| `/api/v1/pipelines/{name}/run` | POST | Execute a pipeline |
| `/api/v1/pipelines/executions/recent` | GET | Recent executions |
| `/api/v1/quality/metrics` | GET | Quality metrics |
| `/api/v1/quality/quarantine` | GET | Quarantined batches |
| `/api/v1/lineage/batches` | GET | Lineage batch list |
| `/api/v1/lineage/batch/{id}` | GET | Batch lineage graph |
| `/docs` | GET | Swagger UI documentation |

---

## 7. Scheduling & Orchestration

### Windows Task Scheduler

```powershell
# Create a daily task at 2:00 AM
schtasks /create /tn "DailyPipeline" /tr "python orchestration/schedules/daily_pipeline.py" /sc daily /st 02:00
```

### Cron (Linux/WSL)

```bash
# crontab -e
0 2 * * * cd /path/to/project && .venv/bin/python orchestration/schedules/daily_pipeline.py
0 4 * * * cd /path/to/project && .venv/bin/python scripts/load_warehouse.py
```

### GitHub Actions (CI/CD)

The project includes `.github/workflows/ci.yml` for automated testing on push/PR.

---

## 8. BI Dashboard Connection

### Power BI

1. Open Power BI Desktop → **Get Data** → **PostgreSQL Database**
2. Server: `<host>:5432` | Database: `pipeline_warehouse`
3. Navigate to `analytics` schema → select views
4. Build dashboards from: `v_daily_sales`, `v_product_performance`, `v_regional_analysis`

### Tableau

1. Open Tableau → **Connect** → **PostgreSQL**
2. Server: `<host>` | Port: `5432` | Database: `pipeline_warehouse`
3. Schema: `analytics`
4. Create visualizations from analytical views

---

## 9. Monitoring & Alerting

### Quality Metrics

The pipeline automatically calculates and logs:

- **Freshness**: Time since last ingestion (target: < 24 hours)
- **Completeness**: Non-null field percentage (target: > 95%)
- **Accuracy**: Records passing all contract rules (target: > 98%)
- **Contract Adherence**: Batches fully passing validation (target: > 99%)

### Log Locations

| Log Type | Location |
|----------|----------|
| Pipeline execution | `logs/pipeline/` |
| Validation results | `logs/validation/` |
| Lineage events | `logs/lineage/` |
| Error & alerts | `logs/errors/` |

### Alert Thresholds

Configured in `config/settings.yaml` under `quality.*` keys. Alerts are logged to `logs/errors/alerts.jsonl` and accessible via the API at `GET /api/v1/quality/alerts`.

---

## 10. Security Hardening

### Production Checklist

- [ ] Change all default passwords in `.env`
- [ ] Enable SSL/TLS for PostgreSQL connections
- [ ] Add API authentication (API keys or JWT)
- [ ] Restrict network access to database ports
- [ ] Enable PostgreSQL connection pooling (PgBouncer)
- [ ] Add rate limiting to FastAPI endpoints
- [ ] Mask PII fields in logs and quarantine data
- [ ] Set `ENVIRONMENT=production` to disable debug modes
- [ ] Enable structured JSON logging for log aggregation
- [ ] Configure log rotation for long-running deployments

---

## 11. Backup & Recovery

### Database Backup

```powershell
# Full database backup
pg_dump -U pipeline_user -h localhost pipeline_warehouse > backup_$(date +%Y%m%d).sql

# Restore
psql -U pipeline_user -h localhost pipeline_warehouse < backup_20261001.sql
```

### Pipeline Recovery

Pipelines support **checkpoint-based recovery**:

```python
from src.storage.checkpoint_manager import CheckpointManager

mgr = CheckpointManager()
latest = mgr.get_latest("etlt_plus_plus")
# Resume from latest.last_completed_stage
```

---

## 12. Troubleshooting

| Issue | Solution |
|-------|----------|
| `Connection refused` to PostgreSQL | Check Docker container is running: `docker ps` |
| `ModuleNotFoundError` | Ensure virtual environment is activated and `pip install -r requirements.txt` ran |
| Pipeline returns `FAILED` | Check `logs/errors/` for stack traces and `logs/pipeline/` for execution details |
| Empty quality metrics | Ensure pipeline has run at least once; check `logs/validation/` |
| BI dashboard shows no data | Verify warehouse tables are populated: `SELECT COUNT(*) FROM warehouse.fact_transactions` |
| API returns 500 | Check `logs/api_error.log` and ensure database is accessible |
