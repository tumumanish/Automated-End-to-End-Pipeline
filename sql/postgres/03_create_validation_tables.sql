-- sql/postgres/03_create_validation_tables.sql
-- Description: Creates metadata tables for tracking data quality and validation runs.

-- 1. Validation Runs Table
-- Tracks high-level execution of validation against a batch
CREATE TABLE IF NOT EXISTS metadata.validation_runs (
    validation_run_id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50) NOT NULL REFERENCES metadata.ingestion_batches(batch_id) ON DELETE CASCADE,
    dataset_name VARCHAR(100) NOT NULL,
    contract_version VARCHAR(20) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_records INTEGER NOT NULL,
    valid_records INTEGER NOT NULL,
    invalid_records INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL, -- PASS, FAILED
    error_count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_validation_runs_batch_id ON metadata.validation_runs(batch_id);
CREATE INDEX IF NOT EXISTS idx_validation_runs_dataset ON metadata.validation_runs(dataset_name);

-- 2. Validation Errors Table
-- Tracks detailed row-level and field-level validation errors
CREATE TABLE IF NOT EXISTS metadata.validation_errors (
    error_id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50) NOT NULL REFERENCES metadata.ingestion_batches(batch_id) ON DELETE CASCADE,
    dataset_name VARCHAR(100) NOT NULL,
    contract_version VARCHAR(20) NOT NULL,
    row_number INTEGER,
    field_name VARCHAR(100) NOT NULL,
    rule_name VARCHAR(50) NOT NULL,
    actual_value TEXT,
    expected_value TEXT,
    error_message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_validation_errors_batch_id ON metadata.validation_errors(batch_id);
CREATE INDEX IF NOT EXISTS idx_validation_errors_dataset ON metadata.validation_errors(dataset_name);
