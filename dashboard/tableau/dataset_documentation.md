# Tableau — Dataset Documentation

This document describes the curated datasets exported by
`python scripts/export_bi_data.py` into `dashboard/exports/`. The same dataset
names and columns are used by the PostgreSQL analytical views when a live
database connection is available.

The full column-by-column dictionary lives in
[`../powerbi/dataset_documentation.md`](../powerbi/dataset_documentation.md);
both BI tools consume identical fields. This page adds Tableau-specific notes.

---

## Dataset Inventory

| Export file | Source object | Grain | Suggested Tableau sheet |
|-------------|---------------|-------|-------------------------|
| `analytics_v_daily_sales.csv` | `analytics.v_daily_sales` | One row per day | Sales Over Time |
| `analytics_v_product_performance.csv` | `analytics.v_product_performance` | One row per product | Product Performance |
| `analytics_v_regional_analysis.csv` | `analytics.v_regional_analysis` | One row per location | Regional Distribution |
| `analytics_v_customer_segments.csv` | `analytics.v_customer_segments` | One row per customer | Customer Segments |
| `analytics_v_transaction_detail.csv` | `analytics.v_transaction_detail` | One row per transaction line | Detail / drill-through |
| `monitoring_pipeline_metrics.csv` | `monitoring.pipeline_metrics` | One row per execution | Pipeline Health |
| `monitoring_batch_quality_metrics.csv` | `monitoring.batch_quality_metrics` | One row per batch | Quality Scorecard |
| `monitoring_alert_log.csv` | `monitoring.alert_log` | One row per alert | Alert Review |
| `metadata_lineage_events.csv` | `metadata.lineage_events` | One row per stage | Lineage Audit |

---

## Tableau Data Types

After connecting each text file, verify:

| Field pattern | Tableau type |
|---------------|--------------|
| `*_date`, `full_date`, `first_purchase`, `last_purchase` | Date |
| `*_at`, `metric_timestamp`, `event_timestamp` | Date & Time |
| `total_sales`, `total_revenue`, `total_spend`, `amount`, `unit_price`, `avg_*` | Number (Decimal) |
| `*_count`, `quantity`, `units_sold`, `total_quantity`, `*_key` | Number (Whole) |
| `is_weekend`, `acknowledged` | Boolean |
| Everything else | String |

`full_date` is currently exported as an ISO date string (`YYYY-MM-DD`). Tableau
usually infers the Date type; if not, right-click the field → **Change Data
Type → Date**.

---

## Relationships

In the Tableau data model:

| Left | Right | Relationship |
|------|-------|--------------|
| `analytics_v_daily_sales.full_date` | `analytics_v_transaction_detail.transaction_date` | Many-to-many logical relationship |
| `analytics_v_product_performance.product_id` | `analytics_v_transaction_detail.product_id` | Many-to-many logical relationship |
| `analytics_v_customer_segments.customer_id` | `analytics_v_transaction_detail.customer_id` | Many-to-many logical relationship |

The daily, product, and customer extracts are pre-aggregated. Use the
transaction-detail extract when a true row-level relationship is required.

---

## Calculated Fields

```tableau
// Total Revenue
SUM([Total Sales])

// Total Transactions
SUM([Transaction Count])

// Average Order Value
SUM([Total Sales]) / SUM([Transaction Count])

// Quality Score (0-100)
(
  AVG([Freshness Score]) +
  AVG([Completeness Score]) +
  AVG([Accuracy Score]) +
  AVG([Contract Adherence Score])
) / 4

// Pipeline Success Rate
SUM(IF [Status] = "SUCCESS" THEN 1 ELSE 0 END) / COUNT([Execution Id])

// Revenue per Customer
SUM([Total Spend]) / COUNTD([Customer Id])
```

---

## Dashboard Layout

| Zone | Sheet | Notes |
|------|-------|-------|
| Top strip | KPI text / BANs | Revenue, transactions, AOV, quality |
| Middle left | Sales Over Time | Continuous date axis |
| Middle right | Product Performance | Top 10 by revenue |
| Bottom left | Regional Distribution | Filled map if geocoding is enabled, otherwise bar |
| Bottom right | Quality Scorecard | Four bullet charts or a highlight table |
| Detail tab | Pipeline Health | Status-colored table with duration |

---

## Refresh

1. Re-run `python scripts/export_bi_data.py`.
2. In Tableau Desktop: **Data → Refresh All**.
3. For a published workbook: **Server → Publish Workbook**, then schedule an
   extract refresh after the export job.

---

## Conventions

- Monetary columns are INR in the sample dataset; set the default number format
  to currency.
- Score columns are on a 0–100 scale.
- Empty exports still include a header row, so the connection remains valid
  before data exists.
- Check `dashboard/exports/manifest.json` after each export to confirm row
  counts and the active backend.
