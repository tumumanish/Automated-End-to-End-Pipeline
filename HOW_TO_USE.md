# How to Use This Project

> For the complete, detailed step-by-step operational manual, please refer directly to:
>
> 📖 **[PROJECT_USAGE_GUIDE.md](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/PROJECT_USAGE_GUIDE.md)**

---

## Quick Reference Summary

### 1. Requirements & Tools
- **Python 3.10+**
- **PostgreSQL 16+** (via Docker Compose: `docker-compose up -d` or native service)
- **Dependencies:** `pip install -r requirements.txt`
- **BI Tools:** Power BI Desktop / Tableau Desktop

### 2. Dataset
- **Domain:** Retail Transactions (`transactions`, Contract v1.0)
- **Generate Data:** `python scripts/generate_sample_data.py --records 500`
- **Sample Fixtures:** `tests/fixtures/sample_transactions.csv`, `sample_transactions.xlsx`

### 3. Quick Run Workflow
```bash
# Setup
Copy-Item .env.example .env    # Windows PowerShell
pip install -r requirements.txt
docker-compose up -d
python scripts/setup_database.py
python scripts/validate_environment.py

# Generate Data & Run Pipeline
python scripts/generate_sample_data.py --records 500
python scripts/run_pipeline.py --pipeline etlt_plus_plus --source csv --file tests/fixtures/sample_transactions.csv

# Load Warehouse & Analytical Views
python scripts/load_warehouse.py

# Start Monitoring API
uvicorn api.main:app --reload

# Run Automated Tests
pytest tests/ -v
```

For full details, explanations of all pipeline architectures (ETLT++, ELTL++, ETLT, ELTL), data lakehouse storage zones, star schema dimensions/facts, API endpoints, curl commands, and troubleshooting, read **[PROJECT_USAGE_GUIDE.md](file:///d:/Major_Project_batch19/Automated-End-to-End-Pipeline/PROJECT_USAGE_GUIDE.md)**.
