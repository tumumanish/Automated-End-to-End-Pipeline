"""
Module: dim_product
Purpose:
    SCD Type 2 product dimension loader (warehouse.dim_product).
"""

import datetime
import pandas as pd
from src.storage.postgres.pg_loader import bulk_insert, execute_query, get_engine
from src.utils.logger import get_logger
from sqlalchemy import text

logger = get_logger("warehouse.dim_product")


class ProductDimensionLoader:
    """Loads product dimension with SCD Type 2 change tracking."""

    SCHEMA = "warehouse"
    TABLE  = "dim_product"

    def extract_from_curated(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract unique products from a curated transactions DataFrame."""
        cols = ["product_id"]
        for c in ["product_name", "category", "subcategory"]:
            if c in df.columns:
                cols.append(c)
        return df[cols].drop_duplicates(subset=["product_id"]).copy()

    def load(self, df: pd.DataFrame) -> int:
        """SCD2 upsert for products. Returns number of rows inserted."""
        products = self.extract_from_curated(df)
        if products.empty:
            return 0

        now = datetime.datetime.now(datetime.timezone.utc)
        existing = execute_query(
            f"SELECT product_id, product_name, category, subcategory FROM {self.SCHEMA}.{self.TABLE} WHERE is_current = TRUE"
        )
        existing_map = {r["product_id"]: r for r in existing}

        new_records = []
        expire_ids = []

        for _, row in products.iterrows():
            pid = row["product_id"]
            if pid not in existing_map:
                new_records.append({
                    "product_id":   pid,
                    "product_name": row.get("product_name"),
                    "category":     row.get("category"),
                    "subcategory":  row.get("subcategory"),
                    "valid_from":   now,
                    "valid_to":     None,
                    "is_current":   True,
                })
            else:
                existing_row = existing_map[pid]
                changed = (
                    row.get("product_name") != existing_row.get("product_name") or
                    row.get("category")     != existing_row.get("category") or
                    row.get("subcategory")  != existing_row.get("subcategory")
                )
                if changed:
                    expire_ids.append(pid)
                    new_records.append({
                        "product_id":   pid,
                        "product_name": row.get("product_name"),
                        "category":     row.get("category"),
                        "subcategory":  row.get("subcategory"),
                        "valid_from":   now,
                        "valid_to":     None,
                        "is_current":   True,
                    })

        if expire_ids:
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(
                    text(f"UPDATE {self.SCHEMA}.{self.TABLE} SET valid_to = :now, is_current = FALSE WHERE product_id = ANY(:ids) AND is_current = TRUE"),
                    {"now": now, "ids": expire_ids}
                )
                conn.commit()
            engine.dispose()
            logger.info(f"dim_product: expired {len(expire_ids)} changed records.")

        if not new_records:
            return 0

        return bulk_insert(pd.DataFrame(new_records), self.SCHEMA, self.TABLE)
