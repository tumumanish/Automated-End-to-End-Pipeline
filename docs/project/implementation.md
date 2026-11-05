# Implementation Guide

## Overview

This document tracks how the implementation maps to the PRD phases and what
remains. It is updated as work progresses; phase status in
`PRD_Implementation_Guide.md` reflects the original audit and may lag behind.

## Current Status (verified 2026-10-27)

| Phase | Area | Status | Key locations |
|-------|------|--------|---------------|
| 1 | Foundation & scaffolding | ✅ Complete | `config/`, `src/utils/`, `docker-compose.yml` |
| 2 | Ingestion (CSV/Excel/API/DB) | ✅ Complete | `src/ingestion/` |
| 3 | Data contracts & validation | ✅ Complete | `src/contracts/`, `contracts/schemas/` |
| 4 | ETLT++ pipeline & T2 | ✅ Complete | `src/pipelines/etlt_plus_plus.py`, `src/transformation/` |
| 5 | Versioning, lineage, checkpoints | ✅ Complete | `src/storage/versioning.py`, `src/lineage/`, `src/storage/checkpoint_manager.py` |
| 6 | Warehouse & dimensional model | ✅ Complete | `sql/postgres/04–06`, `src/warehouse/` |
| 7 | Monitoring & quality metrics | ✅ Complete | `src/monitoring/`, `sql/postgres/07` |
| 8 | REST API | ✅ Complete | `api/routes/`, `api/services/`, `api/schemas/` |
| 9 | BI layer | ✅ Complete (portable artifacts) | `src/bi/`, `scripts/export_bi_data.py`, `scripts/generate_project_report.py`, `dashboard/` |
| 10 | ELTL++ pipeline | ✅ Complete | `src/pipelines/eltl_plus_plus.py`, `src/pipelines/eltl_pipeline.py` |
| 11 | Testing & hardening | 🟡 In progress | 301 tests passing locally; see remaining checklist below |

## Running the System

```powershell
# Optional: start PostgreSQL (the pipeline falls back to SQLite otherwise)
docker-compose up -d

# Create schemas/tables (idempotent; works on Postgres or SQLite fallback)
python scripts/setup_database.py

# Run the ETLT++ pipeline
python scripts/run_pipeline.py --pipeline etlt_plus_plus --source csv `
  --file tests/fixtures/sample_transactions.csv --dataset transactions

# Load curated data into the star schema
python scripts/load_warehouse.py

# Build the BI deliverables (exports + standalone outcome report)
python scripts/export_bi_data.py
python scripts/generate_project_report.py --open

# Run the API / dashboard
uvicorn api.main:app --reload --port 8000

# Full test suite
python -m pytest tests/ -q
```

BI assets are served at `/reports/project-outcome`, `/api/v1/bi/exports`, and
`/exports/{filename}`. See `docs/project/demo_guide.md` for the end-to-end
outcome demonstration.

## Recent Implementation Notes

### SQL script execution

`src/storage/sql_utils.py` now provides comment-aware statement splitting.
Previously a naive `split(";")` skipped statements preceded by `--` comments,
so `setup_database.py` silently created only part of the schema. The same
helper adapts PostgreSQL DDL for the SQLite fallback, including rewriting
analytical views to use unqualified table names (SQLite cannot reference
tables in another attached database from a view).

### Retry with exponential backoff

`src/utils/retry.py` provides `call_with_retry()` and the `@retry` decorator.
`APIIngestion` retries timeouts and connection errors (default: 2 retries,
0.5 s initial backoff). Configure per adapter via `max_retries` and
`retry_backoff`.

### API security and lifecycle

`api/security.py` adds two opt-in protections:

- `PIPELINE_API_KEY` — require `X-API-Key` or `Authorization: Bearer` on
  `/api/*` (health, docs, and the dashboard stay public).
- `API_RATE_LIMIT_PER_MINUTE` — per-IP sliding-window rate limiting.

The FastAPI lifespan handler disposes the database engine on shutdown.

### Validation utilities

`src/utils/validation_utils.py` centralizes scalar null/type/range/format
checks. `ContractValidator` now delegates type and format checks to these
helpers, keeping contract validation and quality monitoring consistent.

### Query builders

`src/storage/postgres/queries.py` and `src/storage/snowflake/queries.py`
centralize SQL with identifier validation and bound parameters. The Postgres
batch/audit functions and warehouse loader consume these definitions.

### Snowflake support

`src/storage/snowflake/` now includes configuration, connection, query
builders, and a functional loader API (DataFrame load, stage creation,
`PUT`/`COPY INTO`). The connector is optional and imported lazily.

### BI deliverables

Phase 9 ships tool-agnostic artifacts rather than binary workbooks:

- `src/bi/exporter.py` exports the five analytical views, three monitoring
  tables, and lineage events to `dashboard/exports/*.csv`, plus
  `kpi_summary.json` and `manifest.json`.
- `src/bi/report.py` generates a standalone
  `dashboard/reports/project_outcome.html` with inline CSS/SVG charts (no CDN
  or external chart library).
- The API exposes the manifest, downloads, and report at
  `/api/v1/bi/*`, `/exports/*`, and `/reports/project-outcome`.
- `dashboard/powerbi/` and `dashboard/tableau/` document binding either the CSV
  extracts or the PostgreSQL views.
- `docs/project/demo_guide.md` defines the repeatable outcome-demo process.

This keeps the deliverable reproducible on SQLite and reviewable in source
control; `.pbix` / `.twbx` files can still be produced locally from the
documented field definitions.

## Remaining Work

From PRD section 14.4 (production hardening):

- [x] Retry logic with exponential backoff for adapters
- [x] Connection pooling for PostgreSQL (engine configured with pooling)
- [x] Request rate limiting for FastAPI
- [x] API-key authentication for FastAPI
- [x] Graceful shutdown handling (engine disposal)
- [ ] Health-check probes for Docker/Kubernetes
- [ ] Structured JSON logging for production
- [ ] Prometheus metrics export
- [ ] PII masking utilities
- [ ] Vectorized contract validation (replace `iterrows`)

Other open items:

- Optional: build local Power BI `.pbix` / Tableau `.twbx` workbooks from the
  CSV exports. Binary workbooks are intentionally not committed; the exports,
  field documentation, and connection guides are the reviewable deliverables.
- Add Snowflake integration tests when credentials are available.

## Guidelines

- Always use configuration from `config/` — never hard-code.
- Always use environment variables for credentials.
- Always log operations with context (batch_id, source, stage).
- Always write tests alongside implementation.
- Keep SQLite fallback working: `WAREHOUSE_BACKEND=sqlite` should be usable
  without PostgreSQL.
