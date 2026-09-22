# Project Requirements

## Functional Requirements

1. Ingest data from REST APIs, CSV files, Excel files, and relational databases.
2. Validate data against registered data contracts (schema and business rules).
3. Quarantine invalid records with full context and audit trail.
4. Transform data through cleaning, normalization, deduplication, and enrichment.
5. Store data in versioned raw, staging, and curated zones.
6. Build a dimensional data warehouse using star schema modeling.
7. Support both ETLT++ and ELTL++ pipeline patterns.
8. Track data lineage from source to destination.
9. Monitor data quality: freshness, completeness, accuracy, contract adherence.
10. Deliver curated analytical datasets to Power BI and Tableau.

## Non-Functional Requirements

1. Configuration-driven: No hard-coded paths, credentials, or business rules.
2. Modular architecture: Each concern in its own module.
3. Testable: Unit and integration test coverage.
4. Reproducible: Docker-based local development environment.
5. Secure: No secrets in source code.

## Technology Constraints

- Python 3.10+
- PostgreSQL (local), Snowflake (cloud, optional)
- Pandas, SQLAlchemy, FastAPI, Pydantic
- Power BI and Tableau for BI
