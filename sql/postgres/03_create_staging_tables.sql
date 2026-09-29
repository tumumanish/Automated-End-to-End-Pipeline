-- ============================================================
-- PostgreSQL: Create Staging Tables
-- ============================================================
-- Staging zone tables for intermediate processing.
-- Holds data between raw ingestion and warehouse loading.
-- ============================================================

CREATE TABLE IF NOT EXISTS staging.transactions (
    id                   SERIAL PRIMARY KEY,
    transaction_id       VARCHAR(255)  NOT NULL,
    customer_id          VARCHAR(255),
    product_id           VARCHAR(255),
    transaction_date     DATE,
    quantity             INTEGER,
    unit_price           NUMERIC(15, 2),
    total_amount         NUMERIC(15, 2),
    location             VARCHAR(255),
    status               VARCHAR(50),
    calculated_total     NUMERIC(15, 2),
    is_high_value        BOOLEAN,
    needs_location_review BOOLEAN,
    batch_id             VARCHAR(100),
    processed_timestamp  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_staging_transactions_batch
    ON staging.transactions (batch_id);

CREATE INDEX IF NOT EXISTS idx_staging_transactions_date
    ON staging.transactions (transaction_date);
