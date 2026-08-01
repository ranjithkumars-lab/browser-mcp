"""Tests for the AuthManager facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from browser_mcp.auth.manager import AuthManager
from browser_mcp.auth.models import AuthCredentials, AuthMetadata, AuthSession, AuthState
from browser_mcp.auth.storage.encryption import AuthEncryptionEngine
from browser_mcp.auth.storage.manager import AuthStorageManager
from browser_mcp.auth.strategies.base import BaseAuthStrategy
from browser_mcp.auth.strategies.registry import AuthStrategyRegistry
from browser_mcp.errors import LoginFailedError

pytestmark = pytest.mark.unit


def _make_manager(tmp_path: Any) -> AuthManager:
    registry = AuthStrategyRegistry()
    storage = AuthStorageManager(
        directory=tmp_path,
        encryption=AuthEncryptionEngine(key="test-key"),
    )
    provider = MagicMock()
    event_bus = MagicMock()
    event_bus.publish = AsyncMock()
    return AuthManager(registry=registry, storage=storage, provider=provider, event_bus=event_bus)


class TestAuthManagerLogin:
    async def test_login_success(self, tmp_path: Path) -> None:
        manager = _make_manager(tmp_path)
        strategy = MagicMock(spec=BaseAuthStrategy)
        strategy.name = "form"
        strategy.execute = AsyncMock(
            return_value={"success": True, "url": "https://example.com/dashboard"}
        )
        manager.register_strategy(strategy)

        context = MagicMock()
        creds = AuthCredentials(
            username="user",
            password="pass",
            url="https://example.com/login",
            metadata={"context_id": "ctx-1", "session_id": "ses-1"},
        )

        result = await manager.login(context, creds)
        assert result["success"] is True
        assert result["session"]["session"]["session_id"] == "ses-1"
        assert result["session"]["session"]["authenticated"] is True

    async def test_login_failure(self, tmp_path: Path) -> None:
        manager = _make_manager(tmp_path)
        strategy = MagicMock(spec=BaseAuthStrategy)
        strategy.name = "form"
        strategy.execute = AsyncMock(side_effect=Exception("network error"))
        manager.register_strategy(strategy)

        context = MagicMock()
        creds = AuthCredentials(
            username="user",
            password="pass",
            url="https://example.com/login",
            metadata={"context_id": "ctx-1", "session_id": "ses-1"},
        )

        with pytest.raises(LoginFailedError, match="network error"):
            await manager.login(context, creds)


class TestAuthManagerStatePersistence:
    async def test_save_and_load_state(self, tmp_path: Path) -> None:
        manager = _make_manager(tmp_path)
        session = AuthSession(
            session_id="ses-1",
            context_id="ctx-1",
            authenticated=True,
            metadata=AuthMetadata(strategy="form", context_id="ctx-1", session_id="ses-1"),
        )
        state = AuthState(session=session)
        save_result = await manager.save_state("ctx-1", "ses-1", state)
        assert save_result["success"] is True

        loaded = await manager.load_state("ctx-1")
        assert loaded.session.session_id == "ses-1"
        assert loaded.session.authenticated is True


class TestAuthManagerSetHeaders:
    async def test_set_headers(self, tmp_path: Path) -> None:
        manager = _make_manager(tmp_path)
        context = MagicMock()
        manager._provider.inject_headers = AsyncMock()

        result = await manager.set_headers(
            context, {"X": "Y"}, context_id="ctx-1", session_id="ses-1"
        )
        assert result["success"] is True
        assert "X" in result["headers_injected"]
