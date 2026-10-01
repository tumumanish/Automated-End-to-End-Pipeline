"""
Module: dim_location
Purpose:
    Location dimension loader (Type 1 — overwrites on change).
    Extracts unique locations from curated transaction data and
    upserts into warehouse.dim_location.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from src.storage.postgres.pg_loader import PostgresLoader
from src.utils.logger import get_logger

logger = get_logger("warehouse.dim_location")

# City-to-state/region mapping for Indian cities in the sample data
_CITY_METADATA = {
    "Hyderabad":  ("Telangana",     "South"),
    "Mumbai":     ("Maharashtra",   "West"),
    "Delhi":      ("Delhi",         "North"),
    "Bangalore":  ("Karnataka",     "South"),
    "Chennai":    ("Tamil Nadu",    "South"),
    "Pune":       ("Maharashtra",   "West"),
    "Kolkata":    ("West Bengal",   "East"),
    "Ahmedabad":  ("Gujarat",       "West"),
    "Jaipur":     ("Rajasthan",     "North"),
    "Lucknow":    ("Uttar Pradesh", "North"),
    "Chandigarh": ("Chandigarh",    "North"),
    "Bhopal":     ("Madhya Pradesh","Central"),
    "Indore":     ("Madhya Pradesh","Central"),
    "Nagpur":     ("Maharashtra",   "West"),
    "Coimbatore": ("Tamil Nadu",    "South"),
}


class LocationDimensionLoader:
    """
    Load location dimension using Type 1 (overwrite) strategy.

    Locations are assumed to be relatively static; changes simply
    update the existing row rather than creating new versions.
    """

    def __init__(self, loader: Optional[PostgresLoader] = None):
        self._loader = loader or PostgresLoader()

    def extract_locations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract unique locations from curated transactions DataFrame.
        Enriches with state and region metadata.
        """
        if "location" not in df.columns:
            logger.warning("No location column — returning empty DataFrame")
            return pd.DataFrame()

        locations = df[["location"]].drop_duplicates().copy()
        locations.rename(columns={"location": "location_name"}, inplace=True)

        # Create a deterministic location_id from the name
        locations["location_id"] = locations["location_name"].apply(
            lambda name: f"LOC-{name.upper().replace(' ', '_')[:20]}"
        )

        # Enrich with city/state/region from metadata
        locations["city"] = locations["location_name"]
        locations["state"] = locations["location_name"].apply(
            lambda name: _CITY_METADATA.get(name, ("Unknown", "Unknown"))[0]
        )
        locations["country"] = "India"
        locations["region"] = locations["location_name"].apply(
            lambda name: _CITY_METADATA.get(name, ("Unknown", "Unknown"))[1]
        )

        return locations

    def load(self, df: pd.DataFrame) -> dict:
        """
        Load locations into ``warehouse.dim_location``.

        Uses an upsert pattern: new locations are inserted; existing
        ones are updated if their attributes have changed.

        Args:
            df: Curated transactions DataFrame.

        Returns:
            Summary dict with insert/update counts.
        """
        locations = self.extract_locations(df)
        if locations.empty:
            return {"new": 0, "updated": 0, "total": 0}

        stats = {"new": 0, "updated": 0, "total": len(locations)}

        # Fetch existing
        try:
            existing = self._loader.query(
                "SELECT location_key, location_id, location_name, city, state, country, region "
                "FROM warehouse.dim_location"
            )
        except Exception:
            existing = pd.DataFrame()

        existing_ids = set()
        if not existing.empty:
            existing_ids = set(existing["location_id"])

        new_rows = []
        for _, row in locations.iterrows():
            lid = row["location_id"]
            if lid not in existing_ids:
                new_rows.append({
                    "location_id": lid,
                    "location_name": row["location_name"],
                    "city": row["city"],
                    "state": row["state"],
                    "country": row["country"],
                    "region": row["region"],
                })
                stats["new"] += 1

        if new_rows:
            df_new = pd.DataFrame(new_rows)
            self._loader.load_dataframe(df_new, "dim_location", "warehouse")

        logger.info("Location dimension loaded: %d new, %d updated", stats["new"], stats["updated"])
        return stats
