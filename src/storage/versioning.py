"""
Module: versioning
Purpose:
    Implement append-only, versioned data storage with SCD Type 2 logic.
    Tracks record history via record_hash change detection.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

import pandas as pd

from src.utils.hashing import hash_record
from src.utils.logger import get_logger
from src.utils.timestamps import utc_now

logger = get_logger("storage.versioning")


@dataclass
class VersionedRecord:
    """Represents a single versioned record with SCD2 metadata."""
    record_id: str
    dataset_name: str
    source_system: str
    batch_id: str
    ingestion_timestamp: datetime
    valid_from: datetime
    valid_to: Optional[datetime] = None
    record_hash: str = ""
    schema_version: str = "1.0"
    is_current: bool = True

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "dataset_name": self.dataset_name,
            "source_system": self.source_system,
            "batch_id": self.batch_id,
            "ingestion_timestamp": self.ingestion_timestamp.isoformat(),
            "valid_from": self.valid_from.isoformat(),
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "record_hash": self.record_hash,
            "schema_version": self.schema_version,
            "is_current": self.is_current,
        }


class VersionStore:
    """In-memory version store backed by a list (can be extended to database)."""

    def __init__(self):
        self._versions: List[VersionedRecord] = []

    def get_current_version(self, record_id: str, dataset_name: str) -> Optional[VersionedRecord]:
        """Get the current active version of a record."""
        for v in reversed(self._versions):
            if v.record_id == record_id and v.dataset_name == dataset_name and v.is_current:
                return v
        return None

    def get_version_history(self, record_id: str, dataset_name: str) -> List[VersionedRecord]:
        """Get all versions of a record, ordered by valid_from."""
        history = [
            v for v in self._versions
            if v.record_id == record_id and v.dataset_name == dataset_name
        ]
        return sorted(history, key=lambda v: v.valid_from)

    def expire_record(self, record_id: str, dataset_name: str, expire_time: datetime) -> None:
        """Expire the current version of a record (SCD2 close)."""
        for v in self._versions:
            if v.record_id == record_id and v.dataset_name == dataset_name and v.is_current:
                v.valid_to = expire_time
                v.is_current = False
                break

    def add_version(self, record: VersionedRecord) -> None:
        """Add a new version record."""
        self._versions.append(record)

    @property
    def all_records(self) -> List[VersionedRecord]:
        return list(self._versions)


class DataVersionManager:
    """
    Manages SCD Type 2 versioning for incoming data batches.

    On each new batch:
      - New records → inserted with is_current=True
      - Changed records → previous version expired, new version inserted
      - Unchanged records → skipped (no duplicate)
    """

    def __init__(self, store: VersionStore | None = None):
        self._store = store or VersionStore()

    def apply_versioning(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        source_system: str,
        batch_id: str,
        record_id_column: str,
        schema_version: str = "1.0",
    ) -> dict:
        """
        Apply SCD Type 2 versioning to an incoming DataFrame.

        Args:
            df: The new batch of records.
            dataset_name: Logical dataset name.
            source_system: Origin system identifier.
            batch_id: Current batch identifier.
            record_id_column: Column used as the business key.
            schema_version: Version of the schema/contract.

        Returns:
            Summary dict with counts: new, changed, unchanged.
        """
        now = utc_now()
        stats = {"new": 0, "changed": 0, "unchanged": 0, "total": len(df)}

        for _, row in df.iterrows():
            row_dict = row.to_dict()
            record_id = str(row_dict.get(record_id_column, ""))
            if not record_id:
                continue

            new_hash = hash_record(row_dict)
            current = self._store.get_current_version(record_id, dataset_name)

            if current is None:
                # New record — insert
                self._store.add_version(VersionedRecord(
                    record_id=record_id,
                    dataset_name=dataset_name,
                    source_system=source_system,
                    batch_id=batch_id,
                    ingestion_timestamp=now,
                    valid_from=now,
                    record_hash=new_hash,
                    schema_version=schema_version,
                    is_current=True,
                ))
                stats["new"] += 1

            elif current.record_hash != new_hash:
                # Changed record — expire old, insert new
                self._store.expire_record(record_id, dataset_name, now)
                self._store.add_version(VersionedRecord(
                    record_id=record_id,
                    dataset_name=dataset_name,
                    source_system=source_system,
                    batch_id=batch_id,
                    ingestion_timestamp=now,
                    valid_from=now,
                    record_hash=new_hash,
                    schema_version=schema_version,
                    is_current=True,
                ))
                stats["changed"] += 1

            else:
                # Unchanged — skip
                stats["unchanged"] += 1

        logger.info(
            "Versioning applied | dataset=%s batch=%s | new=%d changed=%d unchanged=%d",
            dataset_name, batch_id, stats["new"], stats["changed"], stats["unchanged"],
        )
        return stats

    def get_current_snapshot(self, dataset_name: str) -> List[VersionedRecord]:
        """Get all current (active) records for a dataset."""
        return [
            v for v in self._store.all_records
            if v.dataset_name == dataset_name and v.is_current
        ]

    def rollback_batch(self, batch_id: str, dataset_name: str) -> int:
        """
        Rollback a specific batch by removing its versions and re-activating
        previously expired records where applicable.

        Returns:
            Number of records rolled back.
        """
        rolled_back = 0
        # Find records introduced by this batch
        batch_records = [
            v for v in self._store.all_records
            if v.batch_id == batch_id and v.dataset_name == dataset_name
        ]

        for record in batch_records:
            # Remove the batch record
            self._store._versions.remove(record)
            rolled_back += 1

            # Re-activate the previous version if it was expired by this batch
            history = self._store.get_version_history(record.record_id, dataset_name)
            if history:
                latest = history[-1]
                if not latest.is_current:
                    latest.is_current = True
                    latest.valid_to = None

        logger.info(
            "Rollback completed | batch=%s dataset=%s | rolled_back=%d",
            batch_id, dataset_name, rolled_back,
        )
        return rolled_back

    @property
    def store(self) -> VersionStore:
        return self._store
