-- ============================================================
-- PostgreSQL: Create Dimension Tables
-- ============================================================
-- Warehouse zone dimension tables for the star schema.
-- Implements Kimball-style dimensional modeling with SCD Type 2
-- tracking on customer and product dimensions.
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- Date Dimension (pre-populated calendar table)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_year INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    quarter INTEGER NOT NULL,
    year INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL DEFAULT FALSE,
    is_holiday BOOLEAN NOT NULL DEFAULT FALSE,
    fiscal_quarter INTEGER,
    fiscal_year INTEGER
);

-- ────────────────────────────────────────────────────────────
-- Customer Dimension (SCD Type 2)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS warehouse.dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    customer_name VARCHAR(255),
    segment VARCHAR(100),
    region VARCHAR(100),
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMP WITH TIME ZONE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_dim_cust_id ON warehouse.dim_customer(customer_id);
CREATE INDEX IF NOT EXISTS idx_dim_cust_current ON warehouse.dim_customer(customer_id, is_current)
    WHERE is_current = TRUE;

-- ────────────────────────────────────────────────────────────
-- Product Dimension (SCD Type 2)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS warehouse.dim_product (
    product_key SERIAL PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    product_name VARCHAR(255),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    unit_price NUMERIC(15, 2),
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMP WITH TIME ZONE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_dim_prod_id ON warehouse.dim_product(product_id);
CREATE INDEX IF NOT EXISTS idx_dim_prod_current ON warehouse.dim_product(product_id, is_current)
    WHERE is_current = TRUE;

-- ────────────────────────────────────────────────────────────
-- Location Dimension (Type 1 — overwrite on change)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS warehouse.dim_location (
    location_key SERIAL PRIMARY KEY,
    location_id VARCHAR(255) NOT NULL UNIQUE,
    location_name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    region VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_dim_loc_id ON warehouse.dim_location(location_id);
