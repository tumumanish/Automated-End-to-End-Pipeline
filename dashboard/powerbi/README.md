# Power BI Dashboard

## Overview

Power BI consumes curated analytical data — never raw or staging tables. The
repository provides two connection paths:

| Path | When to use | Data source |
|------|-------------|-------------|
| **CSV extracts** (recommended) | Offline review, SQLite fallback, no PostgreSQL server | `dashboard/exports/*.csv` |
| **PostgreSQL direct** | Live warehouse available | `analytics` / `monitoring` schemas |

The CSV path is fully reproducible and is the one used for project demos.

---

## Path A — Load the CSV Extracts

### 1. Generate the files

```powershell
python scripts/export_bi_data.py
```

This writes one CSV per analytical view and monitoring table, plus
`kpi_summary.json` and `manifest.json`, into `dashboard/exports/`.

### 2. Import into Power BI Desktop

1. **Get Data → Text/CSV**.
2. Select a file (start with `analytics_v_daily_sales.csv`).
3. Click **Transform Data** and confirm the delimiter is comma and the first
   row is used as headers.
4. Repeat **Get Data → Text/CSV** for each file, or use **Get Data → Folder**
   on `dashboard/exports/` and **Combine Files** (exclude
   `kpi_summary.json` and `manifest.json` from the folder query).
5. In **Model view**, create relationships:
   - `analytics_v_product_performance[product_id]` → `analytics_v_transaction_detail[product_id]`
   - `analytics_v_customer_segments[customer_id]` → `analytics_v_transaction_detail[customer_id]`
   - `analytics_v_daily_sales[full_date]` → `analytics_v_transaction_detail[transaction_date]`
6. Set `analytics_v_daily_sales[full_date]` and
   `analytics_v_transaction_detail[transaction_date]` to **Date** type.
7. Mark `analytics_v_daily_sales` as a date table if you use time intelligence.

### 3. Measures (DAX)

Create a dedicated measure table and add:

```dax
Total Revenue = SUM('analytics_v_daily_sales'[total_sales])

Total Transactions = SUM('analytics_v_daily_sales'[transaction_count])

Total Units = SUM('analytics_v_daily_sales'[total_quantity])

Average Order Value =
DIVIDE([Total Revenue], [Total Transactions], 0)

Active Customers = DISTINCTCOUNT('analytics_v_customer_segments'[customer_id])

Quality Score =
AVERAGE('monitoring_batch_quality_metrics'[freshness_score])
+ AVERAGE('monitoring_batch_quality_metrics'[completeness_score])
+ AVERAGE('monitoring_batch_quality_metrics'[accuracy_score])
+ AVERAGE('monitoring_batch_quality_metrics'[contract_adherence_score])
```

For the four-part quality score above, divide the final result by 4 (or create
four separate gauges, one per dimension).

```dax
Pipeline Success Rate =
DIVIDE(
    CALCULATE(COUNTROWS('monitoring_pipeline_metrics'),
              'monitoring_pipeline_metrics'[status] = "SUCCESS"),
    COUNTROWS('monitoring_pipeline_metrics'),
    0
)
```

### 4. Report pages

| Page | Visuals | Fields |
|------|---------|--------|
| Executive Summary | KPI cards + line chart | Revenue, transactions, AOV, quality; `full_date` × `total_sales` |
| Product Analysis | Bar chart + table | `product_name` × `total_revenue`, `units_sold` |
| Regional Performance | Map or bar chart | `region` / `city` × `total_sales` |
| Customer Segments | Donut + table | `segment` × `total_spend`, `customer_name` |
| Data Quality | Gauges / cards | Four quality scores, batch count |
| Pipeline Monitoring | Table + status colors | `started_at`, `pipeline_name`, `status`, `duration_seconds` |

Save the workbook as `dashboard/powerbi/project_outcome.pbix` (local artifact;
it is not committed because binary workbooks cannot be reviewed in diffs).

### 5. Refresh

After a new pipeline + warehouse load + export:

1. Re-run `python scripts/export_bi_data.py`.
2. In Power BI Desktop, **Home → Refresh**.
3. For Power BI Service, publish the workbook and schedule a refresh that runs
   after the export job.

---

## Path B — Connect Directly to PostgreSQL

1. Install Power BI Desktop and, if prompted, the Npgsql PostgreSQL connector.
2. **Get Data → PostgreSQL database**.
3. Enter:
   - Server: `localhost:5432`
   - Database: `pipeline_warehouse`
   - Data Connectivity: DirectQuery (live) or Import (scheduled)
4. Select the `analytics` views and, for operational pages, the
   `monitoring.batch_quality_metrics` and `monitoring.pipeline_metrics` tables.
5. Apply the same relationships and measures as Path A.
6. Configure scheduled refresh in Power BI Service after publishing.

If PostgreSQL is unavailable, the project automatically falls back to SQLite;
use Path A in that case.

---

## Field Reference

See [`dataset_documentation.md`](dataset_documentation.md) for column-level
definitions of every exported dataset.

## Validation

- [ ] All nine CSVs load without type errors.
- [ ] `Total Revenue` matches `kpi_summary.json` (`revenue`).
- [ ] `Total Transactions` matches `kpi_summary.json` (`transactions`).
- [ ] Quality gauges match the four scores in `kpi_summary.json`.
- [ ] Pipeline status table shows only `SUCCESS` / `FAILED` / `RUNNING`.
- [ ] **Refresh** picks up a new export without breaking relationships.

## Limitations

- Binary `.pbix` files are not generated by the repository; steps above produce
  one locally if required for submission.
- CSV extracts are snapshots. Use the PostgreSQL path for live data.
- Currency is INR in the sample data; change display units in the visual
  formatting if a different currency is required.
