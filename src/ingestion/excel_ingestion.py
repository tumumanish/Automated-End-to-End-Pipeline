"""
Module: excel_ingestion
Purpose:
    Ingest data from Excel (.xlsx) files into pandas DataFrames.
"""

from pathlib import Path

import pandas as pd

from src.errors.exceptions import IngestionError
from src.ingestion.base import BaseIngestion
from src.utils.logger import get_logger

logger = get_logger("pipeline")


class ExcelIngestion(BaseIngestion):
    """
    Extract data from an Excel workbook.

    Args:
        file_path: Path to the .xlsx file.
        sheet_name: Sheet name or index to read (default: first sheet).
    """

    def __init__(
        self,
        file_path: str | Path,
        sheet_name: str | int = 0,
    ):
        self._file_path = Path(file_path)
        self._sheet_name = sheet_name

    @property
    def source_type(self) -> str:
        return "excel"

    @property
    def source_name(self) -> str:
        return str(self._file_path)

    def extract(self) -> pd.DataFrame:
        """
        Read the Excel file and return a DataFrame.

        Raises:
            IngestionError: If the file does not exist or cannot be read.

        Returns:
            DataFrame with Excel sheet contents.
        """
        if not self._file_path.is_file():
            raise IngestionError(
                f"Excel file not found: {self._file_path}",
                details={"file_path": str(self._file_path)},
            )

        logger.info("Extracting Excel: %s (sheet=%s)", self._file_path, self._sheet_name)

        try:
            df = pd.read_excel(
                self._file_path,
                sheet_name=self._sheet_name,
                engine="openpyxl",
            )
        except Exception as exc:
            raise IngestionError(
                f"Failed to read Excel: {exc}",
                details={
                    "file_path": str(self._file_path),
                    "sheet_name": str(self._sheet_name),
                },
            ) from exc

        logger.info("Excel extracted: %d records, %d columns", len(df), len(df.columns))
        return df
