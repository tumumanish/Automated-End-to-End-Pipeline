-- ============================================================
-- PostgreSQL: Create Monitoring Tables
-- ============================================================
-- Monitoring zone — quality metrics, pipeline execution tracking.
-- Person A ownership.
-- ============================================================

-- Batch-level quality metrics
CREATE TABLE IF NOT EXISTS monitoring.batch_quality_metrics (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(100) NOT NULL,
    dataset_name VARCHAR(100),
    source VARCHAR(50),
    metric_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    record_count INTEGER DEFAULT 0,
    valid_count INTEGER DEFAULT 0,
    invalid_count INTEGER DEFAULT 0,
    quarantined_count INTEGER DEFAULT 0,
    freshness_score NUMERIC(5, 2),
    completeness_score NUMERIC(5, 2),
    accuracy_score NUMERIC(5, 2),
    contract_adherence_score NUMERIC(5, 2),
    pipeline_status VARCHAR(20),
    processing_duration NUMERIC(10, 2)
);

CREATE INDEX IF NOT EXISTS idx_bqm_batch_id
    ON monitoring.batch_quality_metrics (batch_id);

CREATE INDEX IF NOT EXISTS idx_bqm_dataset
    ON monitoring.batch_quality_metrics (dataset_name);

-- Pipeline execution metrics
CREATE TABLE IF NOT EXISTS monitoring.pipeline_metrics (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    execution_id VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(20),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds NUMERIC(10, 2),
    records_extracted INTEGER DEFAULT 0,
    records_valid INTEGER DEFAULT 0,
    records_invalid INTEGER DEFAULT 0,
    records_transformed INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_pm_pipeline_name
    ON monitoring.pipeline_metrics (pipeline_name);

CREATE INDEX IF NOT EXISTS idx_pm_started_at
    ON monitoring.pipeline_metrics (started_at);

-- Alert log
CREATE TABLE IF NOT EXISTS monitoring.alert_log (
    id SERIAL PRIMARY KEY,
    alert_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    severity VARCHAR(20) NOT NULL,
    category VARCHAR(50),
    message TEXT NOT NULL,
    batch_id VARCHAR(100),
    dataset_name VARCHAR(100),
    metric_name VARCHAR(50),
    metric_value NUMERIC(10, 2),
    threshold_value NUMERIC(10, 2),
    acknowledged BOOLEAN DEFAULT FALSE
);
