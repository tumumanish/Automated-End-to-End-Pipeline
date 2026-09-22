"""
Package: ingestion
Handles data extraction from multiple source types.

Classes:
    BaseIngestion   — Abstract interface for all adapters
    CSVIngestion    — CSV file extraction
    ExcelIngestion  — Excel file extraction
    APIIngestion    — REST API extraction
    DatabaseIngestion — Relational DB extraction

Factory:
    create_ingestion(source_type, **kwargs) → BaseIngestion
"""

from src.ingestion.base import BaseIngestion
from src.ingestion.csv_ingestion import CSVIngestion
from src.ingestion.excel_ingestion import ExcelIngestion
from src.ingestion.api_ingestion import APIIngestion
from src.ingestion.database_ingestion import DatabaseIngestion
from src.ingestion.ingestion_factory import create_ingestion

__all__ = [
    "BaseIngestion",
    "CSVIngestion",
    "ExcelIngestion",
    "APIIngestion",
    "DatabaseIngestion",
    "create_ingestion",
]
