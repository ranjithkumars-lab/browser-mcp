"""Structured element tools (Phase 3).

Every tool returns a JSON mapping (``{"success": true, ...}``) with full ID
tracking (session/browser/context/page), the resolved ``element_id`` where
applicable, and a ``duration_ms`` timing field.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from browser_mcp.browser.elements.engine import ElementEngine
from enterprise_mcp.tools.decorators import get_tool_metadata, tool
from enterprise_mcp.tools.metadata import ToolMetadata

__all__ = ["ElementToolkit", "build_element_tools"]

TOOL_NAMESPACE = "browser.element"


def _ok(**fields: Any) -> dict[str, Any]:
    return {
        "success": True,
        "timestamp": datetime.now(UTC).isoformat(),
        **fields,
    }


def _err(error: str, **fields: Any) -> dict[str, Any]:
    return {
        "success": False,
        "error": error,
        "timestamp": datetime.now(UTC).isoformat(),
        **fields,
    }


class ElementToolkit:
    """Factory of structured element tools bound to the element engine."""

    def __init__(self, engine: ElementEngine) -> None:
        self._engine = engine

    @tool(
        name=f"{TOOL_NAMESPACE}.find",
        description=(
            "Find an element and return its element_id for later operations. "
            "strategy is one of 'css', 'xpath', 'aria' (role or role:name), "
            "'text', or 'playwright'. strict=true requires exactly one match."
        ),
        returns="json",
    )
    async def find(
        self,
        session_id: str,
        page_id: str,
        strategy: str,
        value: str,
        timeout_ms: int | None = None,
        strict: bool = True,
        frame_id: str | None = None,
    ) -> dict[str, Any]:
        """Resolve a locator to an ``element_id``."""
        try:
            result = await self._engine.find(
                session_id,
                page_id,
                strategy,
                value,
                frame_id=frame_id,
                timeout_ms=timeout_ms,
                strict=strict,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.find_all",
        description=(
            "Find every element matching a locator and return one element_id per "
            "match. strategy is one of 'css', 'xpath', 'aria', 'text', 'playwright'."
        ),
        returns="json",
    )
    async def find_all(
        self,
        session_id: str,
        page_id: str,
        strategy: str,
        value: str,
        timeout_ms: int | None = None,
        frame_id: str | None = None,
    ) -> dict[str, Any]:
        """Resolve every match to an ``element_id``."""
        try:
            result = await self._engine.find_all(
                session_id,
                page_id,
                strategy,
                value,
                frame_id=frame_id,
                timeout_ms=timeout_ms,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.state",
        description=("Inspect an element's state: exists, visible, enabled, editable, checked."),
        returns="json",
    )
    async def state(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
    ) -> dict[str, Any]:
        """Return the boolean state snapshot of ``element_id``."""
        try:
            result = await self._engine.state(session_id, page_id, element_id)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.text",
        description="Return the rendered inner text of an element.",
        returns="json",
    )
    async def text(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
    ) -> dict[str, Any]:
        """Return the rendered text of ``element_id``."""
        try:
            result = await self._engine.text(session_id, page_id, element_id)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.html",
        description="Return the inner (or outer when outer=true) HTML of an element.",
        returns="json",
    )
    async def html(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        outer: bool = False,
    ) -> dict[str, Any]:
        """Return the inner/outer HTML of ``element_id``."""
        try:
            result = await self._engine.html(session_id, page_id, element_id, outer=outer)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.attribute",
        description="Return the value of an attribute on an element.",
        returns="json",
    )
    async def attribute(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        attribute_name: str,
    ) -> dict[str, Any]:
        """Return the value of ``attribute_name`` on ``element_id``."""
        try:
            result = await self._engine.attribute(session_id, page_id, element_id, attribute_name)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    # -- registration ---------------------------------------------------

    def register(self, registry: Any) -> None:
        """Register every tool in this toolkit with ``registry``."""
        registry_register = registry.register
        for name in _TOOL_METHODS:
            method = getattr(self, name)
            registry_register(method)
            _register_underscore_alias(registry, method, name)


def _register_underscore_alias(registry: Any, method: Callable[..., Any], name: str) -> None:
    """Register an ``browser.element_find``-style alias for a dotted tool name.

    LLM clients frequently guess underscore tool names (matching lifecycle tools
    like ``browser.list_frames``) instead of the dotted ``browser.element.find``.
    Registering both spellings keeps the agent loop working either way.
    """
    metadata = get_tool_metadata(method)
    if metadata is None:
        return
    alias = ToolMetadata(
        name=f"{TOOL_NAMESPACE}_{name}",
        description=(f"Alias for '{metadata.name}'. {metadata.description}"),
        parameters=metadata.parameters,
        returns=metadata.returns,
        version=metadata.version,
    )
    registry.register(method, metadata=alias)


_TOOL_METHODS = frozenset({"find", "find_all", "state", "text", "html", "attribute"})


def build_element_tools(engine: ElementEngine) -> list[Callable[..., Any]]:
    """Return the Phase 3 element tool callables bound to ``engine``."""
    toolkit = ElementToolkit(engine)
    return [getattr(toolkit, name) for name in _TOOL_METHODS]
