"""Tests for the auth strategy architecture."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from browser_mcp.errors import LoginFailedError, UnsupportedAuthStrategyError
from browser_mcp.auth.strategies.base import BaseAuthStrategy
from browser_mcp.auth.strategies.cookie import CookieAuthStrategy
from browser_mcp.auth.strategies.form import FormAuthStrategy
from browser_mcp.auth.strategies.header import HeaderAuthStrategy
from browser_mcp.auth.strategies.registry import AuthStrategyRegistry

pytestmark = pytest.mark.unit


class TestAuthStrategyRegistry:
    def test_register_and_get(self) -> None:
        registry = AuthStrategyRegistry()
        strategy = MagicMock(spec=BaseAuthStrategy)
        strategy.name = "custom"
        registry.register(strategy)
        assert registry.get("custom") is strategy

    def test_oauth_reserved_raises(self) -> None:
        registry = AuthStrategyRegistry()
        with pytest.raises(UnsupportedAuthStrategyError, match="OAuth"):
            registry.get("oauth")

    def test_unknown_strategy_raises(self) -> None:
        registry = AuthStrategyRegistry()
        with pytest.raises(UnsupportedAuthStrategyError, match="not registered"):
            registry.get("unknown")

    def test_names(self) -> None:
        registry = AuthStrategyRegistry()
        registry.register(FormAuthStrategy())
        registry.register(CookieAuthStrategy())
        names = registry.names()
        assert "form" in names
        assert "cookie" in names


class TestFormAuthStrategy:
    async def test_execute(self) -> None:
        strategy = FormAuthStrategy()
        page = MagicMock()
        page.goto = AsyncMock()
        page.fill = AsyncMock()
        page.click = AsyncMock()
        page.wait_for_load_state = AsyncMock()
        page.url = "https://example.com/dashboard"

        from browser_mcp.auth.models import AuthCredentials
        creds = AuthCredentials(
            username="user",
            password="pass",
            url="https://example.com/login",
        )

        result = await strategy.execute(page, creds)
        assert result["success"] is True
        assert result["url"] == "https://example.com/dashboard"


class TestCookieAuthStrategy:
    async def test_execute(self) -> None:
        strategy = CookieAuthStrategy()
        context = MagicMock()
        context.add_cookies = AsyncMock()

        from browser_mcp.auth.models import AuthCredentials
        creds = AuthCredentials(
            url="https://example.com",
            cookies={"session": "abc"},
        )

        result = await strategy.execute(context, creds)
        assert result["success"] is True
        assert result["cookies_injected"] == 1


class TestHeaderAuthStrategy:
    async def test_execute(self) -> None:
        strategy = HeaderAuthStrategy()
        context = MagicMock()
        context.set_extra_http_headers = AsyncMock()

        from browser_mcp.auth.models import AuthCredentials
        creds = AuthCredentials(
            url="https://example.com",
            headers={"Authorization": "Bearer token"},
        )

        result = await strategy.execute(context, creds)
        assert result["success"] is True
        assert "Authorization" in result["headers_injected"]
