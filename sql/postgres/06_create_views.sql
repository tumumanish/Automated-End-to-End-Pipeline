-- ============================================================
-- PostgreSQL: Create Analytical Views
-- ============================================================
-- Analytics zone views for BI consumption.
-- All views join facts with dimensions for BI-ready datasets.
-- ============================================================

-- Daily Sales Summary
CREATE OR REPLACE VIEW analytics.v_daily_sales AS
SELECT
    d.full_date,
    d.day_name,
    d.month,
    d.month_name,
    d.quarter,
    d.year,
    d.is_weekend,
    SUM(f.amount)                  AS total_sales,
    SUM(f.quantity)                AS total_quantity,
    COUNT(*)                       AS transaction_count,
    AVG(f.amount)                  AS avg_transaction_value,
    COUNT(DISTINCT f.customer_key) AS unique_customers
FROM warehouse.fact_transactions f
JOIN warehouse.dim_date d ON f.date_key = d.date_key
GROUP BY d.full_date, d.day_name, d.month, d.month_name, d.quarter, d.year, d.is_weekend;

-- Product Performance
CREATE OR REPLACE VIEW analytics.v_product_performance AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.subcategory,
    SUM(f.amount)     AS total_revenue,
    SUM(f.quantity)   AS units_sold,
    COUNT(*)          AS transaction_count,
    AVG(f.amount)     AS avg_transaction_value,
    AVG(f.unit_price) AS avg_unit_price
FROM warehouse.fact_transactions f
JOIN warehouse.dim_product p ON f.product_key = p.product_key
WHERE p.is_current = TRUE
GROUP BY p.product_id, p.product_name, p.category, p.subcategory;

-- Regional Analysis
CREATE OR REPLACE VIEW analytics.v_regional_analysis AS
SELECT
    l.location_id,
    l.location_name,
    l.city,
    l.state,
    l.country,
    l.region,
    SUM(f.amount)                  AS total_sales,
    SUM(f.quantity)                AS total_quantity,
    COUNT(*)                       AS transaction_count,
    COUNT(DISTINCT f.customer_key) AS unique_customers,
    AVG(f.amount)                  AS avg_transaction_value
FROM warehouse.fact_transactions f
JOIN warehouse.dim_location l ON f.location_key = l.location_key
GROUP BY l.location_id, l.location_name, l.city, l.state, l.country, l.region;

-- Customer Summary
CREATE OR REPLACE VIEW analytics.v_customer_summary AS
SELECT
    c.customer_id,
    c.customer_name,
    c.segment,
    c.region,
    COUNT(*)         AS total_transactions,
    SUM(f.amount)    AS total_spend,
    AVG(f.amount)    AS avg_order_value,
    MIN(d.full_date) AS first_purchase_date,
    MAX(d.full_date) AS last_purchase_date
FROM warehouse.fact_transactions f
JOIN warehouse.dim_customer c ON f.customer_key = c.customer_key
JOIN warehouse.dim_date d     ON f.date_key     = d.date_key
WHERE c.is_current = TRUE
GROUP BY c.customer_id, c.customer_name, c.segment, c.region;

-- Full Transaction Detail (for BI drill-through)
CREATE OR REPLACE VIEW analytics.v_transaction_detail AS
SELECT
    f.transaction_id,
    d.full_date        AS transaction_date,
    d.month_name,
    d.quarter,
    d.year,
    c.customer_id,
    c.customer_name,
    c.segment          AS customer_segment,
    p.product_id,
    p.product_name,
    p.category         AS product_category,
    l.location_name,
    l.city,
    l.region,
    f.quantity,
    f.unit_price,
    f.amount           AS total_amount,
    f.is_high_value,
    f.status,
    f.batch_id
FROM warehouse.fact_transactions f
JOIN warehouse.dim_date     d ON f.date_key     = d.date_key
JOIN warehouse.dim_customer c ON f.customer_key = c.customer_key
JOIN warehouse.dim_product  p ON f.product_key  = p.product_key
JOIN warehouse.dim_location l ON f.location_key = l.location_key
WHERE c.is_current = TRUE
  AND p.is_current = TRUE;
