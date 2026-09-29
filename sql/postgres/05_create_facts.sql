-- ============================================================
-- PostgreSQL: Create Fact Tables
-- ============================================================
-- Warehouse zone fact tables for the star schema.
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.fact_transactions (
    transaction_key   SERIAL PRIMARY KEY,
    date_key          INTEGER REFERENCES warehouse.dim_date(date_key),
    customer_key      INTEGER REFERENCES warehouse.dim_customer(customer_key),
    product_key       INTEGER REFERENCES warehouse.dim_product(product_key),
    location_key      INTEGER REFERENCES warehouse.dim_location(location_key),
    transaction_id    VARCHAR(255) NOT NULL,
    amount            NUMERIC(15, 2),
    quantity          INTEGER,
    unit_price        NUMERIC(15, 2),
    status            VARCHAR(50),
    is_high_value     BOOLEAN DEFAULT FALSE,
    batch_id          VARCHAR(100),
    loaded_timestamp  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fact_transactions_date
    ON warehouse.fact_transactions (date_key);

CREATE INDEX IF NOT EXISTS idx_fact_transactions_customer
    ON warehouse.fact_transactions (customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_transactions_product
    ON warehouse.fact_transactions (product_key);

CREATE INDEX IF NOT EXISTS idx_fact_transactions_location
    ON warehouse.fact_transactions (location_key);

CREATE INDEX IF NOT EXISTS idx_fact_transactions_batch
    ON warehouse.fact_transactions (batch_id);
