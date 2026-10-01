"""
Package: warehouse.staging
Staging ETL — loads curated Parquet/CSV into staging tables
and orchestrates the warehouse loading pipeline.
"""

from src.warehouse.staging.staging_loader import StagingLoader

__all__ = ["StagingLoader"]
