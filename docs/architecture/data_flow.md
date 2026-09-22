# Data Flow

## Overview

This document describes the data flow through the system from source to BI consumption.

## High-Level Flow

```
Sources → Ingestion → Quality/Contracts → Transformation → Storage → Warehouse → Semantic Layer → BI
```

## Data Zones

| Zone       | Directory / Schema | Purpose                                        |
|------------|-------------------|------------------------------------------------|
| Raw        | `data/raw/`, `raw` schema | Original data as-is from sources      |
| Quarantine | `data/quarantine/` | Invalid/rejected records with context          |
| Staging    | `data/staging/`, `staging` schema | Intermediate processing        |
| Processed  | `data/processed/`  | Cleaned and transformed data                   |
| Curated    | `data/curated/`, `analytics` schema | BI-ready analytical datasets  |
| Archive    | `data/archive/`    | Historical data retention                      |

## Flow Details

*(To be documented in detail during Phase 2 implementation)*
