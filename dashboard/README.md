# Dashboard — Business Intelligence Layer

The BI layer provides interactive dashboards and visualizations consuming curated analytical datasets from the data warehouse semantic layer.

## Supported Tools

| Tool       | Directory   | Description                          |
|------------|-------------|--------------------------------------|
| Power BI   | `powerbi/`  | Interactive dashboards and reports   |
| Tableau    | `tableau/`  | Advanced analytics and visualizations|

## Important Principles

1. **Consume curated data only.** Dashboards should connect to analytical views and marts, never directly to raw or staging tables.
2. **Standardized KPIs.** All KPIs should be defined in the semantic layer and consumed consistently across tools.
3. **Refresh strategy.** Dashboards should follow scheduled refresh aligned with pipeline execution.

---

## Database Connection Details

| Setting | Value |
|---------|-------|
| **Host** | `localhost` (dev) / `<production-host>` (prod) |
| **Port** | `5432` |
| **Database** | `pipeline_warehouse` |
| **User** | `pipeline_user` |
| **Schema** | `analytics` (views), `warehouse` (tables), `monitoring` (metrics) |

## Analytical Views Available

These views are pre-built and ready for BI consumption:

| View | Schema | Description |
|------|--------|-------------|
| `v_daily_sales` | `analytics` | Daily aggregated sales with date dimension attributes |
| `v_product_performance` | `analytics` | Product-level revenue, units sold, and averages |
| `v_regional_analysis` | `analytics` | Regional sales, customer counts, and averages |
| `v_customer_segments` | `analytics` | Customer-level spend, frequency, and purchase timeline |
| `v_transaction_detail` | `analytics` | Fully denormalized transaction detail (all dimensions joined) |

## Monitoring Tables (for Data Quality Dashboards)

| Table | Schema | Description |
|-------|--------|-------------|
| `batch_quality_metrics` | `monitoring` | Per-batch quality scores (freshness, completeness, accuracy, adherence) |
| `pipeline_metrics` | `monitoring` | Pipeline execution history (duration, record counts, status) |
| `alert_log` | `monitoring` | Alert history with severity and threshold details |

---

## Power BI Setup

See [`powerbi/README.md`](powerbi/README.md) for detailed setup instructions.

**Quick Start:**
1. Install Power BI Desktop from the Microsoft Store
2. Install the Npgsql PostgreSQL connector if prompted
3. **Get Data** → **PostgreSQL Database** → Enter connection details above
4. Select views from the `analytics` schema
5. Build dashboard pages:
   - **Executive Summary** — KPI cards, trend lines from `v_daily_sales`
   - **Product Analysis** — Bar/treemap charts from `v_product_performance`
   - **Regional Performance** — Map/bar charts from `v_regional_analysis`
   - **Data Quality** — Gauge charts from `monitoring.batch_quality_metrics`
   - **Pipeline Monitoring** — Timeline/status from `monitoring.pipeline_metrics`

---

## Tableau Setup

See [`tableau/README.md`](tableau/README.md) for detailed setup instructions.

**Quick Start:**
1. Install Tableau Desktop or Tableau Public
2. **Connect** → **PostgreSQL** → Enter connection details above
3. Navigate to `analytics` schema
4. Build dashboard sheets:
   - **Sales Over Time** — Dual-axis chart from `v_daily_sales`
   - **Product Heatmap** — Heatmap from `v_product_performance`
   - **Geographic Distribution** — Filled map from `v_regional_analysis`
   - **Quality Scorecard** — Bullet charts from `monitoring.batch_quality_metrics`

---

## Refresh Schedule

| Dashboard | Refresh Frequency | Trigger |
|-----------|-------------------|---------|
| Sales dashboards | Daily at 5:00 AM | After warehouse load completes |
| Quality dashboards | After each pipeline run | Real-time from monitoring tables |
| Pipeline monitoring | After each pipeline run | Real-time from pipeline metrics |

> **Note:** Configure auto-refresh in Power BI Service or Tableau Server for production deployments.
