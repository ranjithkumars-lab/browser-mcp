"""Tests for the auth storage subsystem."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from browser_mcp.errors import StateLoadError, StateSaveError
from browser_mcp.auth.models import AuthMetadata, AuthSession, AuthState
from browser_mcp.auth.storage.encryption import AuthEncryptionEngine
from browser_mcp.auth.storage.manager import AuthStorageManager
from browser_mcp.auth.storage.serializer import StateSerializer
from browser_mcp.auth.storage.ttl import TTLValidator

pytestmark = pytest.mark.unit


class TestStateSerializer:
    def test_round_trip(self) -> None:
        ser = StateSerializer()
        original = {"a": 1, "b": [1, 2, 3]}
        payload = ser.serialize(original)
        assert ser.deserialize(payload) == original


class TestAuthEncryptionEngine:
    def test_encrypt_decrypt_round_trip(self) -> None:
        engine = AuthEncryptionEngine(key="secret-key")
        ct = engine.encrypt("hello world")
        assert engine.decrypt(ct) == "hello world"

    def test_plaintext_fallback(self) -> None:
        engine = AuthEncryptionEngine(allow_plaintext=True)
        pt = engine.encrypt("plain text")
        assert engine.decrypt(pt) == "plain text"


class TestTTLValidator:
    def test_valid_cookie_without_expires(self) -> None:
        validator = TTLValidator()
        assert validator.is_cookie_valid({"name": "a"}) is True

    def test_valid_future_expiry(self) -> None:
        from datetime import UTC, datetime, timedelta
        validator = TTLValidator()
        future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
        assert validator.is_cookie_valid({"name": "a", "expires": future}) is True

    def test_expired_cookie(self) -> None:
        from datetime import UTC, datetime, timedelta
        validator = TTLValidator()
        past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        assert validator.is_cookie_valid({"name": "a", "expires": past}) is False


class TestAuthStorageManager:
    @pytest.fixture
    def manager(self, tmp_path: Path) -> AuthStorageManager:
        return AuthStorageManager(
            directory=tmp_path,
            encryption=AuthEncryptionEngine(key="test-key"),
        )

    async def test_save_and_load(self, manager: AuthStorageManager) -> None:
        state = AuthState(
            session=AuthSession(session_id="ses-1", context_id="ctx-1"),
        )
        path = await manager.save("ctx-1", state)
        assert path.exists()
        loaded = await manager.load("ctx-1")
        assert loaded.session.session_id == "ses-1"

    async def test_load_missing_raises(self, manager: AuthStorageManager) -> None:
        with pytest.raises(StateLoadError, match="no auth state"):
            await manager.load("missing")

    async def test_delete(self, manager: AuthStorageManager) -> None:
        state = AuthState(session=AuthSession(session_id="ses-1", context_id="ctx-1"))
        await manager.save("ctx-1", state)
        manager.delete("ctx-1")
        assert not manager._path_for("ctx-1").exists()
