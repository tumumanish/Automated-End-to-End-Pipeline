"""
Module: dim_customer
Purpose:
    SCD Type 2 customer dimension loader (warehouse.dim_customer).
"""

import datetime
import pandas as pd
from src.storage.postgres.pg_loader import bulk_insert, execute_query, get_engine
from src.utils.logger import get_logger
from sqlalchemy import text

logger = get_logger("warehouse.dim_customer")


class CustomerDimensionLoader:
    """Loads customer dimension with SCD Type 2 change tracking."""

    SCHEMA = "warehouse"
    TABLE  = "dim_customer"

    def extract_from_curated(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract unique customers from a curated transactions DataFrame."""
        cols = {"customer_id": "customer_id"}
        if "customer_name" in df.columns:
            cols["customer_name"] = "customer_name"
        if "segment" in df.columns:
            cols["segment"] = "segment"
        if "region" in df.columns:
            cols["region"] = "region"

        customers = df[list(cols.keys())].drop_duplicates(subset=["customer_id"]).copy()
        customers.rename(columns=cols, inplace=True)
        return customers

    def load(self, df: pd.DataFrame) -> int:
        """
        SCD2 upsert: insert new customers, expire changed ones and insert new version.
        Returns number of rows inserted.
        """
        customers = self.extract_from_curated(df)
        if customers.empty:
            return 0

        now = datetime.datetime.now(datetime.timezone.utc)
        existing = execute_query(
            f"SELECT customer_id, customer_name, segment, region FROM {self.SCHEMA}.{self.TABLE} WHERE is_current = TRUE"
        )
        existing_map = {r["customer_id"]: r for r in existing}

        new_records = []
        expire_ids = []

        for _, row in customers.iterrows():
            cid = row["customer_id"]
            if cid not in existing_map:
                new_records.append({
                    "customer_id":   cid,
                    "customer_name": row.get("customer_name"),
                    "segment":       row.get("segment"),
                    "region":        row.get("region"),
                    "valid_from":    now,
                    "valid_to":      None,
                    "is_current":    True,
                })
            else:
                existing_row = existing_map[cid]
                changed = (
                    row.get("customer_name") != existing_row.get("customer_name") or
                    row.get("segment")       != existing_row.get("segment") or
                    row.get("region")        != existing_row.get("region")
                )
                if changed:
                    expire_ids.append(cid)
                    new_records.append({
                        "customer_id":   cid,
                        "customer_name": row.get("customer_name"),
                        "segment":       row.get("segment"),
                        "region":        row.get("region"),
                        "valid_from":    now,
                        "valid_to":      None,
                        "is_current":    True,
                    })

        # Expire changed records
        if expire_ids:
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(
                    text(f"UPDATE {self.SCHEMA}.{self.TABLE} SET valid_to = :now, is_current = FALSE WHERE customer_id = ANY(:ids) AND is_current = TRUE"),
                    {"now": now, "ids": expire_ids}
                )
                conn.commit()
            engine.dispose()
            logger.info(f"dim_customer: expired {len(expire_ids)} changed records.")

        if not new_records:
            return 0

        return bulk_insert(pd.DataFrame(new_records), self.SCHEMA, self.TABLE)
