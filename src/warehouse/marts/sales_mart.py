"""
Module: sales_mart
Purpose:
    Build aggregated sales mart tables from the star schema
    for high-performance BI consumption.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from src.storage.postgres.pg_loader import PostgresLoader
from src.utils.logger import get_logger

logger = get_logger("warehouse.marts")


class SalesMartBuilder:
    """
    Build pre-aggregated analytical marts from the warehouse
    fact and dimension tables.
    """

    def __init__(self, loader: Optional[PostgresLoader] = None):
        self._loader = loader or PostgresLoader()

    def build_daily_sales_mart(self) -> pd.DataFrame:
        """
        Aggregate fact_transactions by date for daily KPI tracking.

        Returns:
            DataFrame with daily sales aggregations.
        """
        sql = """
            SELECT
                d.full_date,
                d.day_name,
                d.month_name,
                d.quarter,
                d.year,
                d.is_weekend,
                SUM(f.amount)    AS total_sales,
                SUM(f.quantity)  AS total_quantity,
                COUNT(*)         AS transaction_count,
                AVG(f.amount)    AS avg_order_value
            FROM warehouse.fact_transactions f
            JOIN warehouse.dim_date d ON f.date_key = d.date_key
            GROUP BY d.full_date, d.day_name, d.month_name,
                     d.quarter, d.year, d.is_weekend
            ORDER BY d.full_date
        """
        df = self._loader.query(sql)
        logger.info("Daily sales mart: %d rows", len(df))
        return df

    def build_product_sales_mart(self) -> pd.DataFrame:
        """
        Aggregate fact_transactions by product for product analytics.
        """
        sql = """
            SELECT
                p.product_id,
                p.product_name,
                p.category,
                p.subcategory,
                SUM(f.amount)    AS total_revenue,
                SUM(f.quantity)  AS units_sold,
                COUNT(*)         AS transaction_count,
                AVG(f.amount)    AS avg_transaction_value
            FROM warehouse.fact_transactions f
            JOIN warehouse.dim_product p ON f.product_key = p.product_key
            WHERE p.is_current = TRUE
            GROUP BY p.product_id, p.product_name, p.category, p.subcategory
            ORDER BY total_revenue DESC
        """
        df = self._loader.query(sql)
        logger.info("Product sales mart: %d rows", len(df))
        return df

    def build_regional_sales_mart(self) -> pd.DataFrame:
        """
        Aggregate fact_transactions by location for geographic analysis.
        """
        sql = """
            SELECT
                l.location_name,
                l.city,
                l.state,
                l.region,
                SUM(f.amount)                AS total_sales,
                SUM(f.quantity)              AS total_quantity,
                COUNT(*)                     AS transaction_count,
                COUNT(DISTINCT f.customer_key) AS unique_customers
            FROM warehouse.fact_transactions f
            JOIN warehouse.dim_location l ON f.location_key = l.location_key
            GROUP BY l.location_name, l.city, l.state, l.region
            ORDER BY total_sales DESC
        """
        df = self._loader.query(sql)
        logger.info("Regional sales mart: %d rows", len(df))
        return df

    def build_all(self) -> dict:
        """Build all marts and return them as a dict of DataFrames."""
        return {
            "daily_sales": self.build_daily_sales_mart(),
            "product_sales": self.build_product_sales_mart(),
            "regional_sales": self.build_regional_sales_mart(),
        }
