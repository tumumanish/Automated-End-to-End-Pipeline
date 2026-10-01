-- ============================================================
-- PostgreSQL: Create Fact Tables
-- ============================================================
-- Warehouse zone fact tables for the star schema.
-- Central fact table with foreign keys to all dimension tables.
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- Transactions Fact Table
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS warehouse.fact_transactions (
    transaction_key SERIAL PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    customer_key INTEGER NOT NULL REFERENCES warehouse.dim_customer(customer_key),
    product_key INTEGER NOT NULL REFERENCES warehouse.dim_product(product_key),
    location_key INTEGER NOT NULL REFERENCES warehouse.dim_location(location_key),
    transaction_id VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(15, 2) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'completed',
    batch_id VARCHAR(100),
    loaded_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for common analytical queries
CREATE INDEX IF NOT EXISTS idx_fact_txn_date ON warehouse.fact_transactions(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_txn_customer ON warehouse.fact_transactions(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_txn_product ON warehouse.fact_transactions(product_key);
CREATE INDEX IF NOT EXISTS idx_fact_txn_location ON warehouse.fact_transactions(location_key);
CREATE INDEX IF NOT EXISTS idx_fact_txn_batch ON warehouse.fact_transactions(batch_id);
CREATE INDEX IF NOT EXISTS idx_fact_txn_id ON warehouse.fact_transactions(transaction_id);
