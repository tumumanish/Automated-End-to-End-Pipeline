"""
Module: pipeline_metrics
Purpose:
    Track pipeline execution metrics — duration, throughput, success rate.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional

from src.utils.logger import get_logger
from src.utils.timestamps import utc_now

logger = get_logger("monitoring.pipeline")


@dataclass
class PipelineExecutionMetric:
    """Metrics for a single pipeline execution."""
    pipeline_name: str
    execution_id: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: float = 0.0
    records_extracted: int = 0
    records_valid: int = 0
    records_invalid: int = 0
    records_transformed: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


import json
from pathlib import Path
from src.utils.file_utils import get_project_root


class PipelineMetricsTracker:
    """
    Tracks and aggregates pipeline execution metrics across runs.
    """

    def __init__(self, load_persisted: bool = False):
        self._load_persisted = load_persisted
        self._executions: List[PipelineExecutionMetric] = []

    def _load_persisted_metrics(self) -> List[PipelineExecutionMetric]:
        try:
            log_dir = get_project_root() / "logs" / "pipeline"
            if not log_dir.exists():
                return []
            metrics = []
            for f in sorted(log_dir.glob("*_metrics.json"), key=lambda p: p.stat().st_mtime):
                try:
                    with open(f, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                    metrics.append(PipelineExecutionMetric(**data))
                except Exception:
                    continue
            return metrics
        except Exception:
            return []

    def record_execution(
        self,
        pipeline_name: str,
        execution_id: str,
        status: str,
        started_at: str,
        duration: float,
        records_extracted: int = 0,
        records_valid: int = 0,
        records_invalid: int = 0,
        records_transformed: int = 0,
        error_message: Optional[str] = None,
    ) -> PipelineExecutionMetric:
        """
        Record a pipeline execution metric.

        Returns:
            The created PipelineExecutionMetric.
        """
        metric = PipelineExecutionMetric(
            pipeline_name=pipeline_name,
            execution_id=execution_id,
            status=status,
            started_at=started_at,
            completed_at=utc_now().isoformat(),
            duration_seconds=round(duration, 2),
            records_extracted=records_extracted,
            records_valid=records_valid,
            records_invalid=records_invalid,
            records_transformed=records_transformed,
            error_message=error_message,
        )
        self._executions.append(metric)

        logger.info(
            "Pipeline metric | pipeline=%s exec=%s status=%s duration=%.2fs",
            pipeline_name, execution_id, status, duration,
        )
        return metric

    def get_executions(
        self,
        pipeline_name: Optional[str] = None,
        limit: int = 50,
        include_persisted: Optional[bool] = None,
    ) -> List[PipelineExecutionMetric]:
        """Get recent pipeline executions, optionally filtered by name."""
        should_load = self._load_persisted if include_persisted is None else include_persisted
        all_metrics = list(self._executions)
        if should_load:
            persisted = self._load_persisted_metrics()
            seen = {e.execution_id for e in all_metrics}
            for p in persisted:
                if p.execution_id not in seen:
                    all_metrics.append(p)
                    seen.add(p.execution_id)

        results = all_metrics
        if pipeline_name:
            results = [e for e in results if e.pipeline_name == pipeline_name]
        return list(reversed(results[-limit:]))

    def get_success_rate(self, pipeline_name: Optional[str] = None) -> float:
        """Calculate the success rate across recorded executions."""
        executions = self._executions
        if pipeline_name:
            executions = [e for e in executions if e.pipeline_name == pipeline_name]

        if not executions:
            return 100.0

        successes = sum(1 for e in executions if e.status == "SUCCESS")
        return round(100.0 * successes / len(executions), 2)

    def get_avg_duration(self, pipeline_name: Optional[str] = None) -> float:
        """Calculate average execution duration in seconds."""
        executions = self._executions
        if pipeline_name:
            executions = [e for e in executions if e.pipeline_name == pipeline_name]

        if not executions:
            return 0.0

        total = sum(e.duration_seconds for e in executions)
        return round(total / len(executions), 2)

    def get_throughput(self, pipeline_name: Optional[str] = None) -> float:
        """Calculate average records processed per execution."""
        executions = self._executions
        if pipeline_name:
            executions = [e for e in executions if e.pipeline_name == pipeline_name]

        if not executions:
            return 0.0

        total_records = sum(e.records_extracted for e in executions)
        return round(total_records / len(executions), 2)
