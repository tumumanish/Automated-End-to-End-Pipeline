-- ============================================================
-- PostgreSQL Initialization Script
-- ============================================================
-- This script runs automatically when PostgreSQL container starts.
-- It creates the logical schemas for the data warehouse.
-- ============================================================

-- Raw data zone
CREATE SCHEMA IF NOT EXISTS raw;

-- Staging zone
CREATE SCHEMA IF NOT EXISTS staging;

-- Warehouse zone (facts + dimensions)
CREATE SCHEMA IF NOT EXISTS warehouse;

-- Analytics zone (views + marts)
CREATE SCHEMA IF NOT EXISTS analytics;

-- Metadata zone (lineage + contracts + audit)
CREATE SCHEMA IF NOT EXISTS metadata;

-- Monitoring zone (quality + pipeline metrics)
CREATE SCHEMA IF NOT EXISTS monitoring;
