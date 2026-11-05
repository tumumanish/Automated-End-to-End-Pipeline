"""
Module: retry
Purpose:
    Retry helpers with exponential backoff for transient failures in
    ingestion adapters and external service calls.

Usage::

    from src.utils.retry import call_with_retry

    response = call_with_retry(
        lambda: requests.get(url, timeout=10),
        max_attempts=3,
        exceptions=(requests.exceptions.ConnectionError,),
    )
"""

from __future__ import annotations

import random
import time
from functools import wraps
from typing import Any, Callable, Sequence, Type

from src.utils.logger import get_logger

logger = get_logger("pipeline")

DEFAULT_EXCEPTIONS: tuple[Type[BaseException], ...] = (Exception,)


def _delay_for_attempt(
    attempt: int,
    base_delay: float,
    backoff: float,
    max_delay: float,
    jitter: float,
) -> float:
    """Compute the sleep duration before the next attempt (attempt is 1-based)."""
    delay = min(max_delay, base_delay * (backoff ** (attempt - 1)))
    if jitter > 0:
        delay += random.uniform(0, jitter)
    return delay


def call_with_retry(
    func: Callable[[], Any],
    *,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    backoff: float = 2.0,
    jitter: float = 0.0,
    exceptions: Sequence[Type[BaseException]] | None = None,
) -> Any:
    """
    Call ``func`` and retry on the given exception types.

    Args:
        func: Zero-argument callable to execute.
        max_attempts: Total attempts (including the first). Must be >= 1.
        base_delay: Initial delay in seconds.
        max_delay: Upper bound for a single delay.
        backoff: Multiplier applied after each failed attempt.
        jitter: Maximum random seconds added to each delay.
        exceptions: Exception types that trigger a retry.

    Returns:
        The return value of ``func``.

    Raises:
        ValueError: If ``max_attempts`` is less than 1.
        Exception: The last exception if all attempts fail.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    retry_on = tuple(exceptions) if exceptions else DEFAULT_EXCEPTIONS

    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except retry_on as exc:
            if attempt >= max_attempts:
                raise
            delay = _delay_for_attempt(attempt, base_delay, backoff, max_delay, jitter)
            logger.warning(
                "Attempt %d/%d failed (%s: %s). Retrying in %.2fs.",
                attempt,
                max_attempts,
                type(exc).__name__,
                exc,
                delay,
            )
            time.sleep(delay)


def retry(
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    backoff: float = 2.0,
    jitter: float = 0.0,
    exceptions: Sequence[Type[BaseException]] | None = None,
):
    """
    Decorator form of :func:`call_with_retry`.

    Example::

        @retry(max_attempts=3, exceptions=(ConnectionError,))
        def fetch():
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return call_with_retry(
                lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                backoff=backoff,
                jitter=jitter,
                exceptions=exceptions,
            )

        return wrapper

    return decorator
