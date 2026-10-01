# End-to-End Project Usage Guide & Operations Manual

> **Project Title:** Design and Implementation of an Automated End-to-End Data Pipeline and Business Intelligence Architecture  
> **Course / Degree:** B.Tech CSE (Data Science) — Final Year Major Project  
> **Status:** Production-Ready (Phases 1–11 Fully Implemented & Tested)

---

## Table of Contents

1. [Project Overview & Key Capabilities](#1-project-overview--key-capabilities)
2. [Prerequisites & System Requirements](#2-prerequisites--system-requirements)
3. [Required Software, Tools & Technologies](#3-required-software-tools--technologies)
4. [Datasets & Data Contracts](#4-datasets--data-contracts)
   - [Domain: Retail Transactions](#domain-retail-transactions)
   - [Data Contract Specifications (v1.0)](#data-contract-specifications-v10)
   - [Supported Source Formats](#supported-source-formats)
   - [Generating & Accessing Datasets](#generating--accessing-datasets)
   - [Storage Architecture (Data Lakehouse Zones)](#storage-architecture-data-lakehouse-zones)
5. [End-to-End Step-by-Step Usage Guide](#5-end-to-end-step-by-step-usage-guide)
   - [Step 1: Clone Repository & Open Terminal](#step-1-clone-repository--open-terminal)
   - [Step 2: Create & Activate Virtual Environment](#step-2-create--activate-virtual-environment)
   - [Step 3: Install Required Dependencies](#step-3-install-required-dependencies)
   - [Step 4: Configure Environment Variables (.env)](#step-4-configure-environment-variables-env)
   - [Step 5: Start the PostgreSQL Database](#step-5-start-the-postgresql-database)
   - [Step 6: Initialize Schemas, Tables & Views](#step-6-initialize-schemas-tables--views)
   - [Step 7: Validate Environment Setup](#step-7-validate-environment-setup)
   - [Step 8: Generate Sample Data](#step-8-generate-sample-data)
   - [Step 9: Execute Data Pipelines](#step-9-execute-data-pipelines)
   - [Step 10: Load Curated Data into the Warehouse](#step-10-load-curated-data-into-the-warehouse)
   - [Step 11: Launch the FastAPI Monitoring Server](#step-11-launch-the-fastapi-monitoring-server)
   - [Step 12: Run Automated Tests & Verify Quality](#step-12-run-automated-tests--verify-quality)
   - [Step 13: Connect Business Intelligence Dashboards](#step-13-connect-business-intelligence-dashboards)
6. [Master Command Cheat Sheet](#6-master-command-cheat-sheet)
   - [Setup & Environment Commands](#setup--environment-commands)
   - [Database & Migration Commands](#database--migration-commands)
   - [Data Generation Commands](#data-generation-commands)
   - [Pipeline Execution Commands](#pipeline-execution-commands)
   - [Warehouse Loading Commands](#warehouse-loading-commands)
   - [API Server & Curl Endpoint Commands](#api-server--curl-endpoint-commands)
   - [Testing & Quality Assurance Commands](#testing--quality-assurance-commands)
   - [Docker & Container Commands](#docker--container-commands)
   - [Makefile Shortcuts](#makefile-shortcuts)
7. [Architecture & Pipeline Workflows](#7-architecture--pipeline-workflows)
   - [Pipeline Architectures (ETLT++, ELTL++, ETLT, ELTL)](#pipeline-architectures)
   - [Star Schema & Semantic Analytical Views](#star-schema--semantic-analytical-views)
8. [Troubleshooting & Frequently Asked Questions](#8-troubleshooting--frequently-asked-questions)

---

## 1. Project Overview & Key Capabilities

This repository contains a modular, contract-driven, automated data engineering and analytics platform. It bridges raw data ingestion across heterogeneous formats with a dimensional data warehouse and interactive Business Intelligence dashboards.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                    │
│       REST API (JSON)  │  CSV Files  │  Excel (.xlsx)  │  RDBMS        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   INGESTION & DATA CONTRACT LAYER                      │
│       - Format Adapters (API, CSV, Excel, SQL)                         │
│       - Schema Contract Enforcement (v1.0 JSON Schema)                 │
│       - Data Quality Gate: Freshness, Completeness, Accuracy           │
│       - Dead-Letter Queue (DLQ) Quarantine for Malformed Records       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  TRANSFORMATION & STORAGE LAYER                        │
│       - Pipeline Runner (ETLT++, ELTL++, ETLT, ELTL)                   │
│       - Business Logic: Clean, Normalize, Enrich, Deduplicate          │
│       - Lakehouse Storage Zones: Raw, Staging, Processed, Curated      │
│       - Checkpoint-based Failure Recovery & Audit Lineage              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                ENTERPRISE DATA WAREHOUSE & ANALYTICS                   │
│       - PostgreSQL 16 (Schemas: raw, staging, warehouse, analytics)    │
│       - Star Schema: dim_customer, dim_product, dim_location, dim_date │
│       - Fact Table: fact_transactions                                  │
│       - Analytical Views: v_daily_sales, v_product_performance, etc.   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 CONSUMPTION & OBSERVABILITY LAYER                      │
│       - FastAPI REST Service (Health, Runs, Metrics, Lineage)          │
│       - Power BI Desktop & Tableau Dashboards                          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites & System Requirements

### Hardware Requirements
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | Dual-core 2.0 GHz | Quad-core 2.5 GHz+ (Intel i5/i7, AMD Ryzen, Apple Silicon) |
| **RAM** | 4 GB | 8 GB or 16 GB |
| **Disk Space** | 2 GB free space | 10 GB free space (accommodates Docker images & local Parquet files) |
| **Operating System** | Windows 10/11, macOS 12+, or Ubuntu 20.04+ LTS | Windows 11 (PowerShell) or Linux (bash) |

---

## 3. Required Software, Tools & Technologies

### 1. Core Runtimes & Infrastructure
* **Python 3.10 to 3.13:** The runtime environment for ingestion, transformation, pipelines, API, and tests.
* **PostgreSQL 16+:** The local relational analytical data warehouse engine.
* **Docker Desktop & Docker Compose (Recommended):** Provides containerized PostgreSQL without requiring manual local database installation.
* **Git:** For cloning and version control.

### 2. Python Dependencies (`requirements.txt`)
All Python dependencies are pinned to compatible modern versions:

```
# Core Data Processing
pandas>=2.0.0
numpy>=1.24.0

# File Formats & Ingestion
openpyxl>=3.1.0          # Excel (.xlsx) support
requests>=2.31.0          # HTTP API client
python-dateutil>=2.8.0    # ISO date parsing

# Relational Database & ORM
sqlalchemy>=2.0.0         # Modern SQL toolkit & ORM
psycopg2-binary>=2.9.0    # PostgreSQL native binary adapter

# Environment & Configuration
python-dotenv>=1.0.0      # .env configuration management
pyyaml>=6.0.0             # YAML parser for settings.yaml & pipeline.yaml

# Data Validation & Contracts
pydantic>=2.0.0           # Strict data validation models

# REST API & Web Server
fastapi>=0.100.0          # High-performance async REST framework
uvicorn>=0.23.0           # ASGI production server

# Testing & Code Coverage
pytest>=7.4.0             # Unit & integration testing engine
pytest-cov>=4.1.0         # Test coverage reporting

# Optional (Cloud Analytical Warehouse)
# snowflake-connector-python>=3.0.0
# snowflake-sqlalchemy>=1.5.0
```

### 3. Business Intelligence & Database Clients
* **Microsoft Power BI Desktop:** Free download from Microsoft Store or official website.
* **Tableau Desktop / Tableau Public:** For interactive visual analytics.
* **Database Inspection Client (Optional):** DBeaver Community, pgAdmin 4, or VS Code PostgreSQL extension.

---

## 4. Datasets & Data Contracts

### Domain: Retail Transactions
The platform is centered on a retail transaction domain capturing customer purchases, order details, locations, and monetary values.

### Data Contract Specifications (v1.0)
Contract location: `contracts/schemas/transaction_contract.json` (version `1.0`).

| Field Name | Type | Required | Nullable | Constraints & Description | Example Value |
|------------|------|----------|----------|---------------------------|---------------|
| `transaction_id` | string | Yes | No | Unique transaction code (`TXN-YYYYMMDD-XXXXX`) | `TXN-20240415-00102` |
| `customer_id` | string | Yes | No | Customer reference identifier | `CUST-1420` |
| `product_id` | string | Yes | No | Catalog SKU identifier | `PROD-001` |
| `transaction_date`| date | Yes | No | ISO 8601 formatted date (`YYYY-MM-DD`) | `2024-04-15` |
| `quantity` | integer| Yes | No | Number of units purchased (minimum: 1) | `3` |
| `unit_price` | number | Yes | No | Price per single unit (minimum: 0.00) | `45000.00` |
| `total_amount` | number | Yes | No | Calculated line total (minimum: 0.00) | `135000.00` |
| `location` | string | Yes | No | Fulfillment location / city | `Bangalore` |

### Supported Source Formats
1. **CSV Files (`.csv`):** Delimited comma-separated values, UTF-8 encoded.
2. **Excel Spreadsheets (`.xlsx`):** Multi-sheet workbooks read via `openpyxl`.
3. **REST API JSON:** Live JSON payloads containing list of transaction objects.
4. **Relational Database Tables:** Relational source tables ingested via SQLAlchemy queries.

### Generating & Accessing Datasets
You have multiple ways to access and generate datasets:

1. **Pre-Built Test Fixtures (Included in Repo):**
   - `tests/fixtures/sample_transactions.csv` (250 valid records)
   - `tests/fixtures/sample_transactions.xlsx` (250 valid records in Excel sheet)
   - `tests/fixtures/invalid_transactions.csv` (contains missing fields, negative prices, null IDs for quarantine testing)
   - `tests/fixtures/invalid_data.csv` (violates schema contract for DLQ testing)

2. **Synthetic Data Generator Script:**
   Generate custom volumes of realistic synthetic transaction records:
   ```bash
   # Generates 250 records (default) to tests/fixtures/sample_transactions.{csv,xlsx}
   python scripts/generate_sample_data.py

   # Generates 1,000 custom records
   python scripts/generate_sample_data.py --records 1000
   ```

3. **Live Mock API Endpoint:**
   When the FastAPI server is running, synthetic transaction records are served dynamically:
   ```
   GET http://localhost:8000/api/v1/sample/transactions?limit=100
   ```

### Storage Architecture (Data Lakehouse Zones)
All batch artifacts are preserved in directory zones under `data/`:
* `data/raw/`: Immutable source copies timestamped per batch execution.
* `data/staging/`: Temporary working payloads.
* `data/processed/`: Contract-compliant validated JSON/CSV records.
* `data/curated/`: Transformed, enriched, and partitioned Parquet datasets ready for BI.
* `data/quarantine/`: Quarantined invalid records with detailed JSON error traces for triage.
* `data/archive/`: Long-term compressed cold storage for historical runs.

---

## 5. End-to-End Step-by-Step Usage Guide

Follow these 13 steps to set up, operate, and analyze data in the project:

### Step 1: Clone Repository & Open Terminal
Open PowerShell (Windows) or Terminal (macOS/Linux) in your project directory:
```powershell
cd d:\Major_Project_batch19\Automated-End-to-End-Pipeline
```

### Step 2: Create & Activate Virtual Environment
Isolate Python dependencies using a virtual environment:

* **On Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
  *(If execution policies block script activation in PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

* **On Linux / macOS (bash):**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### Step 3: Install Required Dependencies
Install all core libraries:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables (`.env`)
Copy the provided `.env.example` template to `.env`:

* **On Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```
* **On Linux / macOS:**
  ```bash
  cp .env.example .env
  ```

Open `.env` and verify your local settings:
```ini
APP_ENV=development
APP_DEBUG=true
APP_LOG_LEVEL=INFO

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=pipeline_warehouse
POSTGRES_USER=pipeline_user
POSTGRES_PASSWORD=pipeline_password
```

### Step 5: Start the PostgreSQL Database

#### Option A: Using Docker Compose (Recommended - Zero Installation)
If Docker Desktop is running, launch containerized PostgreSQL:
```bash
docker-compose up -d
```
Verify container status:
```bash
docker-compose ps
```

#### Option B: Using a Locally Installed PostgreSQL
If running a native PostgreSQL service on Windows/Linux:
1. Ensure the PostgreSQL service is started (port 5432).
2. Create the database `pipeline_warehouse` and user `pipeline_user` (or set `.env` to your `postgres` superuser credentials).

### Step 6: Initialize Schemas, Tables & Views
Execute the database setup script to apply all idempotent DDL migrations:
```bash
python scripts/setup_database.py
```
This automatically applies:
- `01_create_schemas.sql` (`raw`, `staging`, `warehouse`, `analytics`, `metadata`, `monitoring`)
- `02_create_raw_tables.sql`
- `03_create_validation_tables.sql` & `03_create_staging_tables.sql`
- `04_create_dimensions.sql` (`dim_customer`, `dim_product`, `dim_location`, `dim_date`)
- `05_create_facts.sql` (`fact_transactions`)
- `06_create_views.sql` (Analytical business marts)
- `07_create_monitoring_tables.sql` (`pipeline_metrics`, `batch_quality_metrics`, `alert_log`)
- `08_create_lineage_tables.sql` (`data_lineage`, `lineage_events`)

### Step 7: Validate Environment Setup
Run the environment health check script to verify Python version, libraries, directories, `.env`, and database connectivity:
```bash
python scripts/validate_environment.py
```
You should see all green checkmarks (`PASS`) for Python, Dependencies, Directories, and Database.

### Step 8: Generate Sample Data
Generate synthetic retail transaction datasets:
```bash
python scripts/generate_sample_data.py --records 500
```
This produces:
- `tests/fixtures/sample_transactions.csv` (500 records)
- `tests/fixtures/sample_transactions.xlsx` (500 records in Excel)

### Step 9: Execute Data Pipelines
Run any of the 4 pipeline architectures across different data sources:

#### A. Run ETLT++ Pipeline with CSV Source:
```bash
python scripts/run_pipeline.py --pipeline etlt_plus_plus --source csv --file tests/fixtures/sample_transactions.csv
```

#### B. Run ETLT++ Pipeline with Excel Source:
```bash
python scripts/run_pipeline.py --pipeline etlt_plus_plus --source excel --file tests/fixtures/sample_transactions.xlsx
```

#### C. Run ELTL++ Pipeline (Extract -> Raw Load -> Managed Raw -> Transform -> Curated):
```bash
python scripts/run_pipeline.py --pipeline eltl_plus_plus --source csv --file tests/fixtures/sample_transactions.csv
```

#### D. Run with the Orchestration Runner (Dry-Run Mode):
```bash
python orchestration/jobs/manual_pipeline.py --pipeline etlt_plus_plus --source csv --file tests/fixtures/sample_transactions.csv --dry-run
```

#### E. Run Pipeline and Immediately Auto-Load Warehouse:
```bash
python orchestration/jobs/manual_pipeline.py --pipeline etlt_plus_plus --source csv --file tests/fixtures/sample_transactions.csv --load-warehouse
```

### Step 10: Load Curated Data into the Warehouse
To load all curated data into the star schema dimensions and fact table, and refresh analytical views:
```bash
python scripts/load_warehouse.py
```
You will see output confirming:
- Dimensions loaded (`dim_customer`, `dim_product`, `dim_location`, `dim_date`)
- Facts loaded (`fact_transactions`)
- Analytical views refreshed in the `analytics` schema.

### Step 11: Launch the FastAPI Monitoring Server
Start the monitoring and data service:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
Now access these URLs in your web browser:
* **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc API Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **API Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
* **Sample Transactions Feed:** [http://localhost:8000/api/v1/sample/transactions?limit=25](http://localhost:8000/api/v1/sample/transactions?limit=25)
* **Pipeline Executions History:** [http://localhost:8000/api/v1/pipelines/executions/recent](http://localhost:8000/api/v1/pipelines/executions/recent)
* **Data Quality Metrics:** [http://localhost:8000/api/v1/quality/metrics](http://localhost:8000/api/v1/quality/metrics)
* **Data Lineage Batches:** [http://localhost:8000/api/v1/lineage/batches](http://localhost:8000/api/v1/lineage/batches)

### Step 12: Run Automated Tests & Verify Quality
Verify all unit and integration tests across the 11 phases:

```bash
# Run the complete test suite
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v

# Generate HTML test coverage report
pytest tests/ --cov=src --cov-report=html
```
*(Open `htmlcov/index.html` in your browser to inspect test coverage across all modules).*

### Step 13: Connect Business Intelligence Dashboards
Connect Power BI Desktop or Tableau Desktop to PostgreSQL:

1. **Connection Parameters:**
   - **Server / Host:** `localhost`
   - **Port:** `5432`
   - **Database:** `pipeline_warehouse`
   - **User:** `pipeline_user` (or your `.env` username)
   - **Password:** `pipeline_password` (or your `.env` password)
   - **Data Connectivity Mode:** Import or DirectQuery

2. **Select Analytical Views from `analytics` Schema:**
   - `analytics.v_daily_sales` — Daily trends, total orders, revenue
   - `analytics.v_product_performance` — Product-level volume, sales, average order value
   - `analytics.v_regional_analysis` — Geographic revenue distribution
   - `analytics.v_customer_segments` — Customer loyalty, recency, frequency, monetary value
   - `analytics.v_transaction_detail` — Fully denormalized transaction level view

3. **Select Monitoring Tables for Data Quality Dashboards:**
   - `monitoring.batch_quality_metrics` — Completeness, accuracy, adherence rates
   - `monitoring.pipeline_metrics` — Run durations, execution statuses

---

## 6. Master Command Cheat Sheet

### Setup & Environment Commands

| Action | Windows (PowerShell) | Linux / macOS (bash) |
|--------|----------------------|----------------------|
| **Create Virtualenv** | `python -m venv .venv` | `python3 -m venv .venv` |
| **Activate Virtualenv** | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |
| **Install Dependencies** | `pip install -r requirements.txt` | `pip install -r requirements.txt` |
| **Create .env File** | `Copy-Item .env.example .env` | `cp .env.example .env` |
| **Validate Setup** | `python scripts/validate_environment.py` | `python scripts/validate_environment.py` |

### Database & Migration Commands

| Action | Command |
|--------|---------|
| **Start Docker DB** | `docker-compose up -d` |
| **Stop Docker DB** | `docker-compose down` |
| **View DB Logs** | `docker-compose logs -f postgres` |
| **Initialize All Schemas & Tables** | `python scripts/setup_database.py` |
| **Connect via psql (Docker)** | `docker exec -it pipeline_postgres psql -U pipeline_user -d pipeline_warehouse` |

### Data Generation Commands

| Action | Command |
|--------|---------|
| **Generate Default 250 Records** | `python scripts/generate_sample_data.py` |
| **Generate 1,000 Records** | `python scripts/generate_sample_data.py --records 1000` |
| **Generate 5,000 Records** | `python scripts/generate_sample_data.py --records 5000` |

### Pipeline Execution Commands

```bash
# 1. Run ETLT++ pipeline with CSV file
python scripts/run_pipeline.py --pipeline etlt_plus_plus --source csv --file tests/fixtures/sample_transactions.csv

# 2. Run ETLT++ pipeline with Excel file
python scripts/run_pipeline.py --pipeline etlt_plus_plus --source excel --file tests/fixtures/sample_transactions.xlsx

# 3. Run ELTL++ pipeline with CSV file
python scripts/run_pipeline.py --pipeline eltl_plus_plus --source csv --file tests/fixtures/sample_transactions.csv

# 4. Run basic ETLT pipeline
python scripts/run_pipeline.py --pipeline etlt --source csv --file tests/fixtures/sample_transactions.csv

# 5. Run basic ELTL pipeline
python scripts/run_pipeline.py --pipeline eltl --source csv --file tests/fixtures/sample_transactions.csv

# 6. Manual orchestrator with dry-run
python orchestration/jobs/manual_pipeline.py --pipeline etlt_plus_plus --source csv --file tests/fixtures/sample_transactions.csv --dry-run

# 7. Manual orchestrator with automated warehouse loading
python orchestration/jobs/manual_pipeline.py --pipeline etlt_plus_plus --source csv --file tests/fixtures/sample_transactions.csv --load-warehouse
```

### Warehouse Loading Commands

```bash
# Load all available curated data into warehouse star schema & refresh views
python scripts/load_warehouse.py

# Load specific batch execution into warehouse
python scripts/load_warehouse.py --dataset transactions --batch-id exec_abc123456789
```

### API Server & Curl Endpoint Commands

```bash
# Start API Server with hot reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Health check
curl http://localhost:8000/health

# Fetch 10 sample transactions
curl "http://localhost:8000/api/v1/sample/transactions?limit=10"

# List registered pipelines
curl http://localhost:8000/api/v1/pipelines

# Trigger pipeline execution via API POST
curl -X POST "http://localhost:8000/api/v1/pipelines/etlt_plus_plus/run?source=csv&file_path=tests/fixtures/sample_transactions.csv"

# View recent pipeline runs
curl http://localhost:8000/api/v1/pipelines/executions/recent

# View latest data quality metrics
curl http://localhost:8000/api/v1/quality/metrics

# View active quality alerts
curl http://localhost:8000/api/v1/quality/alerts

# List lineage batches
curl http://localhost:8000/api/v1/lineage/batches

# Query lineage for a specific batch
curl http://localhost:8000/api/v1/lineage/batch/exec_YOUR_BATCH_ID
```

### Testing & Quality Assurance Commands

```bash
# Run all unit and integration tests (verbose output)
pytest -v

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v

# Run tests with HTML coverage report
pytest tests/ --cov=src --cov-report=html

# Clean cached test files
if exist .pytest_cache rd /s /q .pytest_cache
```

### Docker & Container Commands

```bash
# Start PostgreSQL in detached mode
docker-compose up -d

# Check running containers
docker-compose ps

# View database logs in real time
docker-compose logs -f postgres

# Stop containers without losing data
docker-compose stop

# Tear down containers and networks
docker-compose down

# Reset database volume completely (Fresh start)
docker-compose down -v
docker-compose up -d
python scripts/setup_database.py
```

### Makefile Shortcuts
If `make` is installed on your machine:
```bash
make help          # Show available targets
make setup         # Setup virtualenv and dependencies
make env           # Copy .env.example to .env
make validate      # Validate environment
make docker-up     # Start PostgreSQL Docker container
make db-setup      # Run database schema migrations
make run           # Run default pipeline
make api           # Launch FastAPI monitoring server
make test          # Run all tests
make test-cov      # Run tests with coverage report
make clean         # Clean cache directories
```

---

## 7. Architecture & Pipeline Workflows

### Pipeline Architectures

```
ETLT++ Pipeline:
[Source] ──> [Extract] ──> [Contract Validation] ──> [Data Quality Gate] ──> [Versioned Raw] ──> [Business Transform] ──> [Curated Parquet] ──> [Warehouse Load]

ELTL++ Pipeline:
[Source] ──> [Extract] ──> [Raw Storage Load] ──> [Managed Raw Zone] ──> [In-Warehouse Transform] ──> [Curated Semantic Marts] ──> [BI Consumption]
```

* **ETLT++ (Extract-Transform-Load-Transform++):** Recommended for external/untrusted feeds. Validates contracts and quality *before* raw persistence, applies business rules, and loads curated Parquet files.
* **ELTL++ (Extract-Load-Transform-Load++):** Recommended for high-volume ELT patterns where raw unvalidated data is landed immediately into cloud storage/raw tables before transformations are executed.
* **ETLT / ELTL:** Classic standard architectures supported for backward compatibility and benchmarking.

### Star Schema & Semantic Analytical Views

The data warehouse uses a Kimball-style dimensional star schema:

```
                  ┌──────────────────────┐
                  │    dim_customer      │
                  │──────────────────────│
                  │ PK  customer_key     │
                  │     customer_id      │
                  └──────────┬───────────┘
                             │
                             ▼
┌──────────────────┐  ┌──────────────────────┐  ┌──────────────────┐
│   dim_product    │  │  fact_transactions   │  │   dim_location   │
│──────────────────│  │──────────────────────│  │──────────────────│
│ PK  product_key  │◄─┤ PK  transaction_key  ├──► PK  location_key │
│     product_id   │  │ FK  customer_key     │  │     city         │
│     product_name │  │ FK  product_key      │  │     state        │
│     category     │  │ FK  location_key     │  └──────────────────┘
└──────────────────┘  │ FK  date_key         │
                      │     quantity         │
                      │     unit_price       │
                      │     total_amount     │
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │       dim_date       │
                      │──────────────────────│
                      │ PK  date_key         │
                      │     full_date        │
                      │     year, month, day │
                      └──────────────────────┘
```

#### Analytical Views (Ready for Power BI & Tableau)
Located in PostgreSQL schema `analytics`:
* `analytics.v_daily_sales`: Daily revenue, orders count, average order value, month, quarter, year.
* `analytics.v_product_performance`: Total volume sold, total revenue, average price per product SKU.
* `analytics.v_regional_analysis`: Regional sales distribution, active customers count, revenue by city.
* `analytics.v_customer_segments`: Customer-level RFM metrics (frequency, total spend, first/last purchase).
* `analytics.v_transaction_detail`: Flattened 360° denormalized table with all dimension attributes.

---

## 8. Troubleshooting & Frequently Asked Questions

### Q1: `psycopg2.OperationalError: Connection refused (10061 / 5432)`
* **Cause:** PostgreSQL is not running or is listening on a different port.
* **Solution:**
  1. If using Docker, run `docker-compose up -d` and check `docker ps`.
  2. If using native PostgreSQL, ensure the Windows Service `postgresql-x64-16` is "Running" in `services.msc`.
  3. Verify `.env` matches your host, port, username, and password.

### Q2: `ModuleNotFoundError: No module named 'src'`
* **Cause:** The current working directory is not the project root.
* **Solution:**
  Always execute commands from `d:\Major_Project_batch19\Automated-End-to-End-Pipeline` where `src/` is located:
  ```powershell
  cd d:\Major_Project_batch19\Automated-End-to-End-Pipeline
  python scripts/run_pipeline.py ...
  ```

### Q3: `ExecutionPolicy` error in PowerShell when activating `.venv`
* **Cause:** Windows PowerShell script execution policy is restricted by default.
* **Solution:**
  Run PowerShell as Administrator or run this command in your current terminal:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .venv\Scripts\Activate.ps1
  ```

### Q4: Records are being quarantined instead of appearing in curated files
* **Cause:** Input data violates the data contract in `contracts/schemas/transaction_contract.json` (e.g., negative prices, empty strings for IDs, invalid date formats).
* **Solution:**
  Check `data/quarantine/` for JSON error trace files. They will explicitly state which row and column failed validation.

### Q5: How do I completely wipe and re-initialize the warehouse?
* **Solution:**
  Run the idempotent setup script or restart the Docker container:
  ```bash
  python scripts/setup_database.py
  ```
  Or for a clean database container:
  ```bash
  docker-compose down -v
  docker-compose up -d
  python scripts/setup_database.py
  python scripts/generate_sample_data.py
  python scripts/run_pipeline.py --pipeline etlt_plus_plus --source csv --file tests/fixtures/sample_transactions.csv
  python scripts/load_warehouse.py
  ```

---

## Summary of Essential Workflow

```bash
# 1. Start Database
docker-compose up -d

# 2. Setup Database Tables
python scripts/setup_database.py

# 3. Validate Everything
python scripts/validate_environment.py

# 4. Generate Data
python scripts/generate_sample_data.py --records 500

# 5. Run Ingestion & Transformation Pipeline
python scripts/run_pipeline.py --pipeline etlt_plus_plus --source csv --file tests/fixtures/sample_transactions.csv

# 6. Load Warehouse & Refresh BI Views
python scripts/load_warehouse.py

# 7. Start API Service
uvicorn api.main:app --reload

# 8. Open BI Tool (Power BI / Tableau) & Connect to localhost:5432 / pipeline_warehouse / analytics views
```
