# Database Schema

## Overview

The database uses logical schema separation to organize data by processing stage.

## Schemas

| Schema       | Purpose                                                 |
|--------------|---------------------------------------------------------|
| `raw`        | Ingested data as-is with versioning metadata            |
| `staging`    | Intermediate processing and transformation              |
| `warehouse`  | Dimensional model — fact and dimension tables            |
| `analytics`  | Analytical views, marts, and BI-ready datasets          |
| `metadata`   | Lineage records, contract metadata, audit trails        |
| `monitoring` | Quality metrics, pipeline metrics, alert records        |

## Schema Details

*(To be documented in detail when tables are implemented in Phase 2)*
