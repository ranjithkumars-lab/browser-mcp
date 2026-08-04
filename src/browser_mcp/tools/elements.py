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
from browser_mcp.tools.aliases import register_underscore_alias
from enterprise_mcp.tools.decorators import tool

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

    # -- input actions --------------------------------------------------

    @tool(
        name=f"{TOOL_NAMESPACE}.fill",
        description=(
            "Set the value of a text input field. Takes an element_id returned "
            "by browser.element.find (or a CSS selector via the selector "
            "argument). Prefer this over form.fill when you already have an "
            "element_id. After filling, submit with browser.element.press "
            "key='Enter' or browser.form.submit."
        ),
        returns="json",
    )
    async def fill(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        value: str,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Fill a text input with ``value``."""
        try:
            result = await self._engine.fill(
                session_id, page_id, element_id, value, timeout_ms=timeout_ms
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.type",
        description=(
            "Type text into an element one key at a time (delay_ms between "
            "keys). Prefer this over fill when the page reacts to each "
            "keystroke (autocomplete, live validation)."
        ),
        returns="json",
    )
    async def type(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        text: str,
        delay_ms: int | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Type ``text`` into ``element_id`` one key at a time."""
        try:
            result = await self._engine.type_text(
                session_id,
                page_id,
                element_id,
                text,
                delay_ms=delay_ms,
                timeout_ms=timeout_ms,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.clear",
        description="Clear the current value of a text input field.",
        returns="json",
    )
    async def clear(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Clear the value of ``element_id``."""
        try:
            result = await self._engine.clear(
                session_id, page_id, element_id, timeout_ms=timeout_ms
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.press",
        description=(
            "Press a keyboard key on a focused element. Common keys: 'Enter' "
            "(submit forms), 'Tab', 'Escape', 'Control+A'. Use key='Enter' to "
            "submit a login or search form after filling its fields."
        ),
        returns="json",
    )
    async def press(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        key: str,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Press a keyboard ``key`` on ``element_id``."""
        try:
            result = await self._engine.press(
                session_id, page_id, element_id, key, timeout_ms=timeout_ms
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.select_option",
        description=(
            "Select an option in a <select> dropdown by its value. "
            "Find the dropdown first with browser.element.find (tag 'select')."
        ),
        returns="json",
    )
    async def select_option(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        value: str,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Select option ``value`` in ``element_id``."""
        try:
            result = await self._engine.select_option(
                session_id, page_id, element_id, value, timeout_ms=timeout_ms
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.check",
        description="Check a checkbox or radio button by element_id.",
        returns="json",
    )
    async def check(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Check the checkbox/radio ``element_id``."""
        try:
            result = await self._engine.check(
                session_id, page_id, element_id, timeout_ms=timeout_ms
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.uncheck",
        description="Uncheck a checkbox or radio button by element_id.",
        returns="json",
    )
    async def uncheck(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Uncheck the checkbox/radio ``element_id``."""
        try:
            result = await self._engine.uncheck(
                session_id, page_id, element_id, timeout_ms=timeout_ms
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.input_value",
        description=(
            "Return the current value of an input/textarea/select element. "
            "Useful to verify that a fill/type operation took effect."
        ),
        returns="json",
    )
    async def input_value(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
    ) -> dict[str, Any]:
        """Return the current value of ``element_id``."""
        try:
            result = await self._engine.input_value(session_id, page_id, element_id)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.focus",
        description="Move keyboard focus to an element.",
        returns="json",
    )
    async def focus(
        self,
        session_id: str,
        page_id: str,
        element_id: str,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Move keyboard focus to ``element_id``."""
        try:
            result = await self._engine.focus(
                session_id, page_id, element_id, timeout_ms=timeout_ms
            )
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
            register_underscore_alias(registry, method, TOOL_NAMESPACE, name)


_TOOL_METHODS = frozenset(
    {
        "find",
        "find_all",
        "state",
        "text",
        "html",
        "attribute",
        "fill",
        "type",
        "clear",
        "press",
        "select_option",
        "check",
        "uncheck",
        "input_value",
        "focus",
    }
)


def build_element_tools(engine: ElementEngine) -> list[Callable[..., Any]]:
    """Return the Phase 3 element tool callables bound to ``engine``."""
    toolkit = ElementToolkit(engine)
    return [getattr(toolkit, name) for name in _TOOL_METHODS]
