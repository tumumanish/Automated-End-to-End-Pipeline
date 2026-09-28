-- ============================================================
-- PostgreSQL: Create Lineage & Metadata Tables
-- ============================================================
-- Metadata zone — lineage events, data versions, checkpoints.
-- Person A ownership.
-- ============================================================

-- Lineage events — one row per pipeline stage execution
CREATE TABLE IF NOT EXISTS metadata.lineage_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) NOT NULL UNIQUE,
    batch_id VARCHAR(100) NOT NULL,
    pipeline_name VARCHAR(100) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    source_system VARCHAR(100),
    dataset_name VARCHAR(100),
    contract_version VARCHAR(20),
    input_record_count INTEGER DEFAULT 0,
    output_record_count INTEGER DEFAULT 0,
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_le_batch_id
    ON metadata.lineage_events (batch_id);

CREATE INDEX IF NOT EXISTS idx_le_dataset
    ON metadata.lineage_events (dataset_name);

-- Data version records — SCD Type 2 tracking
CREATE TABLE IF NOT EXISTS metadata.data_versions (
    id SERIAL PRIMARY KEY,
    record_id VARCHAR(255) NOT NULL,
    dataset_name VARCHAR(100) NOT NULL,
    source_system VARCHAR(100),
    batch_id VARCHAR(100),
    ingestion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_to TIMESTAMP WITH TIME ZONE,
    record_hash VARCHAR(64) NOT NULL,
    schema_version VARCHAR(20),
    is_current BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_dv_record_id
    ON metadata.data_versions (record_id);

CREATE INDEX IF NOT EXISTS idx_dv_current
    ON metadata.data_versions (dataset_name, is_current)
    WHERE is_current = TRUE;

-- Pipeline checkpoints — resume state
CREATE TABLE IF NOT EXISTS metadata.checkpoints (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,
    pipeline_name VARCHAR(100) NOT NULL,
    last_completed_stage VARCHAR(50) NOT NULL,
    checkpoint_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    state JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_cp_pipeline
    ON metadata.checkpoints (pipeline_name, checkpoint_timestamp DESC);
