"""
Module: ingestion_factory
Purpose:
    Factory for creating the appropriate ingestion adapter based on source type.
"""

from typing import Any

from src.errors.exceptions import IngestionError
from src.ingestion.api_ingestion import APIIngestion
from src.ingestion.base import BaseIngestion
from src.ingestion.csv_ingestion import CSVIngestion
from src.ingestion.database_ingestion import DatabaseIngestion
from src.ingestion.excel_ingestion import ExcelIngestion

# Registry mapping source type strings to adapter classes
_ADAPTER_REGISTRY: dict[str, type[BaseIngestion]] = {
    "csv": CSVIngestion,
    "excel": ExcelIngestion,
    "api": APIIngestion,
    "database": DatabaseIngestion,
}


def create_ingestion(source_type: str, **kwargs: Any) -> BaseIngestion:
    """
    Create an ingestion adapter for the given source type.

    Args:
        source_type: One of 'csv', 'excel', 'api', 'database'.
        **kwargs: Arguments forwarded to the adapter constructor.
            - csv:      file_path, encoding, delimiter
            - excel:    file_path, sheet_name
            - api:      url, timeout, headers, records_key
            - database: connection_string, query

    Raises:
        IngestionError: If the source type is not supported.

    Returns:
        An instance of the appropriate BaseIngestion subclass.

    Example::

        adapter = create_ingestion("csv", file_path="data.csv")
        df = adapter.extract()
    """
    adapter_cls = _ADAPTER_REGISTRY.get(source_type.lower())

    if adapter_cls is None:
        supported = ", ".join(sorted(_ADAPTER_REGISTRY))
        raise IngestionError(
            f"Unsupported source type: '{source_type}'. Supported: {supported}",
            details={"source_type": source_type, "supported": list(_ADAPTER_REGISTRY)},
        )

    return adapter_cls(**kwargs)


def list_supported_sources() -> list[str]:
    """Return the list of supported source type identifiers."""
    return sorted(_ADAPTER_REGISTRY.keys())
