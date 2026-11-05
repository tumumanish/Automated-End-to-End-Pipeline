"""
Module: enrichment
Purpose:
    Data enrichment utilities — derive new fields from existing data.
"""

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("transformation.enrichment")


class DataEnricher:
    """Enrich data by deriving new columns from existing fields."""

    @staticmethod
    def add_computed_fields(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """
        Add computed/derived fields based on dataset-specific rules.

        Args:
            df: Input DataFrame.
            dataset_name: Dataset name to determine enrichment rules.

        Returns:
            DataFrame with additional computed columns.
        """
        df = df.copy()
        original_col_count = len(df.columns)

        if dataset_name == "transactions":
            # Derive discount column if unit_price and total_amount exist
            if "unit_price" in df.columns and "quantity" in df.columns and "total_amount" in df.columns:
                expected_total = df["unit_price"] * df["quantity"]
                df["discount_amount"] = (expected_total - df["total_amount"]).clip(lower=0).round(2)
                df["has_discount"] = df["discount_amount"] > 0

            # Derive transaction_year and transaction_month
            if "transaction_date" in df.columns:
                dt_col = pd.to_datetime(df["transaction_date"], errors="coerce")
                df["transaction_year"] = dt_col.dt.year
                df["transaction_month"] = dt_col.dt.month
                df["transaction_day_of_week"] = dt_col.dt.day_name()

        new_columns_added = len(df.columns) - original_col_count
        logger.info(
            "Enrichment applied | dataset=%s new_columns=%d",
            dataset_name, new_columns_added,
        )
        return df

    @staticmethod
    def add_metadata_columns(
        df: pd.DataFrame,
        batch_id: str,
        source_system: str,
    ) -> pd.DataFrame:
        """
        Add standard metadata columns to a DataFrame.

        Args:
            df: Input DataFrame.
            batch_id: Current batch identifier.
            source_system: Source system identifier.

        Returns:
            DataFrame with metadata columns.
        """
        df = df.copy()
        df["_batch_id"] = batch_id
        df["_source_system"] = source_system
        df["_ingested_at"] = pd.Timestamp.utcnow()
        return df
