-- ============================================================
-- PostgreSQL: Create Schemas
-- ============================================================
-- Creates the logical schema separation for the data warehouse.
-- ============================================================

-- Raw data zone — ingested data as-is
CREATE SCHEMA IF NOT EXISTS raw;

-- Staging zone — intermediate processing
CREATE SCHEMA IF NOT EXISTS staging;

-- Warehouse zone — dimensional model (facts + dimensions)
CREATE SCHEMA IF NOT EXISTS warehouse;

-- Analytics zone — analytical views and marts
CREATE SCHEMA IF NOT EXISTS analytics;

-- Metadata zone — lineage, contracts, audit records
CREATE SCHEMA IF NOT EXISTS metadata;

-- Monitoring zone — quality metrics, pipeline metrics
CREATE SCHEMA IF NOT EXISTS monitoring;
