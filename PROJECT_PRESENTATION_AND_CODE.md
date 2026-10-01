# Automated End-to-End Data Pipeline & Business Intelligence Architecture
## Major Project Presentation Guide & Code Showcase

**B.Tech CSE (Data Science) — Major Project | Batch 19**  
**Document Type:** Project Presentation Master Guide, Architecture Deep-Dive & Sample Code  
**Target Audience:** Project Evaluators, Technical Panels, External Examiners, and Development Teams  

---

## Table of Contents
1. [Executive Summary & Project Overview](#1-executive-summary--project-overview)
2. [Problem Statement & Key Objectives](#2-problem-statement--key-objectives)
3. [System Architecture & Core Design Paradigms](#3-system-architecture--core-design-paradigms)
4. [Layer-by-Layer Architectural Breakdown](#4-layer-by-layer-architectural-breakdown)
   - [4.1 Multi-Source Ingestion Layer](#41-multi-source-ingestion-layer)
   - [4.2 Data Contracts & Schema Validation Gate](#42-data-contracts--schema-validation-gate)
   - [4.3 Two-Stage Transformation Engine (T1 & T2)](#43-two-stage-transformation-engine-t1--t2)
   - [4.4 SCD Type 2 Data Versioning & Checkpointing](#44-scd-type-2-data-versioning--checkpointing)
   - [4.5 Layered Data Warehouse & Dimensional Star Schema](#45-layered-data-warehouse--dimensional-star-schema)
   - [4.6 Comprehensive Observability & Quality Monitoring](#46-comprehensive-observability--quality-monitoring)
   - [4.7 End-to-End Data Lineage & Audit Trails](#47-end-to-end-data-lineage--audit-trails)
   - [4.8 FastAPI Control Plane & Monitoring REST API](#48-fastapi-control-plane--monitoring-rest-api)
   - [4.9 Business Intelligence Dashboards (Power BI & Tableau)](#49-business-intelligence-dashboards-power-bi--tableau)
5. [Presentation Code Showcase (Live Demo & Slides)](#5-presentation-code-showcase-live-demo--slides)
   - [Demo 1: Running the Complete ETLT++ Pipeline](#demo-1-running-the-complete-etlt-pipeline)
   - [Demo 2: Contract-Driven Validation & Automated Quarantine](#demo-2-contract-driven-validation--automated-quarantine)
   - [Demo 3: Unified Ingestion Factory in Action](#demo-3-unified-ingestion-factory-in-action)
   - [Demo 4: SCD Type 2 Versioning with SHA-256 Record Hashing](#demo-4-scd-type-2-versioning-with-sha-256-record-hashing)
   - [Demo 5: Pipeline Observability & Alert Triggering](#demo-5-pipeline-observability--alert-triggering)
   - [Demo 6: Data Lineage Graph Reconstruction](#demo-6-data-lineage-graph-reconstruction)
   - [Demo 7: Querying Star Schema & Analytical Views](#demo-7-querying-star-schema--analytical-views)
   - [Demo 8: FastAPI REST API Execution & Health Probing](#demo-8-fastapi-rest-api-execution--health-probing)
   - [Demo 9: Checkpointing & State Recovery](#demo-9-checkpointing--state-recovery)
6. [Slide-by-Slide Presentation Structure & Speaker Notes](#6-slide-by-slide-presentation-structure--speaker-notes)
7. [Technology Stack & Architectural Evaluation Summary](#7-technology-stack--architectural-evaluation-summary)

---

## 1. Executive Summary & Project Overview

Modern enterprise data ecosystems struggle with fragile data pipelines, lack of schema enforcement, absent data lineage, and poor auditability. When data producers change schema formats or send malformed data, downstream analytics and dashboards silently break.

This project designs and implements an **enterprise-ready, automated End-to-End Data Engineering and Business Intelligence Platform**. The platform ingests data from heterogeneous sources (REST APIs, CSV, Excel, RDBMS), subjects all records to strict versioned **Data Contracts**, performs deterministic two-stage transformations (T1 Contract Validation and T2 Business Rules), manages immutable raw and curated analytical storage (Parquet), maintains **SCD Type 2 versioning**, and publishes clean star-schema datasets to **PostgreSQL/Snowflake** for consumption by **Power BI** and **Tableau** dashboards.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 HIGH-LEVEL PLATFORM OVERVIEW                           │
│                                                                                        │
│   Heterogeneous         Contract-Driven          Layered Warehouse        Curated BI   │
│      Sources               Pipelines                 Storage              Dashboards   │
│   ┌───────────┐         ┌─────────────┐          ┌───────────────┐       ┌───────────┐ │
│   │ REST APIs │───┐     │   ETLT++    │          │  PostgreSQL   │   ┌──▶│ Power BI  │ │
│   │ CSV Files │───┼────▶│  Pipelines  │─────────▶│  (6 Schemas)  ├───┤   │ Tableau   │ │
│   │ Excel     │───┤     │   ELTL++    │          │  Star Schema  │   └──▶│ REST API  │ │
│   │ SQL DBs   │───┘     │  Pipelines  │          │  Curated Parq │       │ /docs     │ │
│   └───────────┘         └─────────────┘          └───────────────┘       └───────────┘ │
│                                │                                                       │
│          ┌─────────────────────┴──────────────────────┐                                │
│          ▼                                            ▼                                │
│   ┌───────────────┐                            ┌───────────────┐                       │
│   │ Observability │ Freshness, Completeness    │ Data Lineage  │ Graph Traceability,   │
│   │  & Monitoring │ Accuracy, Adherence        │  & Metadata   │ Checkpoint Recovery   │
│   └───────────────┘                            └───────────────┘                       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Problem Statement & Key Objectives

### 2.1 Problem Statement
Organizations lose millions due to "silent data corruption":
1. **Schema Drift & Data Corruption**: Producers modify schema without notice, causing downstream pipeline failures.
2. **Lack of Governance & Lineage**: Data engineers cannot track the lifecycle of a metric from source to visualization.
3. **Rigid Architectures**: Traditional ETL or ELT architectures cannot adapt to different latency, governance, or compliance requirements.
4. **Poor Observability**: Teams discover dirty data from executive dashboard errors rather than automated proactive alerts.

### 2.2 Project Objectives
- **Multi-Source Ingestion**: Ingest CSV, Excel, REST API, and RDBMS data via unified factory adapters.
- **Contract-Driven Quality Gate**: Enforce machine-readable JSON Data Contracts with automatic quarantine of corrupted rows.
- **Architectural Flexibility**: Implement both **ETLT++** (validation prior to business transforms) and **ELTL++** (immutable raw lake loading prior to managed transformation).
- **Zero Data Loss & Traceability**: Append-only SCD Type 2 record versioning and stage-level lineage graphs.
- **Dimensional Data Modeling**: Implement Kimball Star Schema with surrogate keys, dimension tables, fact tables, and analytical views.
- **Full-Stack Observability & Control**: Track 4 quality dimensions (Freshness, Completeness, Accuracy, Contract Adherence) backed by a FastAPI REST control plane and BI dashboards.

---

## 3. System Architecture & Core Design Paradigms

### 3.1 ETLT++ vs. ELTL++ Pipeline Patterns

The platform implements two foundational data engineering patterns:

```
ETLT++ PATTERN (Governance & Clean Storage Focus):
Extract ──▶ Immutable Raw ──▶ T1 Contract Validate ──▶ T2 Business Transform ──▶ Curated Parquet ──▶ Star Schema
                                    │ (invalid)
                                    └──▶ Quarantine (JSON Metadata)

ELTL++ PATTERN (Raw Data Lake & Replayability Focus):
Extract ──▶ Raw Immutable Lake ──▶ Managed Raw Zone ──▶ Transform & Validate ──▶ Curated Semantic ──▶ BI Layer
```

| Dimension | ETLT++ Architecture | ELTL++ Architecture |
|---|---|---|
| **Raw Loading** | Saved before validation for audit | Loaded directly as immutable lake records |
| **Validation Point** | T1 stage immediately after raw extraction | Managed Raw stage prior to dimensional transform |
| **Business Logic** | T2 transformation layer on validated data only | Transform stage with surrogate key joins |
| **Ideal For** | High-governance, regulatory, compliance pipelines | Big data lakes, exploratory analytics, re-processing |

---

## 4. Layer-by-Layer Architectural Breakdown

### 4.1 Multi-Source Ingestion Layer
- **Interface**: Abstract Base Class `BaseIngestion` with mandatory `extract()`, `source_type`, and `source_name`.
- **Supported Adapters**:
  - `CSVIngestion`: Delimiter detection, encoding fallbacks, memory-efficient chunking.
  - `ExcelIngestion`: Multi-sheet support via `openpyxl`.
  - `APIIngestion`: HTTP GET, timeout management, bearer/basic auth headers, JSON normalization.
  - `DatabaseIngestion`: SQLAlchemy RDBMS adapter supporting arbitrary SQL queries or table dumps.
- **Design Pattern**: `IngestionFactory.create_ingestion(source_type, **kwargs)` dynamically resolves the correct engine.

### 4.2 Data Contracts & Schema Validation Gate
- **Definition**: Version-controlled JSON schemas (`contracts/schemas/<dataset>_contract.json`).
- **Validation Layers**:
  1. **Structural Validation (`SchemaValidator`)**: Validates missing mandatory columns, extraneous unexpected fields, and null structures.
  2. **Row-Level Contract Validation (`ContractValidator`)**: Validates data types, non-null constraints, min/max ranges, regex formats (e.g., `YYYY-MM-DD`), and allowed enum values.
- **Quarantine Engine (`QuarantineManager`)**: Separates valid records from malformed records. Invalid records are isolated into `data/quarantine/` with a forensic JSON audit file recording row index, offending field, invalid value, and failure rule.

### 4.3 Two-Stage Transformation Engine (T1 & T2)
- **T1 Validation**: Pure contract enforcement (schema integrity).
- **T2 Transformation (`TransformationService`)**:
  - `cleaning.py`: Whitespace stripping, control character removal, null standardizations.
  - `normalization.py`: Date format ISO-8601 conversions, phone/currency standardizations.
  - `deduplication.py`: Exact row deduplication and business-key deduplication.
  - `business_rules.py`: Calculation of derived metrics (e.g., discount logic, total line amounts, order sizes).
  - `enrichment.py` & `type_conversion.py`: Foreign key mappings, strict type casting.

### 4.4 SCD Type 2 Data Versioning & Checkpointing
- **SCD Type 2 (`DataVersionManager`)**:
  - Computes a SHA-256 hash of non-metadata fields (`RecordHasher`).
  - Maintains `valid_from`, `valid_to`, and `is_current` flags.
  - When an existing business key arrives with changed values, the old version is expired (`valid_to = NOW(), is_current = FALSE`) and the new record is inserted.
- **Pipeline Checkpointing (`CheckpointManager`)**:
  - Persists JSON state snapshots to `data/staging/checkpoints/` after every stage (`extract`, `raw_storage`, `contract_validation`, `business_transformation`).
  - Allows instant pipeline resumption upon hardware or network failures.

### 4.5 Layered Data Warehouse & Dimensional Star Schema
Logical database separation across **6 dedicated PostgreSQL schemas**:

```
DATABASE: pipeline_warehouse
├── raw          (Landing zone, untouched raw payload)
├── staging      (Temporary tables for surrogate resolution & ETL)
├── warehouse    (Kimball Star Schema: Dimensions & Facts)
├── analytics    (Aggregated reporting views & data marts)
├── metadata     (Lineage events, data versions, pipeline checkpoints)
└── monitoring   (Quality metrics, pipeline performance logs)
```

**Kimball Star Schema Architecture:**
- `warehouse.dim_date`: Pre-generated temporal dimension (`date_key`, `full_date`, `day_name`, `month`, `quarter`, `year`, `is_weekend`).
- `warehouse.dim_customer`: Customer attributes with SCD2 tracking (`customer_key`, `customer_id`, `name`, `segment`, `region`).
- `warehouse.dim_product`: Product catalog dimension (`product_key`, `product_id`, `category`, `subcategory`).
- `warehouse.dim_location`: Geographic dimension (`location_key`, `city`, `state`, `country`, `region`).
- `warehouse.fact_transactions`: Core transactional metrics with resolved integer surrogate keys.
- **Analytical Views (`analytics`)**:
  - `v_daily_sales`: Daily revenue, quantities, and transaction counts.
  - `v_product_performance`: Revenue by category and top-performing products.
  - `v_regional_analysis`: Geographic sales spread and unique customer reach.

### 4.6 Comprehensive Observability & Quality Monitoring
Calculates **The 4 Pillars of Data Quality** per batch:
1. **Freshness Score**: Hours since latest ingestion compared against SLA threshold (e.g., $\le 24$ hours).
2. **Completeness Score**: Percentage of non-null attributes across critical business fields ($\ge 95\%$).
3. **Accuracy Score**: Percentage of records strictly passing all contract validation rules ($\ge 98\%$).
4. **Contract Adherence Score**: Batch-level contract conformity rate ($\ge 99\%$).
- **Alert Manager (`AlertManager`)**: Evaluates SLA breaches and issues `INFO`, `WARNING`, or `CRITICAL` alerts to console, rotating JSON logs, and monitoring tables.

### 4.7 End-to-End Data Lineage & Audit Trails
- Dataclass `LineageEvent` records: `batch_id`, `stage`, `source_system`, `input_count`, `output_count`, `timestamp`, and execution metadata.
- Persisted to PostgreSQL `metadata.lineage_events` and serialized into local audit files.
- Capable of generating full lineage graphs tracing any BI metric back to its exact raw source batch.

### 4.8 FastAPI Control Plane & Monitoring REST API
- Exposes interactive Swagger UI documentation at `http://localhost:8000/docs`.
- Key Endpoints:
  - `GET /health`: System & database connectivity check.
  - `GET /api/v1/pipelines`: List registered pipeline topologies.
  - `POST /api/v1/pipelines/{name}/run`: Programmatically trigger execution with custom parameters.
  - `GET /api/v1/quality/metrics`: Fetch recent quality scorecards across all datasets.
  - `GET /api/v1/lineage/{dataset}`: Retrieve the end-to-end data lineage graph.

### 4.9 Business Intelligence Dashboards (Power BI & Tableau)
Directly connects to PostgreSQL `analytics` and `monitoring` schemas:
- **Executive Summary Page**: KPI metric cards (Total Sales, Order Volume, AOV) + revenue trends.
- **Product Performance Page**: Category breakdown treemap, product performance rankings.
- **Regional Analytics Page**: Geospatial bubble maps, regional customer penetration.
- **Quality & Governance Page**: Live gauge cards displaying Freshness, Completeness, Accuracy, and Quarantine count.

---

## 5. Presentation Code Showcase (Live Demo & Slides)

These complete, standalone code examples can be executed live during a presentation or copied directly into presentation slides.

---

### Demo 1: Running the Complete ETLT++ Pipeline

Demonstrates executing the unified pipeline with raw storage, contract validation, business transformations, and curated Parquet persistence.

```python
"""
DEMO 1: End-to-End ETLT++ Pipeline Execution
Execute via CLI or directly in Python.
"""
from src.pipelines.pipeline_runner import PipelineRunner
import json

def run_etlt_demo():
    print("=" * 60)
    print("DEMO 1: EXECUTING ETLT++ PIPELINE")
    print("=" * 60)

    runner = PipelineRunner()
    
    # Run the ETLT++ pipeline on sample transactions
    result = runner.run(
        pipeline_name="etlt_plus_plus",
        source="csv",
        dataset="transactions",
        contract_version="1.0",
        file_path="tests/fixtures/sample_transactions.csv"
    )

    print("\nExecution Status:", result["status"])
    print("Execution ID    :", result["execution_id"])
    print("Duration        :", f"{result['duration_seconds']}s")
    print("\nExecution Details:")
    print(json.dumps(result["details"], indent=2))

if __name__ == "__main__":
    run_etlt_demo()
```

---

### Demo 2: Contract-Driven Validation & Automated Quarantine

Shows how invalid incoming records are detected by the JSON contract, separated, and routed to quarantine with full diagnostic error metadata.

```python
"""
DEMO 2: Data Contract Validation & Quarantine Engine
Highlights how corrupted records are isolated without breaking the pipeline.
"""
import pandas as pd
from src.contracts.validation_service import ValidationService

def run_contract_validation_demo():
    print("=" * 60)
    print("DEMO 2: DATA CONTRACT VALIDATION & ISOLATION")
    print("=" * 60)

    # 1. Simulate incoming records (mix of valid and intentional errors)
    raw_data = pd.DataFrame([
        {
            "transaction_id": "TXN_001",
            "customer_id": "CUST_101",
            "product_id": "PROD_201",
            "transaction_date": "2026-03-15",
            "quantity": 2,
            "unit_price": 50.0,
            "total_amount": 100.0,
            "location": "New York"
        },
        {
            "transaction_id": "TXN_002_BAD",
            "customer_id": "CUST_102",
            "product_id": "PROD_202",
            "transaction_date": "invalid-date",  # FAILS: Bad date format
            "quantity": -5,                       # FAILS: quantity < 1
            "unit_price": -20.0,                  # FAILS: unit_price < 0
            "total_amount": 100.0,
            "location": "Chicago"
        }
    ])

    print(f"Total Input Records: {len(raw_data)}")

    # 2. Run validation against Transaction Contract v1.0
    validator = ValidationService()
    df_valid, df_invalid, val_result = validator.run_validation(
        df=raw_data,
        dataset_name="transactions",
        contract_version="1.0",
        batch_id="demo_batch_001"
    )

    print(f"\nValidation Result Status: {val_result.status}")
    print(f"  Valid Records Count   : {len(df_valid)}")
    print(f"  Invalid Records Count : {len(df_invalid)}")
    
    # 3. Inspect Error Metadata
    print("\nQuarantined Errors Trace:")
    for err in val_result.errors:
        print(f"  - Row {err.row_index} | Field: '{err.field}' | Offending Value: '{err.value}' | Reason: {err.message}")

if __name__ == "__main__":
    run_contract_validation_demo()
```

---

### Demo 3: Unified Ingestion Factory in Action

Demonstrates the factory pattern abstracting heterogeneous sources (CSV, Excel, API, DB) behind a single unified interface.

```python
"""
DEMO 3: Unified Ingestion Adapter Factory
Shows polymorphic ingestion from CSV and simulated API sources.
"""
from src.ingestion.ingestion_factory import create_ingestion

def run_ingestion_demo():
    print("=" * 60)
    print("DEMO 3: UNIFIED INGESTION FACTORY")
    print("=" * 60)

    # Ingestion 1: CSV Adapter
    csv_adapter = create_ingestion(
        source_type="csv",
        file_path="tests/fixtures/sample_transactions.csv"
    )
    df_csv = csv_adapter.extract()
    print(f"[CSV Ingestion] Extracted {len(df_csv)} records from {csv_adapter.source_name}")

    # Ingestion 2: API Adapter (polymorphic call with identical extract() method)
    # api_adapter = create_ingestion(source_type="api", url="https://api.example.com/transactions")
    # df_api = api_adapter.extract()

    print("Ingestion columns:", list(df_csv.columns[:5]), "...")

if __name__ == "__main__":
    run_ingestion_demo()
```

---

### Demo 4: SCD Type 2 Versioning with SHA-256 Record Hashing

Demonstrates non-destructive data versioning where updates generate new versions rather than overwriting history.

```python
"""
DEMO 4: SCD Type 2 Versioning & Record Hashing
Demonstrates auditability: new records insert, changed records version, unchanged skip.
"""
import pandas as pd
from src.storage.versioning import DataVersionManager, VersionStore

def run_scd2_demo():
    print("=" * 60)
    print("DEMO 4: SCD TYPE 2 DATA VERSIONING")
    print("=" * 60)

    store = VersionStore()
    version_mgr = DataVersionManager(store=store)

    # Batch 1: Initial arrival of customer CUST_001
    batch_1 = pd.DataFrame([{
        "customer_id": "CUST_001",
        "customer_name": "Alice Johnson",
        "segment": "Consumer",
        "region": "East"
    }])

    res1 = version_mgr.apply_versioning(
        df=batch_1,
        dataset_name="customers",
        source_system="crm",
        batch_id="batch_001",
        record_id_column="customer_id"
    )
    print("Batch 1 Result (New Insert):", res1)

    # Batch 2: Alice moves from 'East' to 'West'
    batch_2 = pd.DataFrame([{
        "customer_id": "CUST_001",
        "customer_name": "Alice Johnson",
        "segment": "Consumer",
        "region": "West"  # CHANGED ATTRIBUTE
    }])

    res2 = version_mgr.apply_versioning(
        df=batch_2,
        dataset_name="customers",
        source_system="crm",
        batch_id="batch_002",
        record_id_column="customer_id"
    )
    print("Batch 2 Result (SCD2 Change Detected):", res2)

    # Inspect Version History for CUST_001
    history = store.get_version_history(record_id="CUST_001", dataset_name="customers")
    print(f"\nVersion History for 'CUST_001' ({len(history)} versions found):")
    for v in history:
        print(f"  - Version Hash: {v.record_hash[:10]}... | Is Current: {v.is_current} | Valid From: {v.valid_from} | Valid To: {v.valid_to}")

if __name__ == "__main__":
    run_scd2_demo()
```

---

### Demo 5: Pipeline Observability & Alert Triggering

Demonstrates computing Freshness, Completeness, Accuracy, and Contract Adherence, followed by automated alert evaluation.

```python
"""
DEMO 5: Quality Metrics & Alert Manager
Demonstrates automated quality scorecards and SLA threshold enforcement.
"""
import pandas as pd
from datetime import datetime, timezone
from src.monitoring.quality_metrics import QualityMetricsCalculator
from src.monitoring.alert_manager import AlertManager
from src.contracts.validation_result import ValidationResult

def run_observability_demo():
    print("=" * 60)
    print("DEMO 5: 4-PILLAR DATA QUALITY & ALERTING")
    print("=" * 60)

    # Create dummy DataFrame with 90 valid, 10 nulls
    data = {"transaction_id": [f"T{i}" for i in range(100)], "amount": [10.0 if i < 90 else None for i in range(100)]}
    df = pd.DataFrame(data)

    val_result = ValidationResult(dataset="transactions", batch_id="batch_test", status="PASS")
    calculator = QualityMetricsCalculator()

    metrics = calculator.calculate(
        batch_id="batch_101",
        dataset_name="transactions",
        source="csv",
        df=df,
        validation_result=val_result,
        ingestion_time=datetime.now(timezone.utc),
        duration=1.45,
        pipeline_status="SUCCESS"
    )

    print("Calculated Quality Scorecard:")
    print(f"  Freshness Score          : {metrics.freshness_score}/100")
    print(f"  Completeness Score       : {metrics.completeness_score}%")
    print(f"  Accuracy Score           : {metrics.accuracy_score}%")
    print(f"  Contract Adherence Score : {metrics.contract_adherence_score}%")

    # Evaluate against thresholds in config/settings.yaml
    alert_mgr = AlertManager()
    alerts = alert_mgr.evaluate(metrics)
    print(f"\nAlerts Triggered ({len(alerts)}):")
    for alert in alerts:
        print(f"  [{alert.severity}] {alert.metric_name}: {alert.message}")

if __name__ == "__main__":
    run_observability_demo()
```

---

### Demo 6: Data Lineage Graph Reconstruction

Demonstrates end-to-end lineage tracking capturing transformation steps and row-count deltas at each phase.

```python
"""
DEMO 6: End-to-End Data Lineage Tracking
Reconstructs the origin and transformation journey of a dataset batch.
"""
from src.lineage.lineage_tracker import LineageTracker

def run_lineage_demo():
    print("=" * 60)
    print("DEMO 6: DATA LINEAGE AUDIT TRAIL")
    print("=" * 60)

    tracker = LineageTracker(
        batch_id="exec_998877",
        pipeline_name="etlt_plus_plus",
        dataset_name="transactions",
        source_system="pos_terminal_csv",
        contract_version="1.0"
    )

    # Simulate stage transitions
    tracker.record("extract", input_count=0, output_count=100, metadata={"source_file": "store_12.csv"})
    tracker.record("raw_storage", input_count=100, output_count=100, metadata={"format": "csv"})
    tracker.record("contract_validation", input_count=100, output_count=95, metadata={"quarantined": 5})
    tracker.record("business_transformation", input_count=95, output_count=93, metadata={"dedup_dropped": 2})
    tracker.record("curated_storage", input_count=93, output_count=93, metadata={"format": "parquet"})

    summary = tracker.get_lineage_summary()
    print(f"Pipeline: {summary['pipeline_name']} | Batch: {summary['batch_id']}")
    print(f"Total Stages Recorded: {summary['total_stages']}\n")

    for i, event in enumerate(summary["events"], 1):
        print(f"  Stage {i}: {event['stage'].upper():<25} | In: {event['input_record_count']:<3} ──▶ Out: {event['output_record_count']:<3}")

if __name__ == "__main__":
    run_lineage_demo()
```

---

### Demo 7: Querying Star Schema & Analytical Views

Demonstrates querying the dimensional model for executive KPI generation.

```sql
-- DEMO 7: Analytical Star Schema Queries for BI Dashboards

-- 1. Daily Sales Performance (analytics.v_daily_sales)
SELECT 
    full_date,
    day_name,
    total_sales,
    transaction_count,
    ROUND(total_sales / NULLIF(transaction_count, 0), 2) AS average_order_value
FROM analytics.v_daily_sales
ORDER BY full_date DESC
LIMIT 7;

-- 2. Top Product Categories by Revenue (analytics.v_product_performance)
SELECT 
    category,
    SUM(total_revenue) AS category_revenue,
    SUM(units_sold) AS total_units
FROM analytics.v_product_performance
GROUP BY category
ORDER BY category_revenue DESC;

-- 3. Regional Customer Reach (analytics.v_regional_analysis)
SELECT 
    region,
    city,
    total_sales,
    unique_customers
FROM analytics.v_regional_analysis
ORDER BY total_sales DESC;
```

---

### Demo 8: FastAPI REST API Execution & Health Probing

Demonstrates interacting with the pipeline control plane via HTTP.

```bash
# DEMO 8: FastAPI Control Plane & Endpoints

# 1. Health check
curl -X GET "http://localhost:8000/health"

# 2. List all registered pipeline architectures
curl -X GET "http://localhost:8000/api/v1/pipelines"

# 3. Trigger ETLT++ execution programmatically via REST
curl -X POST "http://localhost:8000/api/v1/pipelines/etlt_plus_plus/run?source=csv&dataset=transactions&contract_version=1.0&file_path=tests/fixtures/sample_transactions.csv"

# 4. Fetch the latest Data Quality Scorecard
curl -X GET "http://localhost:8000/api/v1/quality/metrics"

# 5. Fetch Data Lineage for the 'transactions' dataset
curl -X GET "http://localhost:8000/api/v1/lineage/transactions"
```

---

### Demo 9: Checkpointing & State Recovery

Demonstrates zero data loss and checkpoint persistence during multi-stage execution.

```python
"""
DEMO 9: Pipeline State Checkpointing & Recovery
Demonstrates saving state at every stage and inspecting checkpoints.
"""
from src.storage.checkpoint_manager import CheckpointManager

def run_checkpoint_demo():
    print("=" * 60)
    print("DEMO 9: CHECKPOINTING & RECOVERY MANAGER")
    print("=" * 60)

    mgr = CheckpointManager()
    exec_id = "exec_demo_resilience"

    # Save state across pipeline stages
    mgr.save(exec_id, "etlt_plus_plus", "extract", {"records": 500})
    mgr.save(exec_id, "etlt_plus_plus", "raw_storage", {"records": 500, "path": "data/raw/demo.csv"})
    mgr.save(exec_id, "etlt_plus_plus", "contract_validation", {"valid": 480, "quarantined": 20})

    # Retrieve latest checkpoint to simulate resumption
    latest = mgr.get_latest("etlt_plus_plus")
    print(f"Latest Checkpoint Pipeline : {latest.pipeline_name}")
    print(f"Last Completed Stage       : {latest.last_completed_stage.upper()}")
    print(f"Timestamp                  : {latest.timestamp}")
    print(f"Saved State Snapshot       : {latest.state}")

if __name__ == "__main__":
    run_checkpoint_demo()
```

---

## 6. Slide-by-Slide Presentation Structure & Speaker Notes

Use this structure for a standard 12–15 minute academic or industry evaluation presentation.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        RECOMMENDED PRESENTATION SLIDE OUTLINE                          │
│                                                                                        │
│  Slide 1: Title & Project Identity          Slide 8:  Data Warehouse Star Schema       │
│  Slide 2: Problem Statement & Motivation    Slide 9:  Observability & 4-Pillar Quality │
│  Slide 3: Project Goals & Value Proposition Slide 10: Data Lineage & Checkpointing     │
│  Slide 4: High-Level System Architecture    Slide 11: FastAPI Control Plane & REST API │
│  Slide 5: ETLT++ vs. ELTL++ Paradigms       Slide 12: Power BI & Tableau Dashboards    │
│  Slide 6: Unified Ingestion Factory         Slide 13: Live Demonstration & Code Flow   │
│  Slide 7: Data Contracts & Quarantine Gate  Slide 14: Engineering Metrics & Results    │
│                                             Slide 15: Conclusion & Future Scope        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Slide 1: Title & Team Credentials
- **Visuals**: Project title, department name, batch details, team members, supervisor name.
- **Talking Points**: Introduce the platform as a production-grade, automated data engineering and BI ecosystem that guarantees data governance, contract compliance, and end-to-end auditability.

### Slide 2: Problem Statement & Industry Reality
- **Visuals**: Infographic showing broken downstream dashboards due to schema changes and unmonitored upstream API modifications.
- **Talking Points**: Silent data corruption is common in industry. Data teams spend 80% of their time debugging data quality failures rather than building business intelligence.

### Slide 3: Proposed Solution & Key Objectives
- **Visuals**: Pillar diagram: Multi-Source Ingestion, Contract Enforcement, Flexible Architecture (ETLT++/ELTL++), Star Schema Warehouse, Full Observability, BI Integration.
- **Talking Points**: We built an automated, contract-governed platform with automated quarantine, SCD Type 2 history, and observability.

### Slide 4: System Architecture
- **Visuals**: Full architecture diagram from `docs/architecture/system_architecture.md`.
- **Talking Points**: Walk through the layered design: Sources $\rightarrow$ Ingestion $\rightarrow$ Contracts $\rightarrow$ Transformation $\rightarrow$ Storage $\rightarrow$ Semantic Layer $\rightarrow$ BI. Emphasize the cross-cutting concerns (observability, lineage, governance).

### Slide 5: Architectural Paradigms: ETLT++ and ELTL++
- **Visuals**: Side-by-side flow comparison between ETLT++ and ELTL++.
- **Talking Points**:
  - *ETLT++*: Extract $\rightarrow$ Raw $\rightarrow$ Contract Validate (T1) $\rightarrow$ Business Transform (T2) $\rightarrow$ Curated Parquet. Focuses on compliance and clean storage.
  - *ELTL++*: Extract $\rightarrow$ Immutable Raw Lake $\rightarrow$ Managed Raw $\rightarrow$ Transform $\rightarrow$ Curated Semantic. Optimized for large-scale data lakes with full replayability.

### Slide 6: Ingestion Layer & Factory Pattern
- **Visuals**: UML diagram of `BaseIngestion` and adapters (`CSVIngestion`, `ExcelIngestion`, `APIIngestion`, `DatabaseIngestion`).
- **Talking Points**: Highlights polymorphic design. Any source can be swapped in without modifying downstream transformation or storage code.

### Slide 7: Data Contracts & Automated Quarantine
- **Visuals**: Sample contract JSON snippet next to the quarantine directory structure with error metadata.
- **Talking Points**: Contracts act as legally binding SLAs between producers and consumers. Bad records are isolated into quarantine with exact line-level error logs; clean records flow through uninterrupted.

### Slide 8: Dimensional Modeling & Star Schema
- **Visuals**: Star Schema ER Diagram (`dim_date`, `dim_customer`, `dim_product`, `dim_location` joined to `fact_transactions`).
- **Talking Points**: Adheres to Ralph Kimball's dimensional modeling principles. Uses surrogate integer keys for fast analytical joins and optimized BI query response times.

### Slide 9: Observability & The 4 Pillars of Data Quality
- **Visuals**: Dashboard cards showing Freshness, Completeness, Accuracy, and Contract Adherence scores.
- **Talking Points**: Continuous quality auditing per batch. Automatic alert evaluation (`INFO`, `WARNING`, `CRITICAL`) when metric thresholds fall below configured SLAs.

### Slide 10: Traceability: Lineage & Checkpointing
- **Visuals**: Lineage DAG diagram and Checkpoint JSON schema.
- **Talking Points**: Lineage answers "Where did this metric come from?" Checkpointing ensures zero data loss by enabling the pipeline to resume from the exact failed stage.

### Slide 11: Control Plane & FastAPI REST API
- **Visuals**: Screenshot of Swagger UI (`/docs`) showing `/pipelines`, `/quality`, `/lineage` endpoints.
- **Talking Points**: Exposes pipeline operations to microservices, DevOps orchestration tools, and automated triggers.

### Slide 12: Business Intelligence Layer (Power BI & Tableau)
- **Visuals**: Screenshots of the 5 Power BI pages (Executive, Product, Regional, Quality, Pipeline) and Tableau sheets.
- **Talking Points**: Direct connection to curated views (`analytics` schema). Executive decision-makers receive real-time, validated metrics with interactive slicers.

### Slide 13: Live Demonstration
- **Action**: Execute `scripts/run_pipeline.py` or trigger via FastAPI. Show the generated Parquet file, the quarantine directory for malformed data, and the live lineage trace.

### Slide 14: Engineering Highlights & Test Coverage
- **Visuals**: Summary table of test suites: 11 unit test files, 7 integration test files, 100% pass rate.
- **Talking Points**: Emphasize robust software engineering practices: Docker containerization, comprehensive pytest suites, modular directory structure.

### Slide 15: Conclusion & Future Enhancements
- **Talking Points**: Summarize achievements. Highlight future extensions: Kubernetes deployment, distributed Apache Spark execution for petabyte-scale data, and streaming ingestion via Apache Kafka.

---

## 7. Technology Stack & Architectural Evaluation Summary

| Tier / Function | Technologies Employed | Architectural Rationale |
|---|---|---|
| **Programming Language** | Python 3.10+ | Industry standard for data engineering, rich library ecosystem |
| **Data Processing** | pandas, NumPy, openpyxl | Vectorized transformations, high-performance data manipulation |
| **Data Serialization** | Apache Parquet (via pyarrow) | Columnar storage, high compression ratio, fast analytical reads |
| **Data Warehouse** | PostgreSQL 16 (Snowflake ready) | Robust schema separation, ACID compliance, relational joins |
| **Database ORM & Driver** | SQLAlchemy 2.0, psycopg2-binary | Safe connection pooling, parameterized query execution |
| **Validation & Governance** | JSON Schema, Custom Contract Engine | Language-agnostic, version-controlled quality enforcement |
| **API Control Plane** | FastAPI, Pydantic v2, Uvicorn | Asynchronous execution, automatic OpenAPI Swagger docs |
| **Observability & Logging** | Python `logging`, JSON log rotation | Multi-destination audit trails (file, console, DB tables) |
| **Business Intelligence** | Power BI Desktop, Tableau | Self-service visual analytics, DAX measures, executive reporting |
| **Infrastructure & CI** | Docker, Docker Compose, GitHub Actions | Reproducible isolated development environment, automated CI |
| **Testing Framework** | pytest, pytest-cov | 18+ comprehensive unit and end-to-end integration test suites |

---
*Created for Major Project Batch 19 — Automated End-to-End Data Pipeline & BI Architecture.*
