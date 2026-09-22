# System Architecture

## Overview

The system follows a clean layered architecture with separation of concerns at every level.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
│              APIs  │  CSV  │  Excel  │  Databases               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION LAYER                             │
│       api_ingestion │ csv_ingestion │ excel_ingestion           │
│       database_ingestion │ ingestion_factory                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              DATA QUALITY / CONTRACT LAYER                      │
│       contract_loader │ contract_validator │ schema_validator    │
│       contract_registry │ quarantine_manager                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TRANSFORMATION LAYER                          │
│       cleaning │ normalization │ deduplication                   │
│       type_conversion │ business_rules │ enrichment             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              STORAGE / DATA WAREHOUSE                           │
│       PostgreSQL │ Snowflake │ Versioning │ Checkpoints         │
│       Raw → Staging → Warehouse → Analytics                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              SEMANTIC / ANALYTICAL LAYER                         │
│       Dimensions │ Facts │ Marts │ Views                        │
│       Star Schema │ KPI Definitions                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BI / REPORTING LAYER                            │
│                Power BI  │  Tableau                              │
└─────────────────────────────────────────────────────────────────┘

╔═════════════════════════════════════════════════════════════════╗
║             CROSS-CUTTING CONCERNS (All Layers)                ║
║  Observability │ Governance │ Lineage │ Error Handling          ║
║  Monitoring │ Logging │ Alerts │ Audit                         ║
╚═════════════════════════════════════════════════════════════════╝
```

## Layer Responsibilities

### Ingestion Layer
- Extract data from heterogeneous sources
- Source-agnostic interface via factory pattern
- Metadata capture at extraction time

### Data Quality / Contract Layer
- Enforce data contracts before or after storage
- Schema validation and business rule validation
- Quarantine invalid records with full context

### Transformation Layer
- Clean, normalize, deduplicate, and enrich data
- Apply business rules and type conversions
- Composable transformation pipeline

### Storage / Data Warehouse
- Versioned raw data preservation
- PostgreSQL for local development
- Snowflake for cloud analytical workloads
- Schema separation: raw → staging → warehouse → analytics

### Semantic / Analytical Layer
- Dimensional modeling with star schema
- Fact and dimension tables
- Analytical marts and views
- Standardized KPI definitions

### BI / Reporting Layer
- Power BI and Tableau consume curated datasets
- Never access raw or staging data directly

### Cross-Cutting Concerns
- **Observability:** Quality metrics, pipeline metrics, alerting
- **Governance:** Data contracts, versioning, audit trails
- **Lineage:** Source-to-destination tracking at every stage
- **Error Handling:** Categorized errors, retry, quarantine
