"""
Unit Tests: Retry Utilities

Covers exponential backoff, attempt limits, and the decorator form.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import retry as retry_module
from src.utils.retry import call_with_retry, retry


class TestCallWithRetry:
    def test_no_retry_needed(self):
        calls = []

        def func():
            calls.append(1)
            return "ok"

        assert call_with_retry(func) == "ok"
        assert len(calls) == 1

    def test_retries_until_success(self, monkeypatch):
        monkeypatch.setattr(retry_module.time, "sleep", lambda _: None)
        calls = []

        def func():
            calls.append(1)
            if len(calls) < 3:
                raise ConnectionError("transient")
            return "ok"

        assert call_with_retry(func, max_attempts=3, exceptions=(ConnectionError,)) == "ok"
        assert len(calls) == 3

    def test_raises_after_max_attempts(self, monkeypatch):
        monkeypatch.setattr(retry_module.time, "sleep", lambda _: None)
        calls = []

        def func():
            calls.append(1)
            raise TimeoutError("down")

        with pytest.raises(TimeoutError):
            call_with_retry(func, max_attempts=3, exceptions=(TimeoutError,))
        assert len(calls) == 3

    def test_non_retryable_exception_is_not_retried(self, monkeypatch):
        monkeypatch.setattr(retry_module.time, "sleep", lambda _: None)
        calls = []

        def func():
            calls.append(1)
            raise ValueError("bad input")

        with pytest.raises(ValueError):
            call_with_retry(func, max_attempts=3, exceptions=(ConnectionError,))
        assert len(calls) == 1

    def test_exponential_backoff_delays(self, monkeypatch):
        sleeps = []
        monkeypatch.setattr(retry_module.time, "sleep", lambda seconds: sleeps.append(seconds))

        def func():
            raise ConnectionError("down")

        with pytest.raises(ConnectionError):
            call_with_retry(
                func,
                max_attempts=4,
                base_delay=1.0,
                backoff=2.0,
                max_delay=10.0,
                exceptions=(ConnectionError,),
            )

        # Sleeps happen between attempts only: 4 attempts -> 3 sleeps.
        assert sleeps == [1.0, 2.0, 4.0]

    def test_max_delay_caps_backoff(self, monkeypatch):
        sleeps = []
        monkeypatch.setattr(retry_module.time, "sleep", lambda seconds: sleeps.append(seconds))

        def func():
            raise ConnectionError("down")

        with pytest.raises(ConnectionError):
            call_with_retry(
                func,
                max_attempts=5,
                base_delay=1.0,
                backoff=10.0,
                max_delay=5.0,
                exceptions=(ConnectionError,),
            )

        assert sleeps == [1.0, 5.0, 5.0, 5.0]

    def test_invalid_max_attempts(self):
        with pytest.raises(ValueError):
            call_with_retry(lambda: None, max_attempts=0)


class TestRetryDecorator:
    def test_decorator_retries(self, monkeypatch):
        monkeypatch.setattr(retry_module.time, "sleep", lambda _: None)
        calls = []

        @retry(max_attempts=2, base_delay=0, exceptions=(ConnectionError,))
        def func(value):
            calls.append(value)
            if len(calls) == 1:
                raise ConnectionError("transient")
            return value * 2

        assert func(5) == 10
        assert calls == [5, 5]

    def test_decorator_preserves_metadata(self):
        @retry(max_attempts=2)
        def documented():
            """Docstring."""

        assert documented.__name__ == "documented"
        assert documented.__doc__ == "Docstring."
