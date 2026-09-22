# Implementation Guide

## Overview

This document provides implementation guidance for Phase 2 and beyond.

## Implementation Order

1. **Utilities first:** `src/utils/` (logger, hashing, timestamps, file_utils)
2. **Errors & Exceptions:** `src/errors/` (exception classes, error handler)
3. **Contracts:** `src/contracts/` (loader, validator, registry) - **Completed**
4. **Ingestion:** `src/ingestion/` (CSV first, then API, Excel, Database) - **Completed**
5. **Transformation:** `src/transformation/` (cleaning → normalization → deduplication)
6. **Storage:** `src/storage/postgres/` (connection → loader → queries)
7. **Pipeline:** `src/pipelines/etlt_plus_plus.py` (compose all above)
8. **Monitoring:** `src/monitoring/` (quality metrics, freshness, completeness)
9. **Lineage:** `src/lineage/` (tracker, collector, store)
10. **API:** `api/` (health → pipelines → data_quality → lineage)
11. **Warehouse:** SQL scripts and dimensional model
12. **BI:** Dashboard connections and documentation

## Guidelines

- Always use configuration from `config/` — never hard-code
- Always use environment variables for credentials
- Always log operations with context (batch_id, source, stage)
- Always write tests alongside implementation
- Always update documentation when implementation changes

## Details

*(To be expanded during implementation)*
