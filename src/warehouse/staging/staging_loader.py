"""
Module: staging_loader
Purpose:
    Load curated Parquet data into staging tables, then trigger
    dimension and fact loading into the warehouse.
"""

from pathlib import Path
from datetime import date
import pandas as pd

from src.storage.postgres.pg_loader import bulk_insert
from src.warehouse.dimensions.dim_date import DateDimensionLoader
from src.warehouse.dimensions.dim_customer import CustomerDimensionLoader
from src.warehouse.dimensions.dim_product import ProductDimensionLoader
from src.warehouse.dimensions.dim_location import LocationDimensionLoader
from src.warehouse.facts.fact_transactions import FactTransactionsLoader
from src.utils.logger import get_logger
from src.utils.file_utils import get_project_root

logger = get_logger("warehouse.staging")


class StagingLoader:
    """
    Orchestrates the full warehouse load:
      Curated Parquet → Staging → Dimensions → Facts
    """

    def __init__(self):
        self.dim_date     = DateDimensionLoader()
        self.dim_customer = CustomerDimensionLoader()
        self.dim_product  = ProductDimensionLoader()
        self.dim_location = LocationDimensionLoader()
        self.fact_loader  = FactTransactionsLoader()

    def load_from_parquet(self, parquet_path: Path, batch_id: str, dataset: str = "transactions") -> dict:
        """
        Load a curated Parquet file into the warehouse.

        Args:
            parquet_path: Path to the curated .parquet file.
            batch_id: Pipeline batch identifier.
            dataset: Dataset name (default: transactions).

        Returns:
            Dict with row counts per stage.
        """
        logger.info(f"Loading {parquet_path} into warehouse (batch={batch_id})")

        df = pd.read_parquet(parquet_path)
        return self._load_dataframe(df, batch_id, dataset)

    def load_latest_curated(self, dataset: str = "transactions") -> dict:
        """Load the most recently created curated file for a dataset."""
        curated_dir = get_project_root() / "data" / "curated" / dataset
        parquet_files = sorted(curated_dir.glob("*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)

        if not parquet_files:
            logger.warning(f"No curated parquet files found for dataset '{dataset}'")
            return {}

        latest = parquet_files[0]
        batch_id = latest.stem
        return self.load_from_parquet(latest, batch_id, dataset)

    def _load_dataframe(self, df: pd.DataFrame, batch_id: str, dataset: str) -> dict:
        results = {}

        # 1. Load into staging table
        staging_count = bulk_insert(df, "staging", dataset)
        results["staging"] = staging_count

        # 2. Load date dimension
        if "transaction_date" in df.columns:
            dates = pd.to_datetime(df["transaction_date"]).dt.date
            start, end = dates.min(), dates.max()
            results["dim_date"] = self.dim_date.load(start, end)

        # 3. Load customer dimension
        results["dim_customer"] = self.dim_customer.load(df)

        # 4. Load product dimension
        results["dim_product"] = self.dim_product.load(df)

        # 5. Load location dimension
        results["dim_location"] = self.dim_location.load(df)

        # 6. Load fact table
        results["fact_transactions"] = self.fact_loader.load(df, batch_id)

        logger.info(f"Warehouse load complete for batch {batch_id}: {results}")
        return results
