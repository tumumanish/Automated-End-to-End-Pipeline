"""
Package: warehouse.facts
Fact table loaders for the star schema.
"""

from src.warehouse.facts.fact_transactions import FactTransactionsLoader

__all__ = ["FactTransactionsLoader"]
