# ETLT++ Architecture

## Overview

ETLT++ (Extract-Transform-Load-Transform Plus Plus) is the primary pipeline pattern that emphasizes **contract-first validation** before data reaches storage.

## Pipeline Flow

```
Extract (API / CSV / Excel / Database)
   ↓
Data Contract Loading & Validation
   ↓
Record-level & Batch-level Validation / Cleaning
   ↓
Versioned Raw Storage (with metadata)
   ↓
Business Transformation (rules, enrichment)
   ↓
Curated Analytical Output (dimensions, facts, views)
   ↓
BI Layer (Power BI / Tableau)
```

## Stage Details

### 1. Extract
- Use `ingestion_factory` to select appropriate extraction strategy
- Capture source metadata (timestamp, record count, source system)

### 2. Data Contract Validation
- Load contract from `contract_registry`
- Validate schema (field presence, data types, nullable)
- Apply hard rules (reject) and soft rules (warn)

### 3. Validation / Cleaning
- Record-level validation against contract rules
- Quarantine records that fail hard rules
- Log warnings for soft rule violations
- Apply cleaning transformations (missing values, whitespace)

### 4. Versioned Raw Storage
- Store validated data in raw zone with versioning metadata
- Record: `record_id`, `batch_id`, `ingestion_timestamp`, `record_hash`, `schema_version`

### 5. Business Transformation
- Apply business rules and derived fields
- Normalize and enrich data
- Deduplicate records

### 6. Curated Analytical Output
- Load into dimensional model (facts + dimensions)
- Create analytical views and marts
- Generate standardized KPIs

### 7. BI Layer
- Curated datasets consumed by Power BI and Tableau

## Cross-Cutting at Every Stage
- Lineage tracking
- Quality monitoring
- Error handling
- Checkpoint recording

## Implementation

- **Module:** `src/pipelines/etlt_plus_plus.py`
- **Configuration:** `config/pipeline.yaml` → `etlt_plus_plus`
