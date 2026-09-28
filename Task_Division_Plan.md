# Task Division Plan — 2-Person Team

## Automated End-to-End Data Pipeline & BI Architecture

> **Goal:** Split all remaining work (Phases 5–11) between two developers so they can work **in parallel on different files** and merge cleanly.

---

## Division Principle

| Person | Role | Core Responsibility |
|--------|------|-------------------|
| **Person A** | Pipeline & Processing Engineer | Everything that processes, tracks, and monitors data flowing through the pipeline |
| **Person B** | Warehouse, BI & Infrastructure Engineer | Everything that stores analytical data, visualizes it, and hardens the system for production |

The split is designed so that **no two people modify the same file**. The only exceptions are 3 shared files with explicit merge protocols.

---

## File Ownership Matrix

### Person A — Pipeline & Processing

#### Phase 5: Data Versioning, Lineage & Checkpointing

| File | Action | Description |
|------|--------|-------------|
| [`src/storage/versioning.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/storage/versioning.py) | **Implement** | SCD Type 2 versioned record storage, record hashing, change detection |
| [`src/storage/checkpoint_manager.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/storage/checkpoint_manager.py) | **Implement** | Save/restore pipeline checkpoints, retention cleanup |
| [`src/lineage/lineage_tracker.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/lineage/lineage_tracker.py) | **Implement** | `LineageEvent` dataclass, stage-level lineage recording |
| [`src/lineage/lineage_store.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/lineage/lineage_store.py) | **Implement** | Persist lineage events to PostgreSQL `metadata.lineage_events` |
| [`src/lineage/metadata_collector.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/lineage/metadata_collector.py) | **Implement** | Collect schema + pipeline metadata per batch |
| [`src/lineage/__init__.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/lineage/__init__.py) | **Update** | Export new classes |
| `sql/postgres/08_create_lineage_tables.sql` | **Create** | `metadata.lineage_events`, `metadata.data_versions`, `metadata.checkpoints` |

#### Phase 7: Monitoring, Observability & Quality Metrics

| File | Action | Description |
|------|--------|-------------|
| [`src/monitoring/freshness.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/monitoring/freshness.py) | **Implement** | Freshness score calculation based on last ingestion timestamp |
| [`src/monitoring/completeness.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/monitoring/completeness.py) | **Implement** | Non-null percentage per field and aggregate |
| [`src/monitoring/accuracy.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/monitoring/accuracy.py) | **Implement** | % records passing all contract rules |
| [`src/monitoring/contract_adherence.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/monitoring/contract_adherence.py) | **Implement** | % batches passing contract validation |
| [`src/monitoring/quality_metrics.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/monitoring/quality_metrics.py) | **Implement** | `BatchQualityMetrics` aggregator dataclass |
| [`src/monitoring/pipeline_metrics.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/monitoring/pipeline_metrics.py) | **Implement** | Pipeline performance tracking (duration, success rate) |
| [`src/monitoring/alert_manager.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/monitoring/alert_manager.py) | **Implement** | Threshold breach detection, alert channels |
| [`src/monitoring/monitoring_logger.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/monitoring/monitoring_logger.py) | **Implement** | Persist metrics to PostgreSQL + JSON logs |
| [`src/monitoring/__init__.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/monitoring/__init__.py) | **Update** | Export new classes |
| `sql/postgres/07_create_monitoring_tables.sql` | **Create** | `monitoring.batch_quality_metrics`, `monitoring.pipeline_metrics` |

#### Phase 8 (Partial): API Routes — Pipelines, Quality, Lineage

| File | Action | Description |
|------|--------|-------------|
| [`api/routes/pipelines.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/api/routes/pipelines.py) | **Implement** | `GET /pipelines`, `GET /pipelines/{name}`, `POST /pipelines/{name}/run`, `GET /pipelines/executions` |
| [`api/routes/data_quality.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/api/routes/data_quality.py) | **Implement** | `GET /quality/metrics`, `GET /quality/metrics/{dataset}`, `GET /quality/quarantine` |
| [`api/routes/lineage.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/api/routes/lineage.py) | **Implement** | `GET /lineage/{dataset}`, `GET /lineage/batch/{batch_id}` |
| `api/schemas/pipeline.py` | **Create** | `PipelineResponse`, `ExecutionResponse` Pydantic models |
| `api/schemas/quality.py` | **Create** | `QualityMetricsResponse`, `QuarantineResponse` models |
| `api/schemas/lineage.py` | **Create** | `LineageResponse` model |
| `api/services/pipeline_service.py` | **Create** | Wraps `PipelineRunner` for API |
| `api/services/quality_service.py` | **Create** | Queries monitoring tables |
| `api/services/lineage_service.py` | **Create** | Queries lineage tables |

#### Phase 10: ELTL++ Pipeline

| File | Action | Description |
|------|--------|-------------|
| [`src/pipelines/eltl_plus_plus.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/pipelines/eltl_plus_plus.py) | **Implement** | Full ELTL++ pipeline: Extract → Raw Load → Managed Raw → Transform → Curated |
| [`src/pipelines/eltl_pipeline.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/pipelines/eltl_pipeline.py) | **Implement** | Basic ELTL pattern (simplified version) |
| [`src/pipelines/etlt_pipeline.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/pipelines/etlt_pipeline.py) | **Implement** | Basic ETLT pattern (simplified version) |
| [`src/pipelines/pipeline_registry.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/pipelines/pipeline_registry.py) | **Update** | Register `eltl_plus_plus`, `eltl`, `etlt` |

#### Integration Hooks (Person A adds to existing pipeline)

| File | Action | Description |
|------|--------|-------------|
| [`src/pipelines/etlt_plus_plus.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/pipelines/etlt_plus_plus.py) | **Modify** | Add lineage recording + monitoring hooks + checkpoint saves after each stage |
| [`src/pipelines/pipeline_runner.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/pipelines/pipeline_runner.py) | **Modify** | Add checkpoint restore logic on startup |
| [`src/transformation/enrichment.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/transformation/enrichment.py) | **Implement** | Data enrichment utilities |
| [`src/transformation/type_conversion.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/src/transformation/type_conversion.py) | **Implement** | Type casting utilities |

#### Person A — Tests

| File | Action |
|------|--------|
| `tests/unit/test_versioning.py` | **Create** |
| `tests/unit/test_lineage.py` | **Create** |
| `tests/unit/test_checkpoint.py` | **Create** |
| `tests/unit/test_monitoring.py` | **Create** |
| `tests/unit/test_alert_manager.py` | **Create** |
| `tests/integration/test_eltl_plus_plus.py` | **Create** |
| `tests/integration/test_monitoring_pipeline.py` | **Create** |
| `tests/integration/test_api_endpoints.py` | **Create** |

---

### Person B — Warehouse, BI & Infrastructure

#### Phase 6: Data Warehouse & Dimensional Modeling

| File | Action | Description |
|------|--------|-------------|
| [`sql/postgres/04_create_dimensions.sql`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/sql/postgres/04_create_dimensions.sql) | **Implement** | Uncomment + finalize `dim_date`, `dim_customer`, `dim_product`, `dim_location` |
| [`sql/postgres/05_create_facts.sql`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/sql/postgres/05_create_facts.sql) | **Implement** | Uncomment + finalize `fact_transactions` |
| [`sql/postgres/06_create_views.sql`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/sql/postgres/06_create_views.sql) | **Implement** | Create `v_daily_sales`, `v_product_performance`, `v_regional_analysis` |
| [`sql/postgres/03_create_staging_tables.sql`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/sql/postgres/03_create_staging_tables.sql) | **Implement** | Staging tables for dimension/fact loading |
| `src/warehouse/__init__.py` | **Update** | Export warehouse modules |
| `src/warehouse/dimensions/dim_date.py` | **Create** | Generate date dimension table from a date range |
| `src/warehouse/dimensions/dim_customer.py` | **Create** | SCD2 customer dimension loader |
| `src/warehouse/dimensions/dim_product.py` | **Create** | SCD2 product dimension loader |
| `src/warehouse/dimensions/dim_location.py` | **Create** | Location dimension loader |
| `src/warehouse/dimensions/__init__.py` | **Create** | Exports |
| `src/warehouse/facts/fact_transactions.py` | **Create** | Fact loader with surrogate key resolution |
| `src/warehouse/facts/__init__.py` | **Create** | Exports |
| `src/warehouse/staging/staging_loader.py` | **Create** | Load curated Parquet → staging → warehouse |
| `src/warehouse/staging/__init__.py` | **Create** | Exports |
| `src/warehouse/marts/sales_mart.py` | **Create** | Aggregated sales mart builder |
| `src/warehouse/marts/__init__.py` | **Create** | Exports |
| `src/warehouse/views/view_manager.py` | **Create** | Create/refresh analytical views |
| `src/warehouse/views/__init__.py` | **Create** | Exports |
| `src/storage/postgres/pg_loader.py` | **Create** | Generic PostgreSQL bulk loader (used by warehouse) |
| `src/storage/postgres/__init__.py` | **Create** | Exports |
| `src/storage/snowflake/sf_loader.py` | **Create** | Snowflake bulk loader (optional) |
| `src/storage/snowflake/__init__.py` | **Create** | Exports |
| `sql/snowflake/01–06_*.sql` | **Implement** | Snowflake equivalents of Postgres scripts |
| `scripts/load_warehouse.py` | **Create** | Script to run warehouse loading post-pipeline |

#### Phase 9: Business Intelligence Dashboards

| File | Action | Description |
|------|--------|-------------|
| `dashboard/powerbi/pipeline_dashboard.pbix` | **Create** | Power BI dashboard (5 pages: Executive, Product, Regional, Quality, Pipeline) |
| `dashboard/powerbi/README.md` | **Create** | Connection guide, DAX measures, screenshots |
| `dashboard/tableau/pipeline_dashboard.twbx` | **Create** | Tableau dashboard (4 sheets: Sales, Heatmap, Geo, Quality) |
| `dashboard/tableau/README.md` | **Create** | Setup guide, calculated fields, screenshots |
| [`dashboard/README.md`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/dashboard/README.md) | **Update** | Overview of both BI tools with connection details |

#### Phase 11: CI/CD, Orchestration & Production Hardening

| File | Action | Description |
|------|--------|-------------|
| `.github/workflows/ci.yml` | **Create** | GitHub Actions CI pipeline (lint, test, coverage) |
| `orchestration/jobs/manual_pipeline.py` | **Implement** | Enhanced manual pipeline trigger |
| `orchestration/jobs/warehouse_load_job.py` | **Create** | Scheduled warehouse refresh job |
| `orchestration/schedules/daily_pipeline.py` | **Create** | Daily pipeline scheduler |
| `orchestration/schedules/README.md` | **Create** | Schedule documentation |
| [`scripts/generate_sample_data.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/scripts/generate_sample_data.py) | **Enhance** | Add more diverse test data |
| `docs/database/dimensional_model.md` | **Update** | Document final star schema |
| `docs/pipeline/deployment_guide.md` | **Create** | Production deployment docs |
| `notebooks/04_warehouse_analysis.ipynb` | **Create** | Notebook for warehouse data exploration |

#### Person B — Tests

| File | Action |
|------|--------|
| `tests/unit/test_warehouse_loader.py` | **Create** |
| `tests/unit/test_dim_date.py` | **Create** |
| `tests/unit/test_staging.py` | **Create** |
| `tests/integration/test_warehouse_pipeline.py` | **Create** |
| `tests/integration/test_end_to_end_full.py` | **Create** |

---

## Shared Files — Merge Protocol

> [!CAUTION]
> Only **3 files** are touched by both people. Follow these merge rules strictly.

### 1. [`api/main.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/api/main.py)

**Who modifies:** Both (Person A adds route registrations, Person B may add middleware)

**Merge protocol:**
- Person A adds these lines at the end of the router registrations:
  ```python
  app.include_router(pipelines.router, prefix="/api/v1", tags=["Pipelines"])
  app.include_router(data_quality.router, prefix="/api/v1", tags=["Data Quality"])
  app.include_router(lineage.router, prefix="/api/v1", tags=["Lineage"])
  ```
- Person B adds **no new routers** (all BI work is external tools). Person B only adds middleware/startup events if needed for warehouse connectivity.
- **Merge order:** Person A merges first → Person B rebases.

### 2. [`scripts/setup_database.py`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/scripts/setup_database.py)

**Who modifies:** Both (both add their SQL files to `SQL_FILES` list)

**Merge protocol:**
- Person A adds:
  ```python
  "07_create_monitoring_tables.sql",
  "08_create_lineage_tables.sql",
  ```
- Person B adds:
  ```python
  "04_create_dimensions.sql",
  "05_create_facts.sql",
  "06_create_views.sql",
  ```
- **Merge order:** Person B merges first (04–06 come before 07–08 in execution order) → Person A rebases and appends.

### 3. [`config/pipeline.yaml`](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/config/pipeline.yaml)

**Who modifies:** Person A only (to enable `eltl_plus_plus`, `etlt`, `eltl` pipelines)

**Person B:** Do NOT modify this file.

---

## Integration Contract

> [!IMPORTANT]
> This defines the interfaces between Person A's and Person B's code so they integrate cleanly.

### Data Handoff Points

```
┌───────────────────────────────────────────────────────────────────┐
│                    PERSON A's TERRITORY                           │
│                                                                   │
│  Sources → Ingestion → Contracts → Transform → Curated Storage   │
│                                                                   │
│  Output: data/curated/<dataset>/<batch_id>.parquet                │
│  Format: Cleaned, validated, transformed pandas DataFrame         │
│  Columns: As defined by the data contract                         │
└───────────────────────────────┬───────────────────────────────────┘
                                │
                    Parquet files in data/curated/
                                │
┌───────────────────────────────▼───────────────────────────────────┐
│                    PERSON B's TERRITORY                           │
│                                                                   │
│  Curated Parquet → Staging → Dimensions → Facts → Views → BI     │
│                                                                   │
│  Input: data/curated/<dataset>/<batch_id>.parquet                 │
│  Reads via: pd.read_parquet() or pd.read_csv() (fallback)        │
└───────────────────────────────────────────────────────────────────┘
```

### Shared Interfaces (Do NOT change signatures)

| Interface | Owner | Consumer | Contract |
|-----------|-------|----------|----------|
| `save_curated_data()` return value | Person A (no changes needed) | Person B reads from `data/curated/` | Returns `Path` to Parquet/CSV file |
| `ValidationResult` class | Person A (no changes needed) | Person A's monitoring | Schema stays as-is; Person A may add fields |
| PostgreSQL schemas | Both | Both | `raw`, `staging`, `warehouse`, `analytics` = Person B. `metadata`, `monitoring` = Person A |
| `config/settings.yaml` quality thresholds | Unchanged | Person A reads | `quality.freshness_max_age_hours`, etc. |
| `PipelineRunner.run()` return dict | Person A | Person A's API | Schema: `{pipeline, execution_id, status, duration_seconds, details}` |

### Database Schema Ownership

| PostgreSQL Schema | Owner | Purpose |
|-------------------|-------|---------|
| `raw` | Shared (existing) | Raw ingested data |
| `staging` | **Person B** | Intermediate warehouse processing |
| `warehouse` | **Person B** | Dimension + Fact tables |
| `analytics` | **Person B** | Analytical views and marts |
| `metadata` | **Person A** | Lineage events, data versions, checkpoints |
| `monitoring` | **Person A** | Quality metrics, pipeline metrics |

---

## Workload Summary

### Person A — Total Files

| Category | Create | Modify | Total |
|----------|--------|--------|-------|
| `src/` Python modules | 13 | 5 | 18 |
| `sql/` scripts | 2 | 0 | 2 |
| `api/` routes + schemas + services | 9 | 0 | 9 |
| `tests/` | 8 | 0 | 8 |
| **Total** | **32** | **5** | **37** |

### Person B — Total Files

| Category | Create | Modify | Total |
|----------|--------|--------|-------|
| `src/` Python modules | 16 | 1 | 17 |
| `sql/` scripts (Postgres + Snowflake) | 6 | 3 | 9 |
| `dashboard/` BI files | 4 | 1 | 5 |
| `orchestration/` | 3 | 1 | 4 |
| `scripts/` + `docs/` + `notebooks/` | 4 | 1 | 5 |
| `tests/` | 5 | 0 | 5 |
| CI/CD | 1 | 0 | 1 |
| **Total** | **39** | **7** | **46** |

> [!NOTE]
> Person B has more files but many are simpler (SQL DDL, BI config, docs). The **coding complexity is roughly equal**: Person A handles complex logic (SCD2, monitoring algorithms, new pipeline architecture, full API layer) while Person B handles data modeling (dimensional design, warehouse ETL, BI dashboards).

---

## Timeline — 3-Week Plan

### Week 1: Core Backend

| Day | Person A | Person B |
|-----|----------|----------|
| **1–2** | Phase 5: `versioning.py` (SCD2 logic, record hashing) | Phase 6: Uncomment + finalize SQL (`04`, `05`, `06`) |
| **3–4** | Phase 5: `lineage_tracker.py`, `lineage_store.py`, `metadata_collector.py` | Phase 6: `dim_date.py`, `dim_customer.py`, `dim_product.py`, `dim_location.py` |
| **5** | Phase 5: `checkpoint_manager.py` + SQL tables | Phase 6: `fact_transactions.py`, `staging_loader.py` |

> **🔄 Week 1 Sync:** Both verify Person A's curated output feeds into Person B's warehouse loader. Run integration test together.

### Week 2: Monitoring, API & BI

| Day | Person A | Person B |
|-----|----------|----------|
| **1–2** | Phase 7: All 8 monitoring modules + SQL | Phase 6 (cont): `sales_mart.py`, `view_manager.py`, `pg_loader.py` |
| **3–4** | Phase 7: Integrate monitoring hooks into ETLT++ pipeline | Phase 9: Power BI Dashboard (connect, build 5 pages) |
| **5** | Phase 8: API routes (`pipelines.py`, `data_quality.py`, `lineage.py`) | Phase 9: Tableau Dashboard (connect, build 4 sheets) |

> **🔄 Week 2 Sync:** Person A demos API endpoints. Person B demos BI dashboards. Verify monitoring data appears in BI Quality page.

### Week 3: ELTL++, Testing & Merge

| Day | Person A | Person B |
|-----|----------|----------|
| **1–2** | Phase 10: Implement `eltl_plus_plus.py` + register in pipeline registry | Phase 11: CI/CD (`ci.yml`), orchestration jobs, docs |
| **3** | Write all unit + integration tests | Write all unit + integration tests |
| **4** | **MERGE DAY:** Both merge to `main`, resolve shared file conflicts | **MERGE DAY** |
| **5** | Full end-to-end integration test | BI dashboard final verification |

---

## Git Branching Strategy

```
main
 ├── feature/person-a-pipeline-processing
 │    ├── (all Person A files)
 │    └── Merges to main SECOND
 │
 └── feature/person-b-warehouse-bi
      ├── (all Person B files)
      └── Merges to main FIRST
```

### Merge Order (Critical!)

1. **Person B merges first** — warehouse SQL (04–06) must exist before monitoring SQL (07–08) since `setup_database.py` runs them in order.
2. **Person A rebases onto updated `main`**, resolves the 3 shared files, then merges.
3. Both run `pytest tests/ -v` on the merged `main` branch.

### Rules
- **Never force-push** to the other person's branch
- **Never modify files** outside your ownership list without notifying the other person
- **Tag shared file changes** in commit messages with `[SHARED]` prefix
- **Daily pull from `main`** to stay in sync with any hotfixes

---

## Quick Reference Card

### Person A Does ✅

- `src/storage/versioning.py`, `checkpoint_manager.py`
- `src/lineage/*` (all 3 files + `__init__`)
- `src/monitoring/*` (all 8 files + `__init__`)
- `src/pipelines/eltl_plus_plus.py`, `etlt_pipeline.py`, `eltl_pipeline.py`
- `src/pipelines/etlt_plus_plus.py` (add hooks), `pipeline_runner.py` (add checkpoint), `pipeline_registry.py` (register new pipelines)
- `src/transformation/enrichment.py`, `type_conversion.py`
- `api/routes/pipelines.py`, `data_quality.py`, `lineage.py`
- `api/schemas/pipeline.py`, `quality.py`, `lineage.py`
- `api/services/pipeline_service.py`, `quality_service.py`, `lineage_service.py`
- `sql/postgres/07_create_monitoring_tables.sql`, `08_create_lineage_tables.sql`
- 8 test files

### Person A Does NOT Touch ❌

- `src/warehouse/*`
- `src/storage/postgres/*`, `src/storage/snowflake/*`
- `sql/postgres/04*`, `05*`, `06*`
- `sql/snowflake/*`
- `dashboard/*`
- `orchestration/*`
- `.github/*`

---

### Person B Does ✅

- `src/warehouse/dimensions/*`, `facts/*`, `marts/*`, `staging/*`, `views/*`
- `src/storage/postgres/pg_loader.py`, `src/storage/snowflake/sf_loader.py`
- `sql/postgres/04_create_dimensions.sql`, `05_create_facts.sql`, `06_create_views.sql`, `03_create_staging_tables.sql`
- `sql/snowflake/*`
- `dashboard/powerbi/*`, `dashboard/tableau/*`, `dashboard/README.md`
- `orchestration/jobs/*`, `orchestration/schedules/*`
- `.github/workflows/ci.yml`
- `scripts/load_warehouse.py`, `scripts/generate_sample_data.py`
- `docs/database/*`, `docs/pipeline/deployment_guide.md`
- `notebooks/04_warehouse_analysis.ipynb`
- 5 test files

### Person B Does NOT Touch ❌

- `src/lineage/*`
- `src/monitoring/*`
- `src/pipelines/*` (all pipeline files)
- `src/contracts/*`
- `src/ingestion/*`
- `src/transformation/*`
- `api/routes/*`, `api/schemas/*`, `api/services/*`
