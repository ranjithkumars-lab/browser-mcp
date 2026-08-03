"""MCP tools for the authentication engine."""

from __future__ import annotations

from typing import Any

from browser_mcp.auth.manager import AuthManager
from browser_mcp.auth.models import AuthCredentials
from browser_mcp.tools.aliases import register_underscore_alias
from enterprise_mcp.tools.decorators import tool

__all__ = ["AuthToolkit"]

TOOL_NAMESPACE = "browser.auth"


def _ok(**fields: Any) -> dict[str, Any]:
    return {"success": True, **fields}


def _err(error: str, **fields: Any) -> dict[str, Any]:
    return {"success": False, "error": error, **fields}


class AuthToolkit:
    """Factory of structured auth tools bound to an :class:`AuthManager`."""

    def __init__(self, auth_manager: AuthManager, pool: Any, sessions: Any) -> None:
        self._auth_manager = auth_manager
        self._pool = pool
        self._sessions = sessions

    @tool(
        name=f"{TOOL_NAMESPACE}.login",
        description="Authenticate against a browser context using the configured strategy.",
        returns="json",
    )
    async def login(
        self,
        session_id: str,
        context_id: str,
        strategy: str = "form",
        username: str | None = None,
        password: str | None = None,
        url: str = "",
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            credentials = AuthCredentials(
                username=username,
                password=password,
                url=url,
                strategy=strategy,
                headers=headers or {},
                cookies=cookies or {},
                metadata=metadata or {"session_id": session_id, "context_id": context_id},
            )
        except Exception as exc:
            return _err(str(exc))
        try:
            self._sessions.get_session(session_id)
            handle = self._pool.get_context(context_id)
        except Exception as exc:
            return _err(str(exc))
        try:
            result = await self._auth_manager.login(handle.context, credentials)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc))

    @tool(
        name=f"{TOOL_NAMESPACE}.save_state",
        description="Persist the current auth state for a context to disk.",
        returns="json",
    )
    async def save_state(
        self,
        session_id: str,
        context_id: str,
    ) -> dict[str, Any]:
        try:
            state = await self._auth_manager.load_state(context_id)
        except Exception as exc:
            return _err(str(exc))
        try:
            result = await self._auth_manager.save_state(context_id, session_id, state)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc))

    @tool(
        name=f"{TOOL_NAMESPACE}.load_state",
        description="Load a previously persisted auth state for a context.",
        returns="json",
    )
    async def load_state(
        self,
        context_id: str,
    ) -> dict[str, Any]:
        try:
            state = await self._auth_manager.load_state(context_id)
            return _ok(state=state.model_dump(mode="json"))
        except Exception as exc:
            return _err(str(exc))

    @tool(
        name=f"{TOOL_NAMESPACE}.set_headers",
        description="Inject dynamic HTTP headers into a browser context.",
        returns="json",
    )
    async def set_headers(
        self,
        session_id: str,
        context_id: str,
        headers: dict[str, str],
    ) -> dict[str, Any]:
        try:
            self._sessions.get_session(session_id)
            handle = self._pool.get_context(context_id)
        except Exception as exc:
            return _err(str(exc))
        try:
            result = await self._auth_manager.set_headers(
                handle.context, headers, context_id=context_id, session_id=session_id
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc))

    def register(self, registry: Any) -> None:
        registry_register = registry.register
        for name in _TOOL_METHODS:
            method = getattr(self, name)
            registry_register(method)
            register_underscore_alias(registry, method, TOOL_NAMESPACE, name)


_TOOL_METHODS = frozenset({"login", "save_state", "load_state", "set_headers"})
