"""Tests for the auth provider abstraction."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from browser_mcp.auth.provider import PlaywrightAuthProvider

pytestmark = pytest.mark.unit


class TestPlaywrightAuthProvider:
    @pytest.fixture
    def provider(self) -> PlaywrightAuthProvider:
        return PlaywrightAuthProvider()

    async def test_inject_cookies(self, provider: PlaywrightAuthProvider) -> None:
        context = AsyncMock()
        await provider.inject_cookies(context, [{"name": "a", "value": "1"}])
        context.add_cookies.assert_awaited_once_with([{"name": "a", "value": "1"}])

    async def test_inject_headers(self, provider: PlaywrightAuthProvider) -> None:
        context = AsyncMock()
        await provider.inject_headers(context, {"X": "Y"})
        context.set_extra_http_headers.assert_awaited_once_with({"X": "Y"})

    async def test_extract_storage_state(self, provider: PlaywrightAuthProvider) -> None:
        context = AsyncMock()
        context.storage_state = AsyncMock(return_value={"cookies": [], "origins": {}})
        state = await provider.extract_storage_state(context)
        assert state == {"cookies": [], "origins": {}}

    async def test_apply_storage_state(self, provider: PlaywrightAuthProvider) -> None:
        context = AsyncMock()
        context.add_cookies = AsyncMock()
        context.goto = AsyncMock()
        context.evaluate = AsyncMock()
        state = {
            "cookies": [{"name": "a", "value": "1"}],
            "origins": {"https://example.com": {"localStorage": {"k": "v"}}},
        }
        await provider.apply_storage_state(context, state)
        context.add_cookies.assert_awaited_once_with([{"name": "a", "value": "1"}])
