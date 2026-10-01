-- ============================================================
-- PostgreSQL: Create Staging Tables
-- ============================================================
-- Staging zone tables for intermediate processing between
-- curated data and the warehouse dimensional model.
-- Staging tables are TRUNCATED before each load cycle.
-- ============================================================

-- Staging: Transactions (landing table for curated batch data)
CREATE TABLE IF NOT EXISTS staging.stg_transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255),
    product_id VARCHAR(255),
    transaction_date DATE,
    quantity INTEGER,
    unit_price NUMERIC(15, 2),
    total_amount NUMERIC(15, 2),
    location VARCHAR(255),
    batch_id VARCHAR(100),
    loaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Staging: Customers (extracted unique customers for dim loading)
CREATE TABLE IF NOT EXISTS staging.stg_customers (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    customer_name VARCHAR(255),
    segment VARCHAR(100),
    region VARCHAR(100),
    batch_id VARCHAR(100),
    loaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Staging: Products (extracted unique products for dim loading)
CREATE TABLE IF NOT EXISTS staging.stg_products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    product_name VARCHAR(255),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    unit_price NUMERIC(15, 2),
    batch_id VARCHAR(100),
    loaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Staging: Locations (extracted unique locations for dim loading)
CREATE TABLE IF NOT EXISTS staging.stg_locations (
    id SERIAL PRIMARY KEY,
    location_id VARCHAR(255) NOT NULL,
    location_name VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    region VARCHAR(100),
    batch_id VARCHAR(100),
    loaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for staging lookups during surrogate key resolution
CREATE INDEX IF NOT EXISTS idx_stg_txn_transaction_id ON staging.stg_transactions(transaction_id);
CREATE INDEX IF NOT EXISTS idx_stg_txn_batch_id ON staging.stg_transactions(batch_id);
CREATE INDEX IF NOT EXISTS idx_stg_cust_customer_id ON staging.stg_customers(customer_id);
CREATE INDEX IF NOT EXISTS idx_stg_prod_product_id ON staging.stg_products(product_id);
CREATE INDEX IF NOT EXISTS idx_stg_loc_location_id ON staging.stg_locations(location_id);
