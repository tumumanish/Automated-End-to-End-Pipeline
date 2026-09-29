-- ============================================================
-- PostgreSQL: Create Dimension Tables
-- ============================================================
-- Warehouse zone dimension tables for the star schema.
-- ============================================================

-- Date Dimension
CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_key      INTEGER PRIMARY KEY,
    full_date     DATE          NOT NULL,
    day_of_week   INTEGER,
    day_name      VARCHAR(20),
    month         INTEGER,
    month_name    VARCHAR(20),
    quarter       INTEGER,
    year          INTEGER,
    is_weekend    BOOLEAN DEFAULT FALSE,
    is_holiday    BOOLEAN DEFAULT FALSE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_date_full_date
    ON warehouse.dim_date (full_date);

-- Customer Dimension (SCD Type 2)
CREATE TABLE IF NOT EXISTS warehouse.dim_customer (
    customer_key  SERIAL PRIMARY KEY,
    customer_id   VARCHAR(255)  NOT NULL,
    customer_name VARCHAR(255),
    segment       VARCHAR(100),
    region        VARCHAR(100),
    valid_from    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_to      TIMESTAMP WITH TIME ZONE,
    is_current    BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_dim_customer_id
    ON warehouse.dim_customer (customer_id);

CREATE INDEX IF NOT EXISTS idx_dim_customer_current
    ON warehouse.dim_customer (customer_id, is_current);

-- Product Dimension (SCD Type 2)
CREATE TABLE IF NOT EXISTS warehouse.dim_product (
    product_key   SERIAL PRIMARY KEY,
    product_id    VARCHAR(255)  NOT NULL,
    product_name  VARCHAR(255),
    category      VARCHAR(100),
    subcategory   VARCHAR(100),
    valid_from    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_to      TIMESTAMP WITH TIME ZONE,
    is_current    BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_dim_product_id
    ON warehouse.dim_product (product_id);

CREATE INDEX IF NOT EXISTS idx_dim_product_current
    ON warehouse.dim_product (product_id, is_current);

-- Location Dimension
CREATE TABLE IF NOT EXISTS warehouse.dim_location (
    location_key  SERIAL PRIMARY KEY,
    location_id   VARCHAR(255)  NOT NULL,
    location_name VARCHAR(255),
    city          VARCHAR(100),
    state         VARCHAR(100),
    country       VARCHAR(100),
    region        VARCHAR(100)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_location_id
    ON warehouse.dim_location (location_id);
