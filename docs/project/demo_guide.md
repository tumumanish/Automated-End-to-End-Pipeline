# Project Outcome Demo Guide

This guide defines a repeatable process for demonstrating the Automated
End-to-End Data Pipeline & BI Architecture and for evidencing the project's
outcome. It is written for a reviewer, examiner, or teammate who has never run
the repository before.

The demo deliberately ends with **open, inspectable artifacts** (CSV extracts
and a standalone HTML report) rather than opaque BI binaries. That makes the
outcome reproducible on any machine, including one where PostgreSQL is not
installed.

---

## 1. Outcomes This Demo Proves

| Outcome | Evidence produced by the demo |
|---------|-------------------------------|
| Raw data is ingested and validated against a contract | Pipeline execution record with extracted/valid/invalid counts |
| Bad records are isolated instead of corrupting the warehouse | Quarantine files + quality metrics |
| Curated data is versioned and traceable | Curated Parquet/CSV + lineage events |
| A dimensional warehouse is built | Staging, four dimensions, fact table row counts |
| Analytical views serve business questions | Five `analytics.v_*` views and their exports |
| Data quality is measured, not assumed | Freshness, completeness, accuracy, contract-adherence scores |
| Pipeline operations are observable | `monitoring.pipeline_metrics`, alerts, live API dashboard |
| Business outcome can be presented | KPI summary + `dashboard/reports/project_outcome.html` |
| BI tools can consume the result | Nine documented CSV extracts with field dictionary |

---

## 2. Audience and Time Budget

| Audience | Suggested flow | Time |
|----------|----------------|------|
| Reviewer / examiner | Full process + report walkthrough + Q&A | 15–20 min |
| Teammate / handover | Commands, artifacts, troubleshooting | 10 min |
| Quick check | One-command demo + report | 3–5 min |

---

## 3. Prerequisites

- Python 3.10+ with the project dependencies installed
  (`pip install -r requirements.txt`).
- Project root as the working directory.
- PowerShell on Windows (commands below); bash equivalents work on macOS/Linux.
- Optional: PostgreSQL via `docker-compose up -d`. If unavailable, the project
  automatically uses `data/warehouse/warehouse.db` (SQLite) and prints a warning.
- The sample fixture at `tests/fixtures/sample_transactions.csv`. If missing,
  `python scripts/showcase.py` generates one.

Verify the environment:

```powershell
python scripts/validate_environment.py
```

Expected: configuration and dependencies pass; a database warning is acceptable
when PostgreSQL is not running.

---

## 4. Fast Path — One Command

```powershell
python scripts/showcase.py
```

This command:

1. Verifies or generates the sample fixture.
2. Runs an ETLT++ pipeline execution.
3. Loads the warehouse **only if the fact table is empty** (avoids duplicate
   demo loads), then refreshes the analytical views.
4. Exports all BI datasets to `dashboard/exports/`.
5. Generates `dashboard/reports/project_outcome.html`.
6. Starts the FastAPI server and opens the control center.

Then open:

| URL | What it shows |
|-----|---------------|
| `http://localhost:8000/` | Live pipeline control center |
| `http://localhost:8000/reports/project-outcome` | Generated business outcome report |
| `http://localhost:8000/api/v1/bi/exports` | Export manifest (JSON) |
| `http://localhost:8000/docs` | Interactive API documentation |

Stop with `Ctrl+C`.

---

## 5. Step-by-Step Process (for a controlled demo)

Run these in order. Each step prints a verifiable result.

### Step 1 — Prepare the database

```powershell
python scripts/setup_database.py
```

Expected: schemas, tables, indexes, and views are created idempotently. On
SQLite the script attaches all schemas to one file; on PostgreSQL it creates
the real schemas. Re-running must not fail.

### Step 2 — Run the pipeline

```powershell
python scripts/run_pipeline.py --pipeline etlt_plus_plus --source csv `
  --file tests/fixtures/sample_transactions.csv --dataset transactions
```

Expected: JSON summary with `status: SUCCESS`, an `execution_id`, duration, and
record counts. The same execution appears in `monitoring.pipeline_metrics`.

Optional contrast: run the ELTL++ variant and compare when transformation
happens relative to loading:

```powershell
python scripts/run_pipeline.py --pipeline eltl_plus_plus --source csv `
  --file tests/fixtures/sample_transactions.csv --dataset transactions
```

### Step 3 — Load the warehouse

```powershell
python scripts/load_warehouse.py
```

Expected: curated records staged, dimensions upserted with SCD Type-2 history,
facts loaded with surrogate keys, and analytical views refreshed.

> The loader appends to the fact table. Run it once per fresh warehouse. Use
> `scripts/showcase.py` if you want an automatic "load only when empty" guard.

### Step 4 — Export the BI datasets

```powershell
python scripts/export_bi_data.py
```

Expected output (shape, not exact numbers):

```text
analytics.v_daily_sales                        203 rows  READY
analytics.v_product_performance                 12 rows  READY
analytics.v_regional_analysis                   15 rows  READY
analytics.v_customer_segments                  246 rows  READY
analytics.v_transaction_detail                 ...  rows  READY
monitoring.pipeline_metrics                     ...  rows  READY
monitoring.batch_quality_metrics                ...  rows  READY
monitoring.alert_log                            ...  rows  READY
metadata.lineage_events                         ...  rows  READY
```

Artifacts: `dashboard/exports/*.csv`, `kpi_summary.json`, `manifest.json`.

### Step 5 — Generate the outcome report

```powershell
python scripts/generate_project_report.py --open
```

Expected: `dashboard/reports/project_outcome.html` opens in the browser. It is a
single file with inline CSS/SVG and no network dependency.

### Step 6 — Serve the live interfaces

```powershell
uvicorn api.main:app --port 8000
```

Open `http://localhost:8000/` for operations and
`http://localhost:8000/reports/project-outcome` for the business outcome.

### Step 7 — Verify

```powershell
python -m pytest tests/ -q
```

Expected: the full suite passes (unit + integration, with environment-dependent
tests skipped when PostgreSQL/Snowflake are unavailable).

---

## 6. Five-Minute Walkthrough

Use this when time is short. Do **not** re-run the pipeline live if the
warehouse is already populated; show the generated report and exports instead.

1. **Frame the problem (30 s).** "Raw transaction files arrive with inconsistent
   types, duplicates, and missing values. We need trustworthy analytics, not
   just a script that copies files."
2. **Show the architecture (45 s).** Open `docs/architecture/system_architecture.md`
   or the README diagram: Raw → Contract → Validate/Clean → SCD2 Curated →
   Star Schema → Analytical Views → BI.
3. **Show one execution (45 s).** Open the control center at `/` and point to
   the KPI strip and recent executions. If live, run the ETLT++ button and show
   the new execution appear.
4. **Show the warehouse result (60 s).**
   `http://localhost:8000/api/v1/warehouse/summary` — staging, dimensions, fact,
   views. Emphasize surrogate keys and SCD2.
5. **Show the business outcome (2 min).** Open `/reports/project-outcome`.
   Walk through: executive summary → revenue trend → product/regional/customer
   analysis → quality scorecard → pipeline health → lineage → deliverables.
6. **Show the portability (45 s).** Open `dashboard/exports/manifest.json` and
   one CSV. Explain that Power BI/Tableau bind to these files, with field
   documentation in `dashboard/powerbi/` and `dashboard/tableau/`.
7. **Close (30 s).** "Every number in the report is reproducible from the
   warehouse; every claim has a command and an artifact behind it."

---

## 7. Fifteen-Minute Walkthrough

Use the full step-by-step process, then add:

- **Contract enforcement:** open `contracts/schemas/transactions_v1.0.yaml` and
  show required fields, types, and ranges. Point to
  `monitoring_batch_quality_metrics` for scores.
- **Quarantine:** show `data/quarantine/` after a deliberately broken row (or
  explain that invalid rows never reach facts).
- **Lineage:** open `/api/v1/lineage/batches` or
  `metadata_lineage_events.csv` and trace one batch through ingest → validate →
  curate → load.
- **SCD2:** query `warehouse.dim_customer` and show `is_current`,
  `valid_from`, `valid_to`.
- **Quality trend:** show the batch quality table and explain how each score is
  computed.
- **Operational health:** show pipeline success rate and alert severities.
- **BI hand-off:** open the Power BI or Tableau README and walk through binding
  the CSVs; explain why binary workbooks are not committed.
- **Engineering quality:** show the test suite result and the SQLite fallback
  design that keeps the demo reproducible.

---

## 8. What to Point At (Artifact Map)

| Claim | Artifact / endpoint |
|-------|---------------------|
| Pipeline ran | `/api/v1/pipelines/executions/recent`, `monitoring_pipeline_metrics.csv` |
| Data is valid | `monitoring_batch_quality_metrics.csv`, `data/quarantine/` |
| Warehouse is modeled | `/api/v1/warehouse/summary`, `docs/database/dimensional_model.md` |
| Business views exist | `/api/v1/warehouse/views`, `sql/postgres/06_create_views.sql` |
| BI data is portable | `dashboard/exports/*.csv`, `manifest.json` |
| Outcome is presentable | `dashboard/reports/project_outcome.html` |
| Lineage is recorded | `/api/v1/lineage/batches`, `metadata_lineage_events.csv` |
| Quality is enforced in code | `tests/`, `src/contracts/`, `src/monitoring/` |

---

## 9. Expected Results and Interpretation

### Business KPIs

| KPI | How it is computed | Where it appears |
|-----|--------------------|------------------|
| Total revenue | `SUM(total_sales)` from `v_daily_sales` | KPI card, executive summary |
| Transactions | `SUM(transaction_count)` | KPI card |
| Units sold | `SUM(total_quantity)` | KPI card |
| Average order value | Revenue ÷ transactions | KPI card |
| Active customers | Distinct `customer_id` in `v_customer_segments` | KPI card |
| Top product / region / category | Max revenue groupings | Executive summary, charts |
| Quality score | Mean of the four 0–100 scores | KPI card, quality panel |
| Pipeline success rate | Successful runs ÷ total runs | KPI card, execution table |

### Data quality

Scores are on a 0–100 scale. In the report:

- **≥ 95** — green
- **80–94.9** — amber
- **< 80** — red

If quality is empty, the report explicitly says so rather than inventing a
number.

### Pipeline health

The execution table shows the ten most recent runs. `SUCCESS` is green,
`FAILED` is red, anything else is amber. Average duration includes seeded demo
rows if present; use the latest rows for the current run.

### Known demo-data caveats

- The sample fixture is small; repeated `load_warehouse.py` runs append facts.
  For a clean story, load once into a fresh warehouse or use `showcase.py`,
  which skips the load when facts already exist.
- Seeded monitoring rows may have older timestamps than the current run. Sort by
  `started_at` when presenting.
- Monetary values are INR in the sample data.

---

## 10. Verification Checklist

- [ ] `python scripts/setup_database.py` exits 0.
- [ ] Pipeline result status is `SUCCESS`.
- [ ] `warehouse.fact_transactions` has rows and all four dimensions are populated.
- [ ] `analytics.v_daily_sales`, `v_product_performance`, `v_regional_analysis`,
      `v_customer_segments`, and `v_transaction_detail` all return rows.
- [ ] `dashboard/exports/manifest.json` lists nine datasets with `READY` status.
- [ ] `kpi_summary.json` parses and revenue/transactions match the report.
- [ ] `dashboard/reports/project_outcome.html` opens offline and shows charts.
- [ ] `/api/v1/bi/exports`, `/api/v1/bi/report`, and `/reports/project-outcome`
      return HTTP 200.
- [ ] `python -m pytest tests/ -q` passes.

---

## 11. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `PostgreSQL unreachable ... falling back to SQLite` | No database server running | Expected in offline demos. Start Docker Desktop + `docker-compose up -d` for PostgreSQL, or continue with SQLite |
| Pipeline says `NO_DATA` during warehouse load | No curated files for the dataset | Run the pipeline first; confirm files under `data/curated/transactions/` |
| Export manifest shows `unavailable` for a dataset | Table/view missing in the current warehouse | Run `python scripts/setup_database.py` and `python scripts/load_warehouse.py`, then re-export |
| Report has empty sections | Warehouse loaded but views empty, or export not run | Run `python scripts/export_bi_data.py` then regenerate the report |
| `Address already in use` on port 8000 | Another server is running | Stop it, or use `uvicorn api.main:app --port 8001` |
| Report link from the API 404s | Report not generated | Run `python scripts/generate_project_report.py` |
| Duplicate-looking revenue after repeated demos | Fact loader appends | Use a fresh warehouse or `showcase.py`; document the load count when presenting |
| Power BI cannot find files | Export not run or wrong folder | Re-run export; point Power BI at `dashboard/exports/` |
| Tests fail only on DB tests | PostgreSQL/Snowflake unavailable | Expected skips; run `python -m pytest tests/unit -q` for a deterministic subset |

---

## 12. Repeatability and Reset

The demo is designed to be repeatable:

- SQL setup is idempotent.
- `showcase.py` avoids reloading an already-populated warehouse.
- BI exports overwrite their files on each run.
- The report is regenerated from the current exports and contains the
  generation timestamp.
- Tests use isolated fixtures and skip live-database tests when unavailable.

To start from a clean local warehouse:

```powershell
# Stop the API first, then remove the generated SQLite warehouse.
Remove-Item data\warehouse\warehouse.db -ErrorAction SilentlyContinue
python scripts/setup_database.py
python scripts/run_pipeline.py --pipeline etlt_plus_plus --source csv `
  --file tests/fixtures/sample_transactions.csv --dataset transactions
python scripts/load_warehouse.py
python scripts/export_bi_data.py
python scripts/generate_project_report.py
```

> On PostgreSQL, reset the schemas with the project's SQL scripts or
> `docker-compose down -v` if a disposable volume is acceptable.

---

## 13. Submission Checklist

| Item | Path |
|------|------|
| Generated outcome report | `dashboard/reports/project_outcome.html` |
| KPI summary | `dashboard/exports/kpi_summary.json` |
| Export manifest | `dashboard/exports/manifest.json` |
| BI extracts | `dashboard/exports/*.csv` |
| BI setup guides | `dashboard/README.md`, `dashboard/powerbi/`, `dashboard/tableau/` |
| Architecture and schema docs | `docs/architecture/`, `docs/database/` |
| Implementation status | `docs/project/implementation.md` |
| Reproducible commands | This guide, `Makefile` targets, `scripts/showcase.py` |

---

## 14. Makefile Shortcuts

```powershell
make db-setup      # python scripts/setup_database.py
make run           # python scripts/run_pipeline.py
make warehouse     # python scripts/load_warehouse.py
make bi-export     # python scripts/export_bi_data.py
make report        # python scripts/generate_project_report.py
make outcome       # export + report
make demo          # python scripts/showcase.py
make test          # full test suite
```

On Windows without `make`, run the Python commands shown in each step directly.
