"""
Module: fact_transactions
Purpose:
    Load curated transaction data into the fact table after resolving
    surrogate keys from all four dimension tables.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from src.storage.postgres.pg_loader import PostgresLoader
from src.utils.logger import get_logger

logger = get_logger("warehouse.fact_transactions")


class FactTransactionsLoader:
    """
    Resolve surrogate keys from dimension tables and load
    transaction facts into ``warehouse.fact_transactions``.
    """

    def __init__(self, loader: Optional[PostgresLoader] = None):
        self._loader = loader or PostgresLoader()

    def _resolve_date_keys(self, df: pd.DataFrame) -> pd.Series:
        """Convert transaction_date to integer date_key (YYYYMMDD)."""
        dates = pd.to_datetime(df["transaction_date"], errors="coerce")
        return dates.dt.strftime("%Y%m%d").astype(int)

    def _resolve_customer_keys(self, df: pd.DataFrame) -> pd.Series:
        """Look up current customer_key for each customer_id."""
        try:
            dim = self._loader.query(
                "SELECT customer_key, customer_id FROM warehouse.dim_customer "
                "WHERE (is_current = 1 OR is_current = TRUE)"
            )
        except Exception:
            dim = pd.DataFrame(columns=["customer_key", "customer_id"])

        if not dim.empty and "customer_id" in dim.columns and "customer_key" in dim.columns:
            key_map = dict(zip(dim["customer_id"], dim["customer_key"]))
            return df["customer_id"].map(key_map)
        return pd.Series(index=df.index, dtype=object)

    def _resolve_product_keys(self, df: pd.DataFrame) -> pd.Series:
        """Look up current product_key for each product_id."""
        try:
            dim = self._loader.query(
                "SELECT product_key, product_id FROM warehouse.dim_product "
                "WHERE (is_current = 1 OR is_current = TRUE)"
            )
        except Exception:
            dim = pd.DataFrame(columns=["product_key", "product_id"])

        if not dim.empty and "product_id" in dim.columns and "product_key" in dim.columns:
            key_map = dict(zip(dim["product_id"], dim["product_key"]))
            return df["product_id"].map(key_map)
        return pd.Series(index=df.index, dtype=object)

    def _resolve_location_keys(self, df: pd.DataFrame) -> pd.Series:
        """Look up location_key for each location name."""
        try:
            dim = self._loader.query(
                "SELECT location_key, location_name FROM warehouse.dim_location"
            )
        except Exception:
            dim = pd.DataFrame(columns=["location_key", "location_name"])

        if not dim.empty and "location_name" in dim.columns and "location_key" in dim.columns:
            key_map = dict(zip(dim["location_name"], dim["location_key"]))
            return df["location"].map(key_map)
        return pd.Series(index=df.index, dtype=object)

    def load(self, df: pd.DataFrame, batch_id: str) -> dict:
        """
        Resolve surrogate keys and load facts into the warehouse.

        Args:
            df: Curated transactions DataFrame with columns:
                transaction_id, customer_id, product_id,
                transaction_date, quantity, unit_price, total_amount, location
            batch_id: Current pipeline execution/batch identifier.

        Returns:
            Summary dict with loaded/skipped counts.
        """
        if df.empty:
            return {"loaded": 0, "skipped": 0}

        fact_df = pd.DataFrame()
        fact_df["transaction_id"] = df["transaction_id"]
        fact_df["date_key"] = self._resolve_date_keys(df)
        fact_df["customer_key"] = self._resolve_customer_keys(df)
        fact_df["product_key"] = self._resolve_product_keys(df)
        fact_df["location_key"] = self._resolve_location_keys(df)
        fact_df["quantity"] = df["quantity"]
        fact_df["unit_price"] = df["unit_price"]
        fact_df["amount"] = df["total_amount"]
        fact_df["status"] = "completed"
        fact_df["batch_id"] = batch_id

        # Drop rows where any surrogate key could not be resolved
        before = len(fact_df)
        fact_df.dropna(
            subset=["date_key", "customer_key", "product_key", "location_key"],
            inplace=True,
        )
        skipped = before - len(fact_df)

        # Cast keys to int (they may be float after dropna)
        for col in ["date_key", "customer_key", "product_key", "location_key"]:
            fact_df[col] = fact_df[col].astype(int)

        if fact_df.empty:
            logger.warning("No fact rows to load after surrogate key resolution")
            return {"loaded": 0, "skipped": skipped}

        max_key = self._loader.get_max_key("fact_transactions", "warehouse", "transaction_key")
        fact_df["transaction_key"] = range(max_key + 1, max_key + 1 + len(fact_df))

        loaded = self._loader.load_dataframe(fact_df, "fact_transactions", "warehouse")
        logger.info(
            "Fact transactions loaded: %d rows (skipped %d — unresolved keys)",
            loaded, skipped,
        )
        return {"loaded": loaded, "skipped": skipped}
