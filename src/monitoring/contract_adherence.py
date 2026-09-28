"""
Module: contract_adherence
Purpose:
    Monitor contract adherence — does data satisfy registered contracts?
    Tracks the percentage of batches that fully pass contract validation.
"""

from typing import List

from src.utils.logger import get_logger

logger = get_logger("monitoring.contract_adherence")


class ContractAdherenceMonitor:
    """
    Tracks contract adherence across batches by maintaining a history
    of validation outcomes and computing the pass rate.
    """

    def __init__(self, min_percent: float = 99.0):
        """
        Args:
            min_percent: Minimum acceptable adherence percentage.
        """
        self._min_percent = min_percent
        self._history: List[dict] = []

    def record_batch(self, batch_id: str, passed: bool, details: str = "") -> None:
        """
        Record a batch validation outcome.

        Args:
            batch_id: The batch identifier.
            passed: Whether the batch fully passed contract validation.
            details: Optional details about the outcome.
        """
        self._history.append({
            "batch_id": batch_id,
            "passed": passed,
            "details": details,
        })

    def calculate_score(self) -> float:
        """
        Calculate contract adherence score across all recorded batches.

        Score = (passed_batches / total_batches) * 100

        Returns:
            Adherence score (0-100).
        """
        if not self._history:
            return 100.0

        passed = sum(1 for h in self._history if h["passed"])
        total = len(self._history)
        score = round(100.0 * passed / total, 2)

        logger.info(
            "Contract adherence | total_batches=%d passed=%d failed=%d score=%.1f",
            total, passed, total - passed, score,
        )
        return score

    def calculate_from_counts(self, total_batches: int, passed_batches: int) -> float:
        """Calculate adherence from raw counts."""
        if total_batches == 0:
            return 100.0
        return round(100.0 * passed_batches / total_batches, 2)

    def is_adherent(self) -> bool:
        """Check whether adherence meets the minimum threshold."""
        return self.calculate_score() >= self._min_percent

    def get_failed_batches(self) -> List[dict]:
        """Return list of batches that failed contract validation."""
        return [h for h in self._history if not h["passed"]]

    def reset(self) -> None:
        """Clear batch history."""
        self._history.clear()
