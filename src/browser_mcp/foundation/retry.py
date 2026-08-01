"""Retry policy for transient failure handling.

Provides a shared :class:`RetryPolicy` used by form automation,
scraping, authentication, and other phases that need resilient
retry-with-backoff semantics.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from enterprise_mcp.utils.errors import EnterpriseMCPError

T = TypeVar("T")

__all__ = ["RetryConfig", "RetryError", "RetryPolicy"]


class RetryError(EnterpriseMCPError):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause
        if cause is not None:
            self.__cause__ = cause


class RetryConfig:
    """Configuration for retry behaviour."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay_ms: float = 100.0,
        backoff_factor: float = 2.0,
        max_delay_ms: float = 5000.0,
        retry_on: tuple[type[Exception], ...] = (),
    ) -> None:
        self.max_attempts = max_attempts
        self.initial_delay_ms = initial_delay_ms
        self.backoff_factor = backoff_factor
        self.max_delay_ms = max_delay_ms
        self.retry_on = retry_on


class RetryPolicy:
    """Executes an async callable with retry and exponential backoff."""

    def __init__(self, config: RetryConfig | None = None) -> None:
        self._config = config or RetryConfig()

    async def run(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        """Execute ``func`` with retry logic.

        Raises
        ------
        RetryError
            When all attempts are exhausted.
        """
        delay_ms = self._config.initial_delay_ms
        last_exc: Exception | None = None

        for attempt in range(1, self._config.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                if not self._is_retryable(exc):
                    raise
                if attempt >= self._config.max_attempts:
                    break
                await asyncio.sleep(delay_ms / 1000.0)
                delay_ms = min(delay_ms * self._config.backoff_factor, self._config.max_delay_ms)

        raise RetryError(
            f"Operation failed after {self._config.max_attempts} attempt(s): {last_exc}"
        )

    def _is_retryable(self, exc: Exception) -> bool:
        if not self._config.retry_on:
            return True
        return any(isinstance(exc, err_type) for err_type in self._config.retry_on)
