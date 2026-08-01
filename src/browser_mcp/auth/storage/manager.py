"""High-level file I/O for persisted auth states."""

from __future__ import annotations

from pathlib import Path

from browser_mcp.errors import StateLoadError, StateSaveError
from browser_mcp.auth.models import AuthState
from browser_mcp.auth.storage.encryption import AuthEncryptionEngine
from browser_mcp.auth.storage.serializer import StateSerializer
from browser_mcp.auth.storage.ttl import TTLValidator

__all__ = ["AuthStorageManager"]


class AuthStorageManager:
    """Manage persistent auth state files on disk."""

    def __init__(
        self,
        directory: str | Path,
        encryption: AuthEncryptionEngine,
        serializer: StateSerializer | None = None,
        ttl: TTLValidator | None = None,
    ) -> None:
        self._directory = Path(directory).expanduser()
        self._directory.mkdir(parents=True, exist_ok=True)
        self._encryption = encryption
        self._serializer = serializer or StateSerializer()
        self._ttl = ttl or TTLValidator()

    def _path_for(self, context_id: str) -> Path:
        return self._directory / f"{context_id}.auth"

    async def save(self, context_id: str, state: AuthState) -> Path:
        path = self._path_for(context_id)
        try:
            payload = self._serializer.serialize(state.model_dump(mode="json"))
            encrypted = self._encryption.encrypt(payload)
            path.write_bytes(encrypted)
        except StateSaveError:
            raise
        except Exception as exc:
            raise StateSaveError(f"failed to write auth state: {exc}") from exc
        return path

    async def load(self, context_id: str) -> AuthState:
        path = self._path_for(context_id)
        if not path.exists():
            raise StateLoadError(f"no auth state for context '{context_id}'")
        try:
            raw = path.read_bytes()
            payload = self._encryption.decrypt(raw)
            data = self._serializer.deserialize(payload)
            state = AuthState.model_validate(data)
            if state.session and state.session.metadata:
                self._ttl.validate_session(state.session.metadata)
            return state
        except StateLoadError:
            raise
        except Exception as exc:
            raise StateLoadError(f"failed to load auth state: {exc}") from exc

    def delete(self, context_id: str) -> None:
        path = self._path_for(context_id)
        if path.exists():
            path.unlink()
