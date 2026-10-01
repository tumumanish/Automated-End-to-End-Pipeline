"""
Module: dim_product
Purpose:
    SCD Type 2 product dimension loader.
    Extracts unique products from curated transaction data and
    upserts into warehouse.dim_product with history tracking.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from src.storage.postgres.pg_loader import PostgresLoader
from src.utils.logger import get_logger
from src.utils.timestamps import utc_now

logger = get_logger("warehouse.dim_product")

# Product catalogue reference — maps product_id to (name, category, subcategory)
_PRODUCT_CATALOG = {
    "PROD-001": ("Laptop", "Electronics", "Computers"),
    "PROD-002": ("Smartphone", "Electronics", "Mobile"),
    "PROD-003": ("Tablet", "Electronics", "Mobile"),
    "PROD-004": ("Monitor", "Electronics", "Displays"),
    "PROD-005": ("Keyboard", "Accessories", "Input Devices"),
    "PROD-006": ("Mouse", "Accessories", "Input Devices"),
    "PROD-007": ("Headphones", "Accessories", "Audio"),
    "PROD-008": ("Webcam", "Accessories", "Video"),
    "PROD-009": ("Printer", "Electronics", "Office"),
    "PROD-010": ("Speaker", "Accessories", "Audio"),
    "PROD-011": ("External SSD", "Storage", "Drives"),
    "PROD-012": ("USB Hub", "Accessories", "Connectivity"),
}


class ProductDimensionLoader:
    """
    Load product dimension with SCD Type 2 change tracking.
    """

    def __init__(self, loader: Optional[PostgresLoader] = None):
        self._loader = loader or PostgresLoader()

    def extract_products(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract unique products from curated transactions DataFrame.
        Enriches with catalogue metadata (name, category, subcategory).
        """
        if "product_id" not in df.columns:
            logger.warning("No product_id column — returning empty DataFrame")
            return pd.DataFrame()

        products = df[["product_id"]].drop_duplicates().copy()

        # Enrich from catalogue
        products["product_name"] = products["product_id"].apply(
            lambda pid: _PRODUCT_CATALOG.get(pid, (pid, "Other", "Other"))[0]
        )
        products["category"] = products["product_id"].apply(
            lambda pid: _PRODUCT_CATALOG.get(pid, (pid, "Other", "Other"))[1]
        )
        products["subcategory"] = products["product_id"].apply(
            lambda pid: _PRODUCT_CATALOG.get(pid, (pid, "Other", "Other"))[2]
        )

        # Get the most common unit_price per product from the data
        if "unit_price" in df.columns:
            price_map = df.groupby("product_id")["unit_price"].median()
            products["unit_price"] = products["product_id"].map(price_map).fillna(0)
        else:
            products["unit_price"] = 0

        return products

    def load(self, df: pd.DataFrame) -> dict:
        """
        Load products into ``warehouse.dim_product`` using SCD2.

        Args:
            df: Curated transactions DataFrame.

        Returns:
            Summary dict with insert/update counts.
        """
        products = self.extract_products(df)
        if products.empty:
            return {"new": 0, "changed": 0, "total": 0}

        now = utc_now()
        stats = {"new": 0, "changed": 0, "total": len(products)}

        # Fetch existing current dimension rows
        try:
            existing = self._loader.query(
                "SELECT product_key, product_id, product_name, category, subcategory, unit_price "
                "FROM warehouse.dim_product WHERE is_current = TRUE"
            )
        except Exception:
            existing = pd.DataFrame()

        existing_map = {}
        if not existing.empty:
            existing_map = existing.set_index("product_id").to_dict("index")

        new_rows = []
        for _, row in products.iterrows():
            pid = row["product_id"]
            if pid not in existing_map:
                new_rows.append({
                    "product_id": pid,
                    "product_name": row["product_name"],
                    "category": row["category"],
                    "subcategory": row["subcategory"],
                    "unit_price": row["unit_price"],
                    "valid_from": now,
                    "valid_to": None,
                    "is_current": True,
                })
                stats["new"] += 1
            else:
                ex = existing_map[pid]
                changed = (
                    ex.get("category") != row["category"]
                    or ex.get("subcategory") != row["subcategory"]
                    or ex.get("product_name") != row["product_name"]
                )
                if changed:
                    self._loader.execute_sql(
                        "UPDATE warehouse.dim_product "
                        "SET valid_to = :now, is_current = FALSE "
                        "WHERE product_id = :pid AND is_current = TRUE",
                        {"now": now, "pid": pid},
                    )
                    new_rows.append({
                        "product_id": pid,
                        "product_name": row["product_name"],
                        "category": row["category"],
                        "subcategory": row["subcategory"],
                        "unit_price": row["unit_price"],
                        "valid_from": now,
                        "valid_to": None,
                        "is_current": True,
                    })
                    stats["changed"] += 1

        if new_rows:
            df_new = pd.DataFrame(new_rows)
            self._loader.load_dataframe(df_new, "dim_product", "warehouse")

        logger.info("Product dimension loaded: %d new, %d changed", stats["new"], stats["changed"])
        return stats
