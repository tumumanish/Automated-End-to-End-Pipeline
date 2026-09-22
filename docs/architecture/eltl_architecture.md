# ELTL++ Architecture

## Overview

ELTL++ (Extract-Load-Transform-Load Plus Plus) is the secondary pipeline pattern that emphasizes **raw data preservation** in an immutable zone before transformation.

## Pipeline Flow

```
Extract (API / CSV / Excel / Database)
   ↓
Raw Load (Immutable Raw Zone)
   ↓
Managed Raw Layer (cleaning, standardization)
   ↓
Transformation (dimensional modeling, business rules)
   ↓
Curated Semantic Layer (KPIs, analytical datasets)
   ↓
BI Layer (Power BI / Tableau)
```

## Stage Details

### 1. Extract
- Use `ingestion_factory` to select appropriate extraction strategy
- Capture source metadata

### 2. Raw Load (Immutable Raw Zone)
- Store raw data as-is in immutable raw zone
- Preserve original format and content
- Add versioning metadata (batch_id, timestamp, hash)
- No transformations applied at this stage

### 3. Managed Raw Layer
- Apply basic cleaning and standardization
- Validate against contracts (post-load)
- Quarantine invalid records
- Metadata-driven processing

### 4. Transformation
- Apply business transformation rules
- Dimensional modeling (facts + dimensions)
- Deduplication and enrichment
- SCD Type 2 versioning for dimensions

### 5. Curated Semantic Layer
- Standardized KPI definitions
- Analytical marts and views
- BI-ready datasets

### 6. BI Layer
- Curated datasets consumed by Power BI and Tableau

## Key Differences from ETLT++

| Aspect               | ETLT++                        | ELTL++                         |
|----------------------|-------------------------------|--------------------------------|
| Validation timing    | Before storage                | After raw storage              |
| Raw data             | Validated before storage      | Preserved as-is (immutable)    |
| Data loss risk       | Lower (validated first)       | None (raw always preserved)    |
| Reprocessing         | From validated raw            | From immutable raw zone        |
| Retention            | Configurable                  | Full raw retention             |

## Implementation

- **Module:** `src/pipelines/eltl_plus_plus.py`
- **Configuration:** `config/pipeline.yaml` → `eltl_plus_plus`
