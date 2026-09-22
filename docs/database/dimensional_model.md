# Dimensional Model

## Overview

The data warehouse uses dimensional modeling with a star schema design for analytical query performance and BI consumption.

## Star Schema

```
                    ┌──────────────┐
                    │  dim_date    │
                    └──────┬───────┘
                           │
┌──────────────┐   ┌───────┴────────┐   ┌──────────────┐
│ dim_customer │───│fact_transactions│───│ dim_product   │
└──────────────┘   └───────┬────────┘   └──────────────┘
                           │
                    ┌──────┴───────┐
                    │ dim_location │
                    └──────────────┘
```

## Dimension Tables

### dim_date
- **Grain:** One row per calendar date
- **Key:** `date_key`
- **Attributes:** full_date, day_of_week, day_name, month, quarter, year, is_weekend, is_holiday

### dim_customer
- **Grain:** One row per customer (SCD Type 2)
- **Key:** `customer_key`
- **Attributes:** customer_id, customer_name, segment, region
- **SCD:** valid_from, valid_to, is_current

### dim_product
- **Grain:** One row per product (SCD Type 2)
- **Key:** `product_key`
- **Attributes:** product_id, product_name, category, subcategory
- **SCD:** valid_from, valid_to, is_current

### dim_location
- **Grain:** One row per location
- **Key:** `location_key`
- **Attributes:** location_id, location_name, city, state, country, region

## Fact Tables

### fact_transactions
- **Grain:** One row per transaction
- **Keys:** date_key, customer_key, product_key, location_key
- **Measures:** amount, quantity
- **Degenerate Dimensions:** transaction_id, status

## Analytical Marts

*(To be defined based on business requirements)*

## Notes

- The dimensional model is extensible — dimension and fact tables will be added or modified based on the final business domain.
- SCD Type 2 is used for slowly changing dimensions (customer, product) to track historical changes.
