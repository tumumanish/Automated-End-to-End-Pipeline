"""
Package: warehouse
Dimensional data warehouse modeling — dimensions, facts, staging, marts, views.

Subpackages:
    - dimensions: Dimension table loaders (dim_date, dim_customer, dim_product, dim_location)
    - facts: Fact table loaders (fact_transactions)
    - staging: Staging ETL and warehouse load orchestration
    - marts: Pre-aggregated analytical data marts
    - views: Analytical view management
"""

from src.warehouse.staging.staging_loader import StagingLoader

__all__ = ["StagingLoader"]
