"""
Package: src
Root package for the Automated Data Pipeline & BI Architecture.

Subpackages:
    - ingestion: Data extraction from APIs, CSV, Excel, databases
    - contracts: Data contract loading, validation, and registry
    - transformation: Data cleaning, normalization, enrichment
    - pipelines: ETLT/ELTL pipeline definitions and orchestration
    - storage: PostgreSQL/Snowflake connections, versioning, checkpoints
    - warehouse: Dimensional modeling (dimensions, facts, marts, views)
    - lineage: Data lineage tracking and metadata collection
    - monitoring: Data quality metrics and pipeline monitoring
    - errors: Exception definitions, error handling, quarantine
    - utils: Shared utilities (logging, hashing, file I/O)
"""
