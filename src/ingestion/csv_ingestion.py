"""
Module: csv_ingestion
Purpose:
    Ingest data from CSV files into pandas DataFrames.
"""

from pathlib import Path

import pandas as pd

from src.errors.exceptions import IngestionError
from src.ingestion.base import BaseIngestion
from src.utils.logger import get_logger

logger = get_logger("pipeline")


class CSVIngestion(BaseIngestion):
    """
    Extract data from a CSV file.

    Args:
        file_path: Path to the CSV file.
        encoding: File encoding (default: utf-8).
        delimiter: Column delimiter (default: ,).
    """

    def __init__(
        self,
        file_path: str | Path,
        encoding: str = "utf-8",
        delimiter: str = ",",
    ):
        self._file_path = Path(file_path)
        self._encoding = encoding
        self._delimiter = delimiter

    @property
    def source_type(self) -> str:
        return "csv"

    @property
    def source_name(self) -> str:
        return str(self._file_path)

    def extract(self) -> pd.DataFrame:
        """
        Read the CSV file and return a DataFrame.

        Raises:
            IngestionError: If the file does not exist or cannot be read.

        Returns:
            DataFrame with CSV contents.
        """
        if not self._file_path.is_file():
            raise IngestionError(
                f"CSV file not found: {self._file_path}",
                details={"file_path": str(self._file_path)},
            )

        logger.info("Extracting CSV: %s", self._file_path)

        try:
            df = pd.read_csv(
                self._file_path,
                encoding=self._encoding,
                delimiter=self._delimiter,
            )
        except pd.errors.EmptyDataError:
            raise IngestionError(
                f"CSV file is empty: {self._file_path}",
                details={"file_path": str(self._file_path)},
            )
        except Exception as exc:
            raise IngestionError(
                f"Failed to read CSV: {exc}",
                details={"file_path": str(self._file_path)},
            ) from exc

        logger.info("CSV extracted: %d records, %d columns", len(df), len(df.columns))
        return df
