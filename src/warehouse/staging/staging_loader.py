"""
Module: staging_loader
Purpose:
    Load curated Parquet/CSV files into staging tables, then
    orchestrate the full warehouse loading pipeline:
        Curated → Staging → Dimensions → Facts
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from src.storage.postgres.pg_loader import PostgresLoader
from src.utils.file_utils import get_project_root
from src.utils.logger import get_logger
from src.warehouse.dimensions.dim_date import DateDimensionLoader
from src.warehouse.dimensions.dim_customer import CustomerDimensionLoader
from src.warehouse.dimensions.dim_product import ProductDimensionLoader
from src.warehouse.dimensions.dim_location import LocationDimensionLoader
from src.warehouse.facts.fact_transactions import FactTransactionsLoader

logger = get_logger("warehouse.staging")


class StagingLoader:
    """
    Orchestrates the warehouse loading pipeline:

    1. Read curated Parquet/CSV from ``data/curated/``
    2. Load into staging tables (truncate + reload)
    3. Populate dimension tables (SCD2 upserts)
    4. Populate fact tables (surrogate key resolution)
    """

    def __init__(self, loader: Optional[PostgresLoader] = None):
        self._loader = loader or PostgresLoader()
        self._dim_date = DateDimensionLoader(self._loader)
        self._dim_customer = CustomerDimensionLoader(self._loader)
        self._dim_product = ProductDimensionLoader(self._loader)
        self._dim_location = LocationDimensionLoader(self._loader)
        self._fact_txn = FactTransactionsLoader(self._loader)

    def read_curated_data(
        self,
        dataset: str = "transactions",
        batch_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Read curated data from the filesystem.

        If ``batch_id`` is provided, reads a specific batch file.
        Otherwise reads all files in the dataset directory and
        concatenates them.

        Args:
            dataset: Dataset name (subdirectory under data/curated/).
            batch_id: Optional specific batch to load.

        Returns:
            DataFrame with the curated data.
        """
        root = get_project_root()
        curated_dir = root / "data" / "curated" / dataset

        if not curated_dir.exists():
            logger.warning("Curated directory not found: %s", curated_dir)
            return pd.DataFrame()

        if batch_id:
            # Try parquet first, then CSV
            parquet_path = curated_dir / f"{batch_id}.parquet"
            csv_path = curated_dir / f"{batch_id}.csv"
            if parquet_path.is_file():
                return pd.read_parquet(parquet_path)
            elif csv_path.is_file():
                return pd.read_csv(csv_path)
            else:
                logger.warning("Batch file not found: %s or %s", parquet_path, csv_path)
                return pd.DataFrame()

        # Read all files in the directory
        frames = []
        for f in sorted(curated_dir.iterdir()):
            if f.suffix == ".parquet":
                frames.append(pd.read_parquet(f))
            elif f.suffix == ".csv":
                frames.append(pd.read_csv(f))

        if not frames:
            logger.warning("No curated files found in %s", curated_dir)
            return pd.DataFrame()

        df = pd.concat(frames, ignore_index=True)
        logger.info("Read %d curated records from %d files", len(df), len(frames))
        return df

    def load_staging(self, df: pd.DataFrame, batch_id: str) -> int:
        """
        Truncate and reload the staging transactions table.

        Returns:
            Number of rows staged.
        """
        if df.empty:
            return 0

        # Build staging DataFrame with expected columns
        stg = pd.DataFrame({
            "transaction_id": df.get("transaction_id"),
            "customer_id": df.get("customer_id"),
            "product_id": df.get("product_id"),
            "transaction_date": pd.to_datetime(df.get("transaction_date"), errors="coerce"),
            "quantity": df.get("quantity"),
            "unit_price": df.get("unit_price"),
            "total_amount": df.get("total_amount"),
            "location": df.get("location"),
            "batch_id": batch_id,
        })

        try:
            self._loader.truncate_table("stg_transactions", "staging")
        except Exception:
            pass  # Table may not exist yet on first run

        count = self._loader.load_dataframe(stg, "stg_transactions", "staging")
        logger.info("Staged %d transaction rows", count)
        return count

    def run(
        self,
        dataset: str = "transactions",
        batch_id: Optional[str] = None,
    ) -> dict:
        """
        Execute the full warehouse loading pipeline.

        Args:
            dataset: Dataset name to load.
            batch_id: Optional specific batch (loads all if omitted).

        Returns:
            Summary dict with results from each stage.
        """
        logger.info("=" * 60)
        logger.info("WAREHOUSE LOAD PIPELINE START")
        logger.info("=" * 60)

        # 1. Read curated data
        df = self.read_curated_data(dataset, batch_id)
        if df.empty:
            logger.warning("No curated data to load. Aborting warehouse load.")
            return {"status": "NO_DATA", "records": 0}

        effective_batch = batch_id or "full_load"

        # 2. Stage data
        staged = self.load_staging(df, effective_batch)

        # 3. Load date dimension (idempotent — generates full calendar)
        date_count = self._dim_date.load()

        # 4. Load dimensions from curated data
        cust_stats = self._dim_customer.load(df)
        prod_stats = self._dim_product.load(df)
        loc_stats = self._dim_location.load(df)

        # 5. Load facts (with surrogate key resolution)
        fact_stats = self._fact_txn.load(df, effective_batch)

        summary = {
            "status": "SUCCESS",
            "records_staged": staged,
            "date_dimension_rows": date_count,
            "customers": cust_stats,
            "products": prod_stats,
            "locations": loc_stats,
            "facts": fact_stats,
        }

        logger.info("=" * 60)
        logger.info("WAREHOUSE LOAD PIPELINE COMPLETE")
        logger.info("Summary: %s", summary)
        logger.info("=" * 60)

        return summary
