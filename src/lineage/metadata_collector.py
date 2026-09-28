"""
Module: metadata_collector
Purpose:
    Collect schema and pipeline metadata about datasets at each stage.
    Provides structured metadata that enriches lineage events.
"""

from dataclasses import dataclass, asdict
from typing import Optional

import pandas as pd

from src.utils.logger import get_logger
from src.utils.timestamps import utc_now

logger = get_logger("lineage")


@dataclass
class DatasetMetadata:
    """Metadata snapshot of a dataset at a pipeline stage."""
    dataset_name: str
    stage: str
    row_count: int
    column_count: int
    columns: list
    column_types: dict
    null_counts: dict
    memory_usage_bytes: int
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PipelineMetadata:
    """Metadata about a pipeline execution."""
    execution_id: str
    pipeline_name: str
    source_type: str
    dataset_name: str
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    status: str = "RUNNING"
    stages_completed: int = 0
    total_stages: int = 0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class MetadataCollector:
    """
    Collects metadata about datasets and pipeline executions.

    Designed to be called at each pipeline stage to create a metadata
    trail alongside lineage events.
    """

    @staticmethod
    def collect_dataset_metadata(
        df: pd.DataFrame,
        dataset_name: str,
        stage: str,
    ) -> DatasetMetadata:
        """
        Collect metadata about a DataFrame at a specific pipeline stage.

        Args:
            df: The DataFrame to analyse.
            dataset_name: Logical dataset name.
            stage: Current pipeline stage name.

        Returns:
            DatasetMetadata instance.
        """
        meta = DatasetMetadata(
            dataset_name=dataset_name,
            stage=stage,
            row_count=len(df),
            column_count=len(df.columns),
            columns=list(df.columns),
            column_types={col: str(dtype) for col, dtype in df.dtypes.items()},
            null_counts={col: int(df[col].isna().sum()) for col in df.columns},
            memory_usage_bytes=int(df.memory_usage(deep=True).sum()),
            timestamp=utc_now().isoformat(),
        )

        logger.debug(
            "Dataset metadata | dataset=%s stage=%s rows=%d cols=%d",
            dataset_name, stage, meta.row_count, meta.column_count,
        )
        return meta

    @staticmethod
    def create_pipeline_metadata(
        execution_id: str,
        pipeline_name: str,
        source_type: str,
        dataset_name: str,
        total_stages: int,
    ) -> PipelineMetadata:
        """
        Create initial pipeline execution metadata.

        Args:
            execution_id: Unique execution identifier.
            pipeline_name: Pipeline name.
            source_type: Data source type.
            dataset_name: Target dataset name.
            total_stages: Total number of stages in the pipeline.

        Returns:
            PipelineMetadata instance.
        """
        return PipelineMetadata(
            execution_id=execution_id,
            pipeline_name=pipeline_name,
            source_type=source_type,
            dataset_name=dataset_name,
            started_at=utc_now().isoformat(),
            total_stages=total_stages,
        )

    @staticmethod
    def finalise_pipeline_metadata(
        meta: PipelineMetadata,
        status: str,
        duration: float,
        stages_completed: int,
        error: Optional[str] = None,
    ) -> PipelineMetadata:
        """
        Finalise pipeline metadata after execution completes.

        Args:
            meta: The PipelineMetadata to update.
            status: Final status (SUCCESS, FAILED).
            duration: Total duration in seconds.
            stages_completed: Number of stages completed.
            error: Error message if failed.

        Returns:
            Updated PipelineMetadata.
        """
        meta.completed_at = utc_now().isoformat()
        meta.duration_seconds = round(duration, 2)
        meta.status = status
        meta.stages_completed = stages_completed
        meta.error = error
        return meta
