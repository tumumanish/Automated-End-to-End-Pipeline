"""
Module: quality_metrics
Purpose:
    Calculate and aggregate data quality metrics across all dimensions.
    Provides a unified BatchQualityMetrics dataclass combining freshness,
    completeness, accuracy, and contract adherence scores.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

import pandas as pd

from src.contracts.validation_result import ValidationResult
from src.monitoring.freshness import FreshnessMonitor
from src.monitoring.completeness import CompletenessMonitor
from src.monitoring.accuracy import AccuracyMonitor
from src.monitoring.contract_adherence import ContractAdherenceMonitor
from src.utils.logger import get_logger
from src.utils.timestamps import utc_now

logger = get_logger("monitoring.quality")


@dataclass
class BatchQualityMetrics:
    """Aggregated quality metrics for a single batch."""
    batch_id: str
    dataset_name: str
    source: str
    timestamp: str
    record_count: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    quarantined_count: int = 0
    freshness_score: float = 0.0
    completeness_score: float = 0.0
    accuracy_score: float = 0.0
    contract_adherence_score: float = 0.0
    pipeline_status: str = "UNKNOWN"
    processing_duration_seconds: float = 0.0

    @property
    def overall_score(self) -> float:
        """Calculate the overall quality score as a weighted average."""
        weights = {
            "freshness": 0.15,
            "completeness": 0.30,
            "accuracy": 0.35,
            "contract_adherence": 0.20,
        }
        return round(
            self.freshness_score * weights["freshness"]
            + self.completeness_score * weights["completeness"]
            + self.accuracy_score * weights["accuracy"]
            + self.contract_adherence_score * weights["contract_adherence"],
            2,
        )

    def to_dict(self) -> dict:
        result = asdict(self)
        result["overall_score"] = self.overall_score
        return result


class QualityMetricsCalculator:
    """
    Orchestrates all quality monitors and produces a unified
    BatchQualityMetrics for each batch.
    """

    def __init__(
        self,
        max_freshness_hours: float = 24.0,
        min_completeness: float = 95.0,
        min_accuracy: float = 98.0,
        min_adherence: float = 99.0,
    ):
        self.freshness = FreshnessMonitor(max_age_hours=max_freshness_hours)
        self.completeness = CompletenessMonitor(min_percent=min_completeness)
        self.accuracy = AccuracyMonitor(min_percent=min_accuracy)
        self.adherence = ContractAdherenceMonitor(min_percent=min_adherence)

    def calculate(
        self,
        batch_id: str,
        dataset_name: str,
        source: str,
        df: pd.DataFrame,
        validation_result: ValidationResult,
        ingestion_time: Optional[datetime] = None,
        duration: float = 0.0,
        pipeline_status: str = "SUCCESS",
    ) -> BatchQualityMetrics:
        """
        Calculate all quality metrics for a batch.

        Args:
            batch_id: Batch identifier.
            dataset_name: Logical dataset name.
            source: Source type.
            df: The raw/validated DataFrame.
            validation_result: Result from contract validation.
            ingestion_time: When the data was ingested (for freshness).
            duration: Pipeline processing duration.
            pipeline_status: Final pipeline status.

        Returns:
            BatchQualityMetrics instance.
        """
        now = utc_now()
        ingest_time = ingestion_time or now

        freshness_score = self.freshness.calculate_score(ingest_time)
        completeness_score = self.completeness.calculate_score(df)
        accuracy_score = self.accuracy.calculate_score(validation_result)

        # Record adherence for this batch
        self.adherence.record_batch(
            batch_id=batch_id,
            passed=validation_result.is_valid,
        )
        adherence_score = self.adherence.calculate_score()

        metrics = BatchQualityMetrics(
            batch_id=batch_id,
            dataset_name=dataset_name,
            source=source,
            timestamp=now.isoformat(),
            record_count=validation_result.total_records,
            valid_count=validation_result.valid_records,
            invalid_count=validation_result.invalid_records,
            quarantined_count=validation_result.invalid_records,
            freshness_score=freshness_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            contract_adherence_score=adherence_score,
            pipeline_status=pipeline_status,
            processing_duration_seconds=duration,
        )

        logger.info(
            "Quality metrics | batch=%s overall=%.1f fresh=%.1f complete=%.1f "
            "accuracy=%.1f adherence=%.1f",
            batch_id, metrics.overall_score, freshness_score,
            completeness_score, accuracy_score, adherence_score,
        )

        return metrics
