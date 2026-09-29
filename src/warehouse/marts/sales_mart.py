"""
Module: sales_mart
Purpose:
    Build aggregated sales mart from warehouse fact and dimension tables.
"""

import pandas as pd
from src.storage.postgres.pg_loader import execute_query, bulk_insert
from src.utils.logger import get_logger

logger = get_logger("warehouse.marts.sales")


class SalesMartBuilder:
    """Builds and refreshes the sales analytical mart."""

    SCHEMA = "analytics"

    def build_daily_sales(self) -> pd.DataFrame:
        """Aggregate daily sales from fact + dim_date."""
        sql = """
            SELECT
                d.full_date,
                d.month_name,
                d.quarter,
                d.year,
                SUM(f.amount)                  AS total_sales,
                SUM(f.quantity)                AS total_quantity,
                COUNT(*)                       AS transaction_count,
                AVG(f.amount)                  AS avg_transaction_value,
                COUNT(DISTINCT f.customer_key) AS unique_customers
            FROM warehouse.fact_transactions f
            JOIN warehouse.dim_date d ON f.date_key = d.date_key
            GROUP BY d.full_date, d.month_name, d.quarter, d.year
            ORDER BY d.full_date
        """
        rows = execute_query(sql)
        df = pd.DataFrame(rows)
        logger.info(f"Sales mart: built daily_sales with {len(df)} rows.")
        return df

    def build_product_performance(self) -> pd.DataFrame:
        """Aggregate product performance from fact + dim_product."""
        sql = """
            SELECT
                p.product_name,
                p.category,
                SUM(f.amount)   AS total_revenue,
                SUM(f.quantity) AS units_sold,
                COUNT(*)        AS transaction_count,
                AVG(f.amount)   AS avg_transaction_value
            FROM warehouse.fact_transactions f
            JOIN warehouse.dim_product p ON f.product_key = p.product_key
            WHERE p.is_current = TRUE
            GROUP BY p.product_name, p.category
            ORDER BY total_revenue DESC
        """
        rows = execute_query(sql)
        df = pd.DataFrame(rows)
        logger.info(f"Sales mart: built product_performance with {len(df)} rows.")
        return df

    def build_regional_summary(self) -> pd.DataFrame:
        """Aggregate regional sales from fact + dim_location."""
        sql = """
            SELECT
                l.region,
                l.city,
                SUM(f.amount)                  AS total_sales,
                COUNT(*)                       AS transaction_count,
                COUNT(DISTINCT f.customer_key) AS unique_customers
            FROM warehouse.fact_transactions f
            JOIN warehouse.dim_location l ON f.location_key = l.location_key
            GROUP BY l.region, l.city
            ORDER BY total_sales DESC
        """
        rows = execute_query(sql)
        df = pd.DataFrame(rows)
        logger.info(f"Sales mart: built regional_summary with {len(df)} rows.")
        return df

    def get_summary(self) -> dict:
        """Return a high-level summary of all mart metrics."""
        return {
            "daily_sales_rows":        len(self.build_daily_sales()),
            "product_performance_rows": len(self.build_product_performance()),
            "regional_summary_rows":   len(self.build_regional_summary()),
        }
