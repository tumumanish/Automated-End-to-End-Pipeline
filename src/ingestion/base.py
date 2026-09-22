"""
Module: base
Purpose:
    Abstract base class for all ingestion adapters.
    Every source type (API, CSV, Excel, Database) implements this interface
    so the pipeline can treat them uniformly.
"""

from abc import ABC, abstractmethod

import pandas as pd


class BaseIngestion(ABC):
    """
    Common interface for data ingestion adapters.

    Subclasses must implement:
        - extract()    → return a pandas DataFrame
        - source_type  → return the source type identifier
    """

    @abstractmethod
    def extract(self) -> pd.DataFrame:
        """
        Extract data from the source and return it as a DataFrame.

        Raises:
            IngestionError: If extraction fails.

        Returns:
            pandas DataFrame containing the extracted records.
        """
        ...

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return the source type identifier (e.g., 'csv', 'api', 'excel', 'database')."""
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return a human-readable source name (file path, URL, table, etc.)."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.source_type}, name={self.source_name})"
