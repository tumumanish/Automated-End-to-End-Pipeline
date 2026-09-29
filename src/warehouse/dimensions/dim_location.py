"""
Module: dim_location
Purpose:
    Location dimension loader (warehouse.dim_location).
"""

import pandas as pd
from src.storage.postgres.pg_loader import upsert_dimension
from src.utils.logger import get_logger

logger = get_logger("warehouse.dim_location")


class LocationDimensionLoader:
    """Loads location dimension, inserting only new locations."""

    SCHEMA = "warehouse"
    TABLE  = "dim_location"

    def extract_from_curated(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract unique locations from a curated transactions DataFrame."""
        if "location" not in df.columns:
            return pd.DataFrame()

        locations = df[["location"]].drop_duplicates().copy()
        locations.rename(columns={"location": "location_name"}, inplace=True)
        locations["location_id"] = locations["location_name"].str.upper().str.replace(" ", "_")
        locations["city"]    = locations["location_name"]
        locations["state"]   = None
        locations["country"] = "India"
        locations["region"]  = None
        return locations

    def load(self, df: pd.DataFrame) -> int:
        """Insert new locations. Returns number of rows inserted."""
        locations = self.extract_from_curated(df)
        if locations.empty:
            return 0

        count = upsert_dimension(locations, self.SCHEMA, self.TABLE, natural_key="location_id")
        logger.info(f"dim_location: loaded {count} new location records.")
        return count
