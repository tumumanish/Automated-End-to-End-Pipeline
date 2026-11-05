# Power BI — Dataset Documentation

This document describes the curated datasets exported by
`python scripts/export_bi_data.py` into `dashboard/exports/`. The same dataset
names and columns are used by the PostgreSQL analytical views when a live
database connection is available.

---

## Dataset Inventory

| Export file | Source object | Grain | Suggested use |
|-------------|---------------|-------|---------------|
| `analytics_v_daily_sales.csv` | `analytics.v_daily_sales` | One row per calendar day | Executive trend, revenue, transactions, AOV |
| `analytics_v_product_performance.csv` | `analytics.v_product_performance` | One row per current product | Product ranking, category mix |
| `analytics_v_regional_analysis.csv` | `analytics.v_regional_analysis` | One row per location | Regional map, market comparison |
| `analytics_v_customer_segments.csv` | `analytics.v_customer_segments` | One row per current customer | Segmentation, top customers, recency |
| `analytics_v_transaction_detail.csv` | `analytics.v_transaction_detail` | One row per transaction line | Drill-through, detailed tables |
| `monitoring_pipeline_metrics.csv` | `monitoring.pipeline_metrics` | One row per execution | Pipeline health, success rate, duration |
| `monitoring_batch_quality_metrics.csv` | `monitoring.batch_quality_metrics` | One row per batch | Quality scorecard |
| `monitoring_alert_log.csv` | `monitoring.alert_log` | One row per alert | Alert severity analysis |
| `metadata_lineage_events.csv` | `metadata.lineage_events` | One row per stage event | Lineage and audit views |

`kpi_summary.json` is a pre-computed KPI document. `manifest.json` records the
backend, generation time, row counts, columns, and any datasets that could not
be exported.

---

## Relationships

| From | To | Cardinality |
|------|----|-------------|
| `analytics_v_daily_sales[full_date]` | `analytics_v_transaction_detail[transaction_date]` | 1:* |
| `analytics_v_product_performance[product_id]` | `analytics_v_transaction_detail[product_id]` | 1:* |
| `analytics_v_customer_segments[customer_id]` | `analytics_v_transaction_detail[customer_id]` | 1:* |

The regional and monitoring datasets are independent extracts and can be used
without relationships.

---

## Field Dictionary

### `analytics_v_daily_sales`

| Field | Type | Description |
|-------|------|-------------|
| `full_date` | Date | Calendar date |
| `day_name` | Text | Weekday name |
| `day_of_week` | Integer | 1 = Monday … 7 = Sunday |
| `month` | Integer | Calendar month number |
| `month_name` | Text | Month name |
| `quarter` | Integer | Calendar quarter |
| `year` | Integer | Calendar year |
| `is_weekend` | Boolean | Weekend flag |
| `total_sales` | Decimal | Sum of transaction amount |
| `total_quantity` | Integer | Sum of units |
| `transaction_count` | Integer | Number of transactions |
| `avg_transaction_value` | Decimal | Average transaction amount |

### `analytics_v_product_performance`

| Field | Type | Description |
|-------|------|-------------|
| `product_id` | Text | Business product identifier |
| `product_name` | Text | Product name |
| `category` | Text | Product category |
| `subcategory` | Text | Product subcategory |
| `total_revenue` | Decimal | Sum of transaction amount |
| `units_sold` | Integer | Sum of quantity |
| `transaction_count` | Integer | Number of transactions |
| `avg_transaction_value` | Decimal | Average transaction amount |
| `avg_unit_price` | Decimal | Average unit price |

### `analytics_v_regional_analysis`

| Field | Type | Description |
|-------|------|-------------|
| `location_name` | Text | Location key/name |
| `city` | Text | City |
| `state` | Text | State |
| `country` | Text | Country |
| `region` | Text | Sales region |
| `total_sales` | Decimal | Sum of transaction amount |
| `total_quantity` | Integer | Sum of units |
| `transaction_count` | Integer | Number of transactions |
| `unique_customers` | Integer | Distinct customers |
| `avg_transaction_value` | Decimal | Average transaction amount |

### `analytics_v_customer_segments`

| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | Text | Business customer identifier |
| `customer_name` | Text | Customer name |
| `segment` | Text | Customer segment |
| `customer_region` | Text | Customer region |
| `total_spend` | Decimal | Lifetime spend in the warehouse |
| `total_items` | Integer | Lifetime units |
| `transaction_count` | Integer | Number of transactions |
| `avg_transaction_value` | Decimal | Average transaction amount |
| `first_purchase` | Date | First purchase date |
| `last_purchase` | Date | Most recent purchase date |

### `analytics_v_transaction_detail`

| Field | Type | Description |
|-------|------|-------------|
| `transaction_date` | Date | Transaction date |
| `day_name` | Text | Weekday name |
| `month_name` | Text | Month name |
| `quarter` | Integer | Quarter |
| `year` | Integer | Year |
| `customer_id` | Text | Customer identifier |
| `customer_name` | Text | Customer name |
| `customer_segment` | Text | Customer segment |
| `product_id` | Text | Product identifier |
| `product_name` | Text | Product name |
| `product_category` | Text | Product category |
| `location_name` | Text | Location name |
| `city` | Text | City |
| `region` | Text | Region |
| `transaction_id` | Text | Transaction identifier |
| `quantity` | Integer | Units purchased |
| `unit_price` | Decimal | Price per unit |
| `amount` | Decimal | Line amount |
| `status` | Text | Transaction status |
| `batch_id` | Text | Source batch identifier |

### `monitoring_pipeline_metrics`

| Field | Type | Description |
|-------|------|-------------|
| `pipeline_name` | Text | Pipeline identifier |
| `execution_id` | Text | Execution identifier |
| `status` | Text | `SUCCESS`, `FAILED`, `RUNNING` |
| `started_at` | Timestamp | Start time |
| `completed_at` | Timestamp | Completion time |
| `duration_seconds` | Decimal | Runtime |
| `records_extracted` | Integer | Rows read |
| `records_valid` | Integer | Rows passing validation |
| `records_invalid` | Integer | Rows failing validation |
| `records_transformed` | Integer | Rows transformed |
| `error_message` | Text | Failure detail, if any |

### `monitoring_batch_quality_metrics`

| Field | Type | Description |
|-------|------|-------------|
| `batch_id` | Text | Batch identifier |
| `dataset_name` | Text | Dataset name |
| `source` | Text | Source type |
| `metric_timestamp` | Timestamp | Measurement time |
| `record_count` | Integer | Records in batch |
| `valid_count` | Integer | Valid records |
| `invalid_count` | Integer | Invalid records |
| `quarantined_count` | Integer | Quarantined records |
| `freshness_score` | Decimal | 0–100 |
| `completeness_score` | Decimal | 0–100 |
| `accuracy_score` | Decimal | 0–100 |
| `contract_adherence_score` | Decimal | 0–100 |
| `pipeline_status` | Text | Batch outcome |
| `processing_duration` | Decimal | Processing seconds |

### `monitoring_alert_log`

| Field | Type | Description |
|-------|------|-------------|
| `alert_timestamp` | Timestamp | Alert time |
| `severity` | Text | `INFO`, `WARNING`, `CRITICAL` |
| `category` | Text | Alert category |
| `message` | Text | Human-readable message |
| `batch_id` | Text | Related batch |
| `dataset_name` | Text | Related dataset |
| `metric_name` | Text | Metric that triggered the alert |
| `metric_value` | Decimal | Observed value |
| `threshold_value` | Decimal | Threshold |
| `acknowledged` | Boolean | Acknowledgement flag |

### `metadata_lineage_events`

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | Text | Event identifier |
| `batch_id` | Text | Batch identifier |
| `pipeline_name` | Text | Pipeline identifier |
| `stage` | Text | Pipeline stage |
| `source_system` | Text | Source system |
| `dataset_name` | Text | Dataset name |
| `contract_version` | Text | Contract version |
| `input_record_count` | Integer | Rows in |
| `output_record_count` | Integer | Rows out |
| `event_timestamp` | Timestamp | Event time |
| `metadata` | Text (JSON) | Stage-specific detail |

---

## Conventions

- Monetary columns are INR in the sample dataset and should use a currency
  format (`₹#,0`).
- Score columns are on a 0–100 scale.
- Empty exports still include a header row, so Power BI can bind a schema before
  data exists.
- `manifest.json` is the authoritative record of the export run; check it before
  refreshing a published report.
