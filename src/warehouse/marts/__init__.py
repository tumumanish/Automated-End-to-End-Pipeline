"""
Package: warehouse.marts
Analytical data marts built from the star schema.
"""

from src.warehouse.marts.sales_mart import SalesMartBuilder

__all__ = ["SalesMartBuilder"]
