# Power BI Dashboard

## Overview

Power BI dashboards consume curated analytical datasets from the warehouse semantic layer.

## Setup (To Be Configured in Phase 2)

1. Connect Power BI to the PostgreSQL `analytics` schema (or Snowflake analytics schema).
2. Use DirectQuery or Import mode depending on data volume.
3. Configure scheduled refresh to align with pipeline execution schedule.

## Recommended Datasets

| Dataset                         | Source View                      | Description                      |
|---------------------------------|----------------------------------|----------------------------------|
| Transaction Summary             | `analytics.vw_transaction_summary` | Aggregated transaction metrics |
| *(Additional datasets TBD)*     |                                  |                                  |

## KPI Definitions (To Be Defined)

| KPI                  | Formula                                     | Granularity     |
|----------------------|---------------------------------------------|-----------------|
| Total Revenue        | SUM(amount) WHERE status = 'completed'      | Daily / Monthly |
| Transaction Count    | COUNT(transaction_id)                       | Daily / Monthly |
| *(Additional KPIs TBD)* |                                           |                 |

## Fact / Dimension Relationships

| Fact Table             | Dimension Tables                                          |
|------------------------|-----------------------------------------------------------|
| fact_transactions      | dim_date, dim_customer, dim_product, dim_location         |

## Data Source Connection

- **Type:** PostgreSQL (local) or Snowflake (cloud)
- **Schema:** `analytics`
- **Authentication:** Database credentials (from .env)

## Refresh Strategy

- Align with pipeline schedule (e.g., daily at 3:00 AM after pipeline completes at 2:00 AM)
- Use incremental refresh where supported
