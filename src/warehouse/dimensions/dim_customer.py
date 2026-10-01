"""
Module: dim_customer
Purpose:
    SCD Type 2 customer dimension loader.
    Extracts unique customers from curated transaction data and
    upserts into warehouse.dim_customer with history tracking.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from src.storage.postgres.pg_loader import PostgresLoader
from src.utils.logger import get_logger
from src.utils.timestamps import utc_now

logger = get_logger("warehouse.dim_customer")


class CustomerDimensionLoader:
    """
    Load customer dimension with SCD Type 2 change tracking.

    New customers are inserted as current. Changed customers have
    their existing row expired (valid_to set, is_current = FALSE)
    and a new current row inserted.
    """

    def __init__(self, loader: Optional[PostgresLoader] = None):
        self._loader = loader or PostgresLoader()

    def extract_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract unique customers from a curated transactions DataFrame.

        Since the transaction data only has ``customer_id``, we derive
        placeholder names and segments. In a production system these
        would come from a CRM source.
        """
        if "customer_id" not in df.columns:
            logger.warning("No customer_id column — returning empty DataFrame")
            return pd.DataFrame()

        customers = df[["customer_id"]].drop_duplicates().copy()
        customers["customer_name"] = customers["customer_id"].apply(
            lambda cid: f"Customer {cid}"
        )
        # Derive a simple segment from the customer ID hash
        customers["segment"] = customers["customer_id"].apply(
            lambda cid: ["Consumer", "Corporate", "Home Office"][hash(cid) % 3]
        )
        # Derive region from location if available
        if "location" in df.columns:
            loc_map = (
                df[["customer_id", "location"]]
                .drop_duplicates(subset=["customer_id"])
                .set_index("customer_id")["location"]
            )
            customers["region"] = customers["customer_id"].map(loc_map).fillna("Unknown")
        else:
            customers["region"] = "Unknown"

        return customers

    def load(self, df: pd.DataFrame) -> dict:
        """
        Load customers into ``warehouse.dim_customer`` using SCD2.

        Args:
            df: Curated transactions DataFrame.

        Returns:
            Summary dict with insert/update counts.
        """
        customers = self.extract_customers(df)
        if customers.empty:
            return {"new": 0, "changed": 0, "total": 0}

        now = utc_now()
        stats = {"new": 0, "changed": 0, "total": len(customers)}

        # Fetch existing current dimension rows
        try:
            existing = self._loader.query(
                "SELECT customer_key, customer_id, customer_name, segment, region "
                "FROM warehouse.dim_customer WHERE is_current = TRUE"
            )
        except Exception:
            existing = pd.DataFrame()

        existing_map = {}
        if not existing.empty:
            existing_map = existing.set_index("customer_id").to_dict("index")

        new_rows = []
        for _, row in customers.iterrows():
            cid = row["customer_id"]
            if cid not in existing_map:
                # New customer — insert
                new_rows.append({
                    "customer_id": cid,
                    "customer_name": row["customer_name"],
                    "segment": row["segment"],
                    "region": row["region"],
                    "valid_from": now,
                    "valid_to": None,
                    "is_current": True,
                })
                stats["new"] += 1
            else:
                # Check for changes
                ex = existing_map[cid]
                changed = (
                    ex.get("segment") != row["segment"]
                    or ex.get("region") != row["region"]
                    or ex.get("customer_name") != row["customer_name"]
                )
                if changed:
                    # Expire old row
                    self._loader.execute_sql(
                        "UPDATE warehouse.dim_customer "
                        "SET valid_to = :now, is_current = FALSE "
                        "WHERE customer_id = :cid AND is_current = TRUE",
                        {"now": now, "cid": cid},
                    )
                    new_rows.append({
                        "customer_id": cid,
                        "customer_name": row["customer_name"],
                        "segment": row["segment"],
                        "region": row["region"],
                        "valid_from": now,
                        "valid_to": None,
                        "is_current": True,
                    })
                    stats["changed"] += 1

        if new_rows:
            df_new = pd.DataFrame(new_rows)
            self._loader.load_dataframe(df_new, "dim_customer", "warehouse")

        logger.info("Customer dimension loaded: %d new, %d changed", stats["new"], stats["changed"])
        return stats
