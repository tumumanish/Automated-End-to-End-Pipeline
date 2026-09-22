-- ============================================================
-- Snowflake: Create Raw Tables
-- ============================================================

-- TODO: Create Snowflake-specific raw tables.
-- Consider Snowflake VARIANT type for semi-structured raw data.

-- Example:
-- CREATE TABLE IF NOT EXISTS raw.transactions (
--     id INTEGER AUTOINCREMENT PRIMARY KEY,
--     record_id VARCHAR,
--     source_system VARCHAR,
--     batch_id VARCHAR,
--     ingestion_timestamp TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
--     record_hash VARCHAR,
--     schema_version VARCHAR,
--     raw_data VARIANT
-- );
