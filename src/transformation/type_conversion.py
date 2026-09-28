"""
Module: type_conversion
Purpose:
    Type casting and coercion utilities for pipeline data.
"""

import pandas as pd
import numpy as np

from src.utils.logger import get_logger

logger = get_logger("transformation.type_conversion")


class TypeConverter:
    """Convert DataFrame column types according to a target schema."""

    # Mapping from contract type names to pandas-compatible types
    TYPE_MAP = {
        "string": "object",
        "integer": "Int64",      # Nullable integer
        "number": "float64",
        "boolean": "boolean",    # Nullable boolean
        "date": "datetime64[ns]",
        "datetime": "datetime64[ns]",
    }

    @staticmethod
    def convert(df: pd.DataFrame, type_spec: dict[str, str]) -> pd.DataFrame:
        """
        Convert DataFrame columns to specified types.

        Args:
            df: Input DataFrame.
            type_spec: Dict mapping column name to target type
                       (using contract type names like 'string', 'integer', etc.).

        Returns:
            DataFrame with converted types.
        """
        df = df.copy()

        for col, target_type in type_spec.items():
            if col not in df.columns:
                continue

            pandas_type = TypeConverter.TYPE_MAP.get(target_type)
            if pandas_type is None:
                continue

            try:
                if target_type in ("date", "datetime"):
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                elif target_type == "integer":
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
                elif target_type == "number":
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                elif target_type == "boolean":
                    df[col] = df[col].astype("boolean")
                elif target_type == "string":
                    df[col] = df[col].astype(str).replace("nan", pd.NA)
            except Exception as exc:
                logger.warning(
                    "Type conversion failed | col=%s target=%s error=%s",
                    col, target_type, str(exc),
                )

        logger.info("Type conversion applied | columns=%d", len(type_spec))
        return df

    @staticmethod
    def infer_and_convert(df: pd.DataFrame) -> pd.DataFrame:
        """
        Attempt automatic type inference and conversion.

        Args:
            df: Input DataFrame.

        Returns:
            DataFrame with inferred types.
        """
        return df.convert_dtypes()
