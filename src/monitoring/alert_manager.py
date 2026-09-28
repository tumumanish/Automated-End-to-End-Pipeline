"""
Module: alert_manager
Purpose:
    Detect threshold breaches in quality metrics and generate alerts.
    Supports multiple severity levels and configurable thresholds.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Optional

from src.monitoring.quality_metrics import BatchQualityMetrics
from src.utils.logger import get_logger
from src.utils.timestamps import utc_now

logger = get_logger("monitoring.alerts")


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class Alert:
    """Represents a quality or pipeline alert."""
    severity: str
    category: str
    message: str
    timestamp: str
    batch_id: str = ""
    dataset_name: str = ""
    metric_name: str = ""
    metric_value: float = 0.0
    threshold_value: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


class AlertManager:
    """
    Evaluates quality metrics against configured thresholds and
    generates alerts when breaches are detected.
    """

    def __init__(
        self,
        freshness_warning: float = 50.0,
        freshness_critical: float = 25.0,
        completeness_warning: float = 95.0,
        completeness_critical: float = 85.0,
        accuracy_warning: float = 98.0,
        accuracy_critical: float = 90.0,
        adherence_warning: float = 99.0,
        adherence_critical: float = 95.0,
    ):
        self._thresholds = {
            "freshness": {"warning": freshness_warning, "critical": freshness_critical},
            "completeness": {"warning": completeness_warning, "critical": completeness_critical},
            "accuracy": {"warning": accuracy_warning, "critical": accuracy_critical},
            "contract_adherence": {"warning": adherence_warning, "critical": adherence_critical},
        }
        self._alerts: List[Alert] = []

    def evaluate(self, metrics: BatchQualityMetrics) -> List[Alert]:
        """
        Evaluate batch quality metrics and generate alerts for threshold breaches.

        Args:
            metrics: The quality metrics to evaluate.

        Returns:
            List of Alert objects generated.
        """
        new_alerts: List[Alert] = []

        checks = [
            ("freshness", metrics.freshness_score),
            ("completeness", metrics.completeness_score),
            ("accuracy", metrics.accuracy_score),
            ("contract_adherence", metrics.contract_adherence_score),
        ]

        for metric_name, value in checks:
            thresholds = self._thresholds[metric_name]

            if value < thresholds["critical"]:
                alert = self._create_alert(
                    severity=AlertSeverity.CRITICAL,
                    category="data_quality",
                    metric_name=metric_name,
                    value=value,
                    threshold=thresholds["critical"],
                    metrics=metrics,
                )
                new_alerts.append(alert)

            elif value < thresholds["warning"]:
                alert = self._create_alert(
                    severity=AlertSeverity.WARNING,
                    category="data_quality",
                    metric_name=metric_name,
                    value=value,
                    threshold=thresholds["warning"],
                    metrics=metrics,
                )
                new_alerts.append(alert)

        # Pipeline failure alert
        if metrics.pipeline_status == "FAILED":
            alert = Alert(
                severity=AlertSeverity.CRITICAL,
                category="pipeline",
                message=f"Pipeline execution FAILED for batch {metrics.batch_id}",
                timestamp=utc_now().isoformat(),
                batch_id=metrics.batch_id,
                dataset_name=metrics.dataset_name,
                metric_name="pipeline_status",
            )
            new_alerts.append(alert)

        self._alerts.extend(new_alerts)

        for alert in new_alerts:
            log_fn = logger.critical if alert.severity == AlertSeverity.CRITICAL else logger.warning
            log_fn(
                "ALERT [%s] %s | batch=%s metric=%s value=%.1f threshold=%.1f",
                alert.severity, alert.message, alert.batch_id,
                alert.metric_name, alert.metric_value, alert.threshold_value,
            )

        return new_alerts

    def _create_alert(
        self,
        severity: AlertSeverity,
        category: str,
        metric_name: str,
        value: float,
        threshold: float,
        metrics: BatchQualityMetrics,
    ) -> Alert:
        return Alert(
            severity=severity.value,
            category=category,
            message=f"{metric_name} score ({value:.1f}) below {severity.value} threshold ({threshold:.1f})",
            timestamp=utc_now().isoformat(),
            batch_id=metrics.batch_id,
            dataset_name=metrics.dataset_name,
            metric_name=metric_name,
            metric_value=value,
            threshold_value=threshold,
        )

    def get_alerts(self, severity: Optional[str] = None) -> List[Alert]:
        """Get all recorded alerts, optionally filtered by severity."""
        if severity:
            return [a for a in self._alerts if a.severity == severity]
        return list(self._alerts)

    def get_recent_alerts(self, limit: int = 20) -> List[Alert]:
        """Get the most recent alerts."""
        return list(reversed(self._alerts[-limit:]))

    def clear_alerts(self) -> None:
        """Clear all stored alerts."""
        self._alerts.clear()
