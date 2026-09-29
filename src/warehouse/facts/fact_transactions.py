"""
Module: fact_transactions
Purpose:
    Load curated transactions into warehouse.fact_transactions
    by resolving surrogate keys from dimension tables.
"""

import pandas as pd
from src.storage.postgres.pg_loader import bulk_insert, execute_query
from src.utils.logger import get_logger

logger = get_logger("warehouse.fact_transactions")


class FactTransactionsLoader:
    """Resolves dimension surrogate keys and loads fact_transactions."""

    SCHEMA = "warehouse"
    TABLE  = "fact_transactions"

    def _load_dim_map(self, table: str, natural_key: str, surrogate_key: str, extra_filter: str = "") -> dict:
        """Load a natural_key -> surrogate_key mapping from a dimension table."""
        sql = f"SELECT {natural_key}, {surrogate_key} FROM warehouse.{table}"
        if extra_filter:
            sql += f" WHERE {extra_filter}"
        rows = execute_query(sql)
        return {r[natural_key]: r[surrogate_key] for r in rows}

    def load(self, df: pd.DataFrame, batch_id: str) -> int:
        """
        Resolve surrogate keys and insert into fact_transactions.

        Args:
            df: Curated transactions DataFrame.
            batch_id: Pipeline batch identifier.

        Returns:
            Number of rows inserted.
        """
        if df.empty:
            logger.warning("No data to load into fact_transactions.")
            return 0

        # Load dimension maps
        date_map     = self._load_dim_map("dim_date",     "full_date",    "date_key")
        customer_map = self._load_dim_map("dim_customer", "customer_id",  "customer_key", "is_current = TRUE")
        product_map  = self._load_dim_map("dim_product",  "product_id",   "product_key",  "is_current = TRUE")
        location_map = self._load_dim_map("dim_location", "location_id",  "location_key")

        facts = df.copy()

        # Resolve date_key
        if "transaction_date" in facts.columns:
            facts["transaction_date"] = pd.to_datetime(facts["transaction_date"]).dt.date
            facts["date_key"] = facts["transaction_date"].astype(str).map(
                lambda d: date_map.get(pd.to_datetime(d).date())
            )
        else:
            facts["date_key"] = None

        # Resolve customer_key
        facts["customer_key"] = facts.get("customer_id", pd.Series()).map(customer_map)

        # Resolve product_key
        facts["product_key"] = facts.get("product_id", pd.Series()).map(product_map)

        # Resolve location_key
        if "location" in facts.columns:
            location_id_map = {v.replace(" ", "_").upper(): k for k, v in
                               {r["location_id"]: r["location_id"] for r in execute_query("SELECT location_id FROM warehouse.dim_location")}.items()}
            facts["location_key"] = facts["location"].str.upper().str.replace(" ", "_").map(
                lambda lid: location_map.get(lid)
            )
        else:
            facts["location_key"] = None

        # Build fact rows
        fact_cols = {
            "transaction_id": facts.get("transaction_id"),
            "date_key":       facts["date_key"],
            "customer_key":   facts["customer_key"],
            "product_key":    facts["product_key"],
            "location_key":   facts["location_key"],
            "amount":         facts.get("total_amount", facts.get("calculated_total")),
            "quantity":       facts.get("quantity"),
            "unit_price":     facts.get("unit_price"),
            "status":         facts.get("status"),
            "is_high_value":  facts.get("is_high_value", False),
            "batch_id":       batch_id,
        }

        fact_df = pd.DataFrame({k: v for k, v in fact_cols.items() if v is not None})

        count = bulk_insert(fact_df, self.SCHEMA, self.TABLE)
        logger.info(f"fact_transactions: loaded {count} rows for batch {batch_id}.")
        return count
