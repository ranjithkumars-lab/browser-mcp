"""Tests for the RetryPolicy foundation module."""

from __future__ import annotations

import asyncio

import pytest

from browser_mcp.foundation.retry import RetryConfig, RetryError, RetryPolicy


class TestRetryPolicy:
    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self) -> None:
        call_count = 0

        async def success() -> int:
            nonlocal call_count
            call_count += 1
            return call_count

        policy = RetryPolicy(RetryConfig(max_attempts=3))
        result = await policy.run(success)
        assert result == 1
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self) -> None:
        call_count = 0

        async def flaky() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("transient")
            return call_count

        policy = RetryPolicy(RetryConfig(max_attempts=5, initial_delay_ms=10))
        result = await policy.run(flaky)
        assert result == 3
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_exhausts_retries_and_raises(self) -> None:
        async def always_fails() -> int:
            raise RuntimeError("permanent")

        policy = RetryPolicy(RetryConfig(max_attempts=2, initial_delay_ms=10))
        with pytest.raises(RetryError):
            await policy.run(always_fails)

    @pytest.mark.asyncio
    async def test_non_retryable_error_raises_immediately(self) -> None:
        call_count = 0

        async def fails() -> int:
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        policy = RetryPolicy(
            RetryConfig(max_attempts=5, initial_delay_ms=10, retry_on=(RuntimeError,))
        )
        with pytest.raises(ValueError):
            await policy.run(fails)

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_backoff_delay(self) -> None:
        call_count = 0

        async def flaky() -> int:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("transient")
            return call_count

        policy = RetryPolicy(
            RetryConfig(max_attempts=5, initial_delay_ms=50, backoff_factor=2.0)
        )
        start = asyncio.get_event_loop().time()
        result = await policy.run(flaky)
        elapsed = asyncio.get_event_loop().time() - start
        assert result == 3
        assert elapsed >= 0.05  # at least one delay

    def test_retry_config_defaults(self) -> None:
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay_ms == 100.0
        assert config.backoff_factor == 2.0
        assert config.max_delay_ms == 5000.0
        assert config.retry_on == ()

    def test_retry_config_custom(self) -> None:
        config = RetryConfig(
            max_attempts=5,
            initial_delay_ms=200,
            backoff_factor=3.0,
            max_delay_ms=10000,
            retry_on=(ConnectionError,),
        )
        assert config.max_attempts == 5
        assert config.initial_delay_ms == 200
        assert config.backoff_factor == 3.0
        assert config.max_delay_ms == 10000
        assert config.retry_on == (ConnectionError,)


class TestRetryError:
    def test_retry_error_message(self) -> None:
        err = RetryError("all attempts failed")
        assert "all attempts failed" in str(err)

    def test_retry_error_with_cause(self) -> None:
        cause = RuntimeError("root")
        err = RetryError("failed", cause=cause)
        assert err.__cause__ is cause
