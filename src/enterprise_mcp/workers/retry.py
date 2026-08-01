"""Retry policy."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["RetryPolicy"]


class RetryPolicy(BaseModel):
    """Configuration for automatic retries."""

    max_attempts: int = Field(default=3, ge=1)
    base_delay_seconds: float = Field(default=1.0, ge=0.0)
    max_delay_seconds: float = Field(default=60.0, ge=0.0)
    exponential_backoff: bool = True
    retry_on: tuple[str, ...] = ("ConnectionError", "TimeoutError")
