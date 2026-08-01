"""High-level facade orchestrating strategies, storage, and provider calls."""

from __future__ import annotations

import time
from typing import Any

from browser_mcp.auth.events import (
    emit_auth_failed,
    emit_auth_headers_updated,
    emit_auth_started,
    emit_auth_state_loaded,
    emit_auth_state_saved,
    emit_auth_success,
)
from browser_mcp.auth.models import AuthCredentials, AuthMetadata, AuthSession, AuthState
from browser_mcp.auth.provider import AuthProvider
from browser_mcp.auth.storage.manager import AuthStorageManager
from browser_mcp.auth.strategies.base import BaseAuthStrategy
from browser_mcp.auth.strategies.registry import AuthStrategyRegistry
from browser_mcp.errors import LoginFailedError

__all__ = ["AuthManager"]


class AuthManager:
    """Facade over auth strategies, storage, and provider."""

    def __init__(
        self,
        registry: AuthStrategyRegistry,
        storage: AuthStorageManager,
        provider: AuthProvider,
        event_bus: Any,
    ) -> None:
        self._registry = registry
        self._storage = storage
        self._provider = provider
        self._events = event_bus

    async def login(self, context: Any, credentials: AuthCredentials) -> dict[str, Any]:
        strategy = self._registry.get(credentials.strategy)
        await emit_auth_started(
            self._events,
            strategy=credentials.strategy,
            context_id=credentials.metadata.get("context_id", ""),
            session_id=credentials.metadata.get("session_id", ""),
        )
        started = time.perf_counter()
        try:
            _ = await strategy.execute(context, credentials)
            duration_ms = (time.perf_counter() - started) * 1000
            session = AuthSession(
                session_id=credentials.metadata.get("session_id", ""),
                context_id=credentials.metadata.get("context_id", ""),
                authenticated=True,
                metadata=AuthMetadata(
                    strategy=credentials.strategy,
                    context_id=credentials.metadata.get("context_id", ""),
                    session_id=credentials.metadata.get("session_id", ""),
                ),
            )
            state = AuthState(session=session)
            await self._storage.save(session.context_id, state)
            await emit_auth_state_saved(
                self._events,
                context_id=session.context_id,
                session_id=session.session_id,
                path=str(self._storage._path_for(session.context_id)),  # type: ignore[reportPrivateUsage]
                encrypted=True,
            )
            await emit_auth_success(
                self._events,
                strategy=credentials.strategy,
                context_id=session.context_id,
                session_id=session.session_id,
                duration_ms=duration_ms,
            )
            return {
                "success": True,
                "session": state.model_dump(mode="json"),
                "duration_ms": duration_ms,
            }
        except LoginFailedError:
            raise
        except Exception as exc:
            duration_ms = (time.perf_counter() - started) * 1000
            await emit_auth_failed(
                self._events,
                strategy=credentials.strategy,
                context_id=credentials.metadata.get("context_id", ""),
                session_id=credentials.metadata.get("session_id", ""),
                error=str(exc),
                duration_ms=duration_ms,
            )
            raise LoginFailedError(str(exc)) from exc

    async def save_state(
        self, context_id: str, session_id: str, state: AuthState
    ) -> dict[str, Any]:
        path = await self._storage.save(context_id, state)
        await emit_auth_state_saved(
            self._events,
            context_id=context_id,
            session_id=session_id,
            path=str(path),
            encrypted=True,
        )
        return {"success": True, "path": str(path)}

    async def load_state(self, context_id: str) -> AuthState:
        state = await self._storage.load(context_id)
        await emit_auth_state_loaded(
            self._events,
            context_id=context_id,
            session_id=state.session.session_id,
            path=str(self._storage._path_for(context_id)),  # type: ignore[reportPrivateUsage]
        )
        return state

    async def set_headers(
        self, context: Any, headers: dict[str, str], *, context_id: str, session_id: str
    ) -> dict[str, Any]:
        await self._provider.inject_headers(context, headers)
        await emit_auth_headers_updated(
            self._events,
            context_id=context_id,
            session_id=session_id,
            headers=list(headers.keys()),
        )
        return {"success": True, "headers_injected": list(headers.keys())}

    def register_strategy(self, strategy: BaseAuthStrategy) -> None:
        self._registry.register(strategy)
