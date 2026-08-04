"""Structured page-level keyboard tools.

``browser.keyboard.type`` sends keystrokes to the focused element (or the
active page) and ``browser.keyboard.press`` presses a named key such as
``Enter``, ``Tab`` or ``Escape``. These complement the element-level actions
(``browser.element.fill`` / ``browser.element.press``) for flows that need to
interact with whatever currently has focus — e.g. pressing Enter to submit a
login form after filling its fields.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from browser_mcp.browser.navigation.interactions import InteractionManager
from browser_mcp.tools.aliases import register_underscore_alias
from enterprise_mcp.tools.decorators import tool

__all__ = ["KeyboardToolkit", "build_keyboard_tools"]

TOOL_NAMESPACE = "browser.keyboard"


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


class KeyboardToolkit:
    """Factory of structured keyboard tools bound to the interaction manager."""

    def __init__(self, interactions: InteractionManager) -> None:
        self._interactions = interactions

    @tool(
        name=f"{TOOL_NAMESPACE}.type",
        description=(
            "Type text at the page level using whatever element currently has "
            "focus (or the page body). delay_ms spaces keystrokes apart for "
            "sites with per-key handlers."
        ),
        returns="json",
    )
    async def type(
        self,
        session_id: str,
        page_id: str,
        text: str,
        delay_ms: int | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Type ``text`` at the page level."""
        try:
            result = await self._interactions.keyboard_type(
                session_id,
                page_id,
                text,
                delay_ms=delay_ms,
                timeout_ms=timeout_ms,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.press",
        description=(
            "Press a named key at the page level. Common keys: 'Enter' "
            "(submit the focused form/field), 'Tab', 'Escape', 'Control+A'. "
            "Use this to submit a login form after filling its fields."
        ),
        returns="json",
    )
    async def press(
        self,
        session_id: str,
        page_id: str,
        key: str,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Press key ``key`` at the page level."""
        try:
            result = await self._interactions.keyboard_press(
                session_id, page_id, key, timeout_ms=timeout_ms
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    def register(self, registry: Any) -> None:
        """Register every tool in this toolkit with ``registry``."""
        registry_register = registry.register
        for name in _TOOL_METHODS:
            method = getattr(self, name)
            registry_register(method)
            register_underscore_alias(registry, method, TOOL_NAMESPACE, name)


_TOOL_METHODS = frozenset({"type", "press"})


def build_keyboard_tools(interactions: InteractionManager) -> list[Callable[..., Any]]:
    """Return the keyboard tool callables bound to ``interactions``."""
    toolkit = KeyboardToolkit(interactions)
    return [getattr(toolkit, name) for name in _TOOL_METHODS]
