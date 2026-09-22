-- ============================================================
-- PostgreSQL: Create Phase 2 Tables
-- ============================================================
-- Creates raw ingestion tables and metadata tracking tables.
-- Safe to execute multiple times (idempotent).
-- ============================================================

-- ----------------------------------------------------------
-- 1. RAW TRANSACTION TABLE
-- ----------------------------------------------------------
-- Stores raw ingested transaction records as-is from source.
-- Each record is tagged with its ingestion batch for traceability.

CREATE TABLE IF NOT EXISTS raw.transactions (
    id                  SERIAL PRIMARY KEY,
    transaction_id      VARCHAR(100),
    customer_id         VARCHAR(100),
    product_id          VARCHAR(100),
    transaction_date    DATE,
    quantity            INTEGER,
    unit_price          NUMERIC(12, 2),
    total_amount        NUMERIC(12, 2),
    location            VARCHAR(200),
    source_system       VARCHAR(50)   NOT NULL DEFAULT 'unknown',
    ingestion_batch_id  VARCHAR(100)  NOT NULL,
    ingestion_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index for batch-level queries
CREATE INDEX IF NOT EXISTS idx_raw_txn_batch
    ON raw.transactions (ingestion_batch_id);

-- Index for transaction lookups
CREATE INDEX IF NOT EXISTS idx_raw_txn_id
    ON raw.transactions (transaction_id);

-- ----------------------------------------------------------
-- 2. INGESTION BATCH TABLE
-- ----------------------------------------------------------
-- Tracks every ingestion execution with status and metrics.

CREATE TABLE IF NOT EXISTS metadata.ingestion_batches (
    batch_id        VARCHAR(100) PRIMARY KEY,
    source_type     VARCHAR(50)  NOT NULL,          -- csv, api, excel, database
    source_name     VARCHAR(500),                    -- file path or URL
    dataset_name    VARCHAR(200) NOT NULL,            -- logical dataset name
    started_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMP WITH TIME ZONE,
    status          VARCHAR(20)  NOT NULL DEFAULT 'RUNNING',  -- RUNNING, SUCCESS, FAILED
    record_count    INTEGER      DEFAULT 0,
    file_path       VARCHAR(500),                    -- raw file storage path
    source_version  VARCHAR(50),
    error_message   TEXT,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------
-- 3. INGESTION AUDIT TABLE
-- ----------------------------------------------------------
-- Records fine-grained events during ingestion for auditability.

CREATE TABLE IF NOT EXISTS metadata.ingestion_audit (
    audit_id        SERIAL PRIMARY KEY,
    batch_id        VARCHAR(100) NOT NULL,
    stage           VARCHAR(100) NOT NULL,            -- e.g., extract, raw_store, db_load
    event_type      VARCHAR(100) NOT NULL,            -- e.g., STARTED, COMPLETED, FAILED
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    message         TEXT,
    record_count    INTEGER DEFAULT 0
);

-- Index for batch audit queries
CREATE INDEX IF NOT EXISTS idx_audit_batch
    ON metadata.ingestion_audit (batch_id);
