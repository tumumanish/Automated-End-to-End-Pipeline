"""
Module: api_ingestion
Purpose:
    Extract data from REST APIs into pandas DataFrames.
"""

import requests
import pandas as pd

from src.errors.exceptions import IngestionError
from src.ingestion.base import BaseIngestion
from src.utils.logger import get_logger

logger = get_logger("pipeline")


class APIIngestion(BaseIngestion):
    """
    Extract data from a REST API endpoint.

    The endpoint is expected to return JSON with a ``records`` list.

    Args:
        url: Full API URL.
        timeout: Request timeout in seconds (default: 30).
        headers: Optional HTTP headers.
        records_key: JSON key that contains the records list (default: 'records').
    """

    def __init__(
        self,
        url: str,
        timeout: int = 30,
        headers: dict | None = None,
        records_key: str = "records",
    ):
        self._url = url
        self._timeout = timeout
        self._headers = headers or {}
        self._records_key = records_key

    @property
    def source_type(self) -> str:
        return "api"

    @property
    def source_name(self) -> str:
        return self._url

    def extract(self) -> pd.DataFrame:
        """
        Send HTTP GET request, parse JSON response, and return a DataFrame.

        Raises:
            IngestionError: On HTTP errors, timeouts, or JSON parsing failures.

        Returns:
            DataFrame built from the ``records`` in the JSON response.
        """
        logger.info("Extracting from API: %s", self._url)

        # --- HTTP request ---
        try:
            response = requests.get(
                self._url,
                headers=self._headers,
                timeout=self._timeout,
            )
        except requests.exceptions.Timeout:
            raise IngestionError(
                f"API request timed out after {self._timeout}s: {self._url}",
                details={"url": self._url, "timeout": self._timeout},
            )
        except requests.exceptions.ConnectionError as exc:
            raise IngestionError(
                f"API connection failed: {self._url} — {exc}",
                details={"url": self._url},
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise IngestionError(
                f"API request error: {exc}",
                details={"url": self._url},
            ) from exc

        # --- HTTP status check ---
        if response.status_code != 200:
            raise IngestionError(
                f"API returned HTTP {response.status_code}: {self._url}",
                details={
                    "url": self._url,
                    "status_code": response.status_code,
                    "body": response.text[:500],
                },
            )

        # --- JSON parsing ---
        try:
            data = response.json()
        except ValueError as exc:
            raise IngestionError(
                f"API response is not valid JSON: {self._url}",
                details={"url": self._url},
            ) from exc

        # --- Extract records ---
        records = data.get(self._records_key)
        if records is None:
            raise IngestionError(
                f"API response missing '{self._records_key}' key: {self._url}",
                details={"url": self._url, "keys": list(data.keys())},
            )

        if not isinstance(records, list):
            raise IngestionError(
                f"API '{self._records_key}' is not a list: {self._url}",
                details={"url": self._url, "type": type(records).__name__},
            )

        df = pd.DataFrame(records)
        logger.info("API extracted: %d records, %d columns", len(df), len(df.columns))
        return df
