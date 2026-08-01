"""Structured browser lifecycle tools.

Every tool returns a structured JSON mapping (``{"success": true, ...}``)
rather than a plain string, so clients can programmatically inspect results.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from browser_mcp.browser.session import SessionManager
from browser_mcp.config.models import BrowserEngine, BrowserProfile
from enterprise_mcp.tools.decorators import tool

__all__ = ["BrowserToolkit"]

TOOL_NAMESPACE = "browser"


def _ok(**fields: Any) -> dict[str, Any]:
    return {"success": True, **fields}


def _err(error: str, **fields: Any) -> dict[str, Any]:
    return {"success": False, "error": error, **fields}


class BrowserToolkit:
    """Factory of structured browser lifecycle tools bound to a session manager."""

    def __init__(self, sessions: SessionManager) -> None:
        self._sessions = sessions

    # -- session --------------------------------------------------------

    @tool(
        name=f"{TOOL_NAMESPACE}.create_session",
        description=(
            "Launch a new browser session and return its session_id. "
            "Optionally pick an engine (chromium/firefox/webkit), headless mode, "
            "and a profile (temporary/persistent/incognito)."
        ),
        returns="json",
    )
    async def create_session(
        self,
        engine: str = "chromium",
        headless: bool = True,
        profile: str = "temporary",
        label: str | None = None,
    ) -> dict[str, Any]:
        """Create a new browser session."""
        try:
            result = await self._sessions.create_session(
                engine=BrowserEngine(engine),
                headless=headless,
                profile=BrowserProfile(profile),
                label=label,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc))

    @tool(
        name=f"{TOOL_NAMESPACE}.close_session",
        description="Close a browser session and release all of its resources.",
        returns="json",
    )
    async def close_session(self, session_id: str) -> dict[str, Any]:
        """Close an existing browser session."""
        try:
            result = await self._sessions.close_session(session_id)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc))

    # -- context --------------------------------------------------------

    @tool(
        name=f"{TOOL_NAMESPACE}.create_context",
        description=(
            "Create a new context (storage sandbox) inside an existing session. "
            "Returns the context_id."
        ),
        returns="json",
    )
    async def create_context(
        self,
        session_id: str,
        profile: str = "temporary",
        label: str | None = None,
    ) -> dict[str, Any]:
        """Create a context inside a session's browser."""
        try:
            result = await self._sessions.create_context(
                session_id,
                profile=BrowserProfile(profile),
                label=label,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc))

    @tool(
        name=f"{TOOL_NAMESPACE}.close_context",
        description="Close a context and all of its pages.",
        returns="json",
    )
    async def close_context(self, session_id: str, context_id: str) -> dict[str, Any]:
        """Close a context within a session."""
        try:
            result = await self._sessions.close_context(session_id, context_id)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc))

    # -- page -----------------------------------------------------------

    @tool(
        name=f"{TOOL_NAMESPACE}.new_page",
        description=(
            "Open a new page in a context. Optionally navigate to url. Returns the page_id."
        ),
        returns="json",
    )
    async def new_page(
        self,
        session_id: str,
        context_id: str,
        url: str | None = None,
    ) -> dict[str, Any]:
        """Open a new page inside a session's context."""
        try:
            result = await self._sessions.new_page(session_id, context_id, url=url)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc))

    @tool(
        name=f"{TOOL_NAMESPACE}.close_page",
        description="Close an individual page.",
        returns="json",
    )
    async def close_page(self, session_id: str, page_id: str) -> dict[str, Any]:
        """Close a page within a session."""
        try:
            result = await self._sessions.close_page(session_id, page_id)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc))

    # -- registration ---------------------------------------------------

    def register(self, registry: Any) -> None:
        """Register every tool in this toolkit with ``registry``."""
        registry_register = registry.register
        for name in _TOOL_METHODS:
            registry_register(getattr(self, name))


_TOOL_METHODS = frozenset(
    {"create_session", "close_session", "create_context", "close_context", "new_page", "close_page"}
)


def build_browser_tools(sessions: SessionManager) -> list[Callable[..., Any]]:
    """Return the six browser tool callables bound to ``sessions``."""
    toolkit = BrowserToolkit(sessions)
    return [getattr(toolkit, name) for name in _TOOL_METHODS]
