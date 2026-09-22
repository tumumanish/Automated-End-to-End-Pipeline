# Design and Implementation of an Automated End-to-End Data Pipeline and Business Intelligence Architecture

> **B.Tech CSE (Data Science) — Major Project**

---

## 1. Project Overview

This project implements an automated end-to-end data engineering and Business Intelligence platform. It demonstrates a production-grade architecture for ingesting, validating, transforming, storing, and visualizing data using industry-standard tools and best practices.

The system supports multiple pipeline patterns (ETLT++ and ELTL++), enforces data contracts, maintains full data lineage, and delivers curated analytical datasets to Business Intelligence tools.

---

## 2. Problem Statement

Organizations face significant challenges in managing data across heterogeneous sources, ensuring data quality, maintaining governance and lineage, and delivering reliable analytical datasets for decision-making. Manual, ad-hoc data processing leads to inconsistent results, poor data quality, and lack of auditability.

This project addresses these challenges by designing and implementing an automated, contract-driven data pipeline architecture with built-in quality monitoring, versioning, and lineage tracking.

---

## 3. Objectives

1. Design a layered data pipeline architecture supporting ETLT++ and ELTL++ patterns.
2. Implement automated data ingestion from REST APIs, CSV, Excel, and relational databases.
   - Modular ingestion adapters (CSV, Excel, API, SQL)
   - Raw storage layer for immutable source tracking
   - Detailed ingestion batch logging
3. Enforce data quality through schema validation, data contracts, and business-rule validation.
   - **Phase 3:** Data Contracts & Schema Validation
     - JSON-based versioned data contracts
     - Structural schema validation (missing/unexpected columns)
     - Row-level validation (types, nullability, ranges, allowed values, formats)
     - Validation error reporting and invalid record quarantine with detailed JSON metadata traces
4. Execute End-to-End Orchestration via the **ETLT++** Architecture Pattern.
   - **Phase 4:** Pipeline orchestration and T2 Transformation Layer
     - Unified `PipelineRunner` and dynamic `PipelineRegistry`
     - Clean separation of T1 (Contract) and T2 (Business) logic
     - Business logic: data cleaning, normalizations, deduplication, and field derivations
     - Curated analytical storage zone in Parquet format
5. Implement data versioning, lineage tracking, and checkpoint-based recovery.
6. Deliver curated analytical datasets for Power BI and Tableau dashboards.
7. Provide pipeline monitoring with freshness, completeness, accuracy, and contract adherence metrics.
8. Maintain quarantine and error-handling mechanisms for invalid records.

---

## 4. System Architecture

The system follows a clean layered architecture:

```
DATA SOURCES (APIs, CSV, Excel, Databases)
        │
        ▼
INGESTION LAYER (Extract & Load)
        │
        ▼
DATA QUALITY / CONTRACT LAYER (Validate & Quarantine)
        │
        ▼
TRANSFORMATION LAYER (Clean, Normalize, Enrich)
        │
        ▼
STORAGE / DATA WAREHOUSE (PostgreSQL / Snowflake)
        │
        ▼
SEMANTIC / ANALYTICAL LAYER (Dimensions, Facts, Marts)
        │
        ▼
BI / REPORTING LAYER (Power BI, Tableau)
```

**Cross-cutting concerns:**
- Observability & Monitoring
- Data Governance & Contracts
- Data Lineage & Metadata
- Error Handling & Quarantine

---

## 5. Data Sources

The platform supports ingestion from:

| Source Type       | Description                          |
|-------------------|--------------------------------------|
| REST APIs         | Public/private HTTP endpoints        |
| CSV Files         | Comma-separated value files          |
| Excel Files       | `.xlsx` workbooks via `openpyxl`     |
| Relational DBs    | PostgreSQL and other RDBMS via SQLAlchemy |

---

## 6. ETLT++ Pipeline

**Extract → Contract → Validate/Clean → Versioned Raw Storage → Business Transform → Curated Output → BI**

Key capabilities:
- Contract-first validation before storage
- Record-level and batch-level validation
- Invalid record quarantine
- Versioned raw data preservation
- Business rule transformations
- Curated analytical output generation

See: [`docs/architecture/etlt_architecture.md`](docs/architecture/etlt_architecture.md)

---

## 7. ELTL++ Pipeline

**Extract → Raw Load (Immutable) → Managed Raw Layer → Transform → Curated Semantic Layer → BI**

Key capabilities:
- Raw data preservation in immutable zone
- Metadata-driven ingestion
- Retention policy support
- Dimensional modeling in semantic layer
- Standardized KPI definitions

See: [`docs/architecture/eltl_architecture.md`](docs/architecture/eltl_architecture.md)

---

## 8. Data Quality

The system monitors four major quality indicators:

| Indicator            | Description                                    |
|-----------------------|------------------------------------------------|
| **Freshness**         | How recent is the data?                        |
| **Completeness**      | Are all expected fields and records present?   |
| **Accuracy**          | Do values conform to expected ranges/formats?  |
| **Contract Adherence**| Does data satisfy registered contracts?        |

Quality metrics are recorded per batch with full audit trails.

---

## 9. Data Contracts

Data contracts are JSON-based schema definitions that specify:
- Required fields and data types
- Nullable/non-nullable constraints
- Value ranges (min/max)
- Allowed values (enums)
- Format patterns
- Hard rules (reject on violation) and soft rules (warn on violation)

Contracts are versioned and stored in `contracts/versions/`.

---

## 10. Data Versioning

The system supports append-only, versioned storage with metadata:
- `record_id`, `source_system`, `batch_id`
- `ingestion_timestamp`, `valid_from`, `valid_to`
- `record_hash`, `schema_version`

---

## 11. Data Lineage

The lineage subsystem tracks:
- Dataset origin and source system
- Pipeline and transformations applied
- Contract version used
- Batch identifiers
- Final destination tables

---

## 12. Data Warehouse

The warehouse uses dimensional modeling with star schema:

- **Dimensions:** `dim_date`, `dim_customer`, `dim_product`, `dim_location`
- **Facts:** `fact_transactions`
- **Staging:** Intermediate processing tables
- **Marts:** Business-specific analytical views

---

## 13. Business Intelligence

| Tool       | Purpose                                   |
|------------|-------------------------------------------|
| Power BI   | Interactive dashboards and reports        |
| Tableau    | Advanced analytics and visualizations     |

BI tools consume curated analytical datasets from the semantic layer — not raw tables.

---

## 14. Technology Stack

| Layer               | Technology                                |
|---------------------|-------------------------------------------|
| Language            | Python 3.10+                              |
| Data Processing     | Pandas, SQL                               |
| Validation          | Pydantic, custom validators               |
| Database (Local)    | PostgreSQL                                |
| Database (Cloud)    | Snowflake (optional)                      |
| ORM / DB Access     | SQLAlchemy, psycopg2                      |
| API Framework       | FastAPI                                   |
| Configuration       | PyYAML, python-dotenv                     |
| File Processing     | openpyxl                                  |
| Containerization    | Docker, Docker Compose                    |
| Testing             | pytest                                    |
| BI                  | Power BI, Tableau                         |

---

## 15. Project Structure

```
automated-data-pipeline-bi/
├── config/          — Configuration files (settings, logging, pipeline, environments)
├── contracts/       — Data contract schemas and versioned contracts
├── data/            — Data zones (raw, quarantine, staging, processed, curated, archive)
├── src/             — Source code (ingestion, contracts, transformation, pipelines, etc.)
├── sql/             — SQL scripts for PostgreSQL and Snowflake
├── orchestration/   — Pipeline jobs and scheduling
├── api/             — REST API for pipeline monitoring
├── dashboard/       — BI documentation (Power BI, Tableau)
├── tests/           — Unit, integration, and fixture tests
├── scripts/         — Utility scripts (setup, run, validate)
├── logs/            — Pipeline, validation, lineage, and error logs
├── notebooks/       — Jupyter notebooks for exploration and analysis
├── docs/            — Architecture, database, pipeline, and project documentation
└── infrastructure/  — Docker and infrastructure scripts
```

---

## 16. Local Setup

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- Git

### Steps

```bash
# 1. Clone the repository
git clone <repository-url>
cd automated-data-pipeline-bi

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your local settings

# 5. Start PostgreSQL
docker-compose up -d

# 6. Initialize database
python scripts/setup_database.py

# 7. Validate environment
python scripts/validate_environment.py
```

---

## 17. Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable              | Description                      |
|-----------------------|----------------------------------|
| `POSTGRES_HOST`       | PostgreSQL host                  |
| `POSTGRES_PORT`       | PostgreSQL port                  |
| `POSTGRES_DB`         | PostgreSQL database name         |
| `POSTGRES_USER`       | PostgreSQL username              |
| `POSTGRES_PASSWORD`   | PostgreSQL password              |
| `SNOWFLAKE_ACCOUNT`   | Snowflake account identifier     |
| `SNOWFLAKE_USER`      | Snowflake username               |
| `SNOWFLAKE_PASSWORD`  | Snowflake password               |
| `SNOWFLAKE_DATABASE`  | Snowflake database               |
| `SNOWFLAKE_SCHEMA`    | Snowflake schema                 |
| `SNOWFLAKE_WAREHOUSE` | Snowflake warehouse              |
| `API_BASE_URL`        | Base URL for external API sources|

> ⚠️ **Never commit `.env` to version control.**

---

## 18. Running the Pipeline

```bash
# Run the pipeline manually
python scripts/run_pipeline.py

# Run via orchestration
python orchestration/jobs/manual_pipeline.py

# Start the monitoring API
uvicorn api.main:app --reload
```

---

## 19. Testing

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=src tests/
```

---

## 20. Future Enhancements

- [ ] Real-time streaming ingestion
- [ ] Apache Airflow orchestration
- [ ] Advanced anomaly detection in data quality
- [ ] Machine learning feature store integration
- [ ] Automated data catalog generation
- [ ] Role-based access control for API
- [ ] CI/CD pipeline for automated testing and deployment
- [ ] Data masking and PII handling
- [ ] Multi-tenant support
- [ ] Cost monitoring for Snowflake queries

---

## License

This project is developed as part of a B.Tech CSE (Data Science) Major Project.

See [LICENSE](LICENSE) for details.

---

## Author

B.Tech CSE (Data Science) — Final Year Major Project
