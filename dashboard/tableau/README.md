# Tableau Dashboard

## Overview

Tableau dashboards consume curated analytical datasets from the warehouse semantic layer.

## Setup (To Be Configured in Phase 2)

1. Connect Tableau to the PostgreSQL `analytics` schema (or Snowflake analytics schema).
2. Use Live or Extract mode depending on data volume.
3. Configure scheduled extract refresh to align with pipeline execution schedule.

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

## Data Source Connection

- **Type:** PostgreSQL (local) or Snowflake (cloud)
- **Schema:** `analytics`
- **Authentication:** Database credentials (from .env)

## Refresh Strategy

- Align with pipeline schedule
- Use Tableau Extract scheduled refresh
