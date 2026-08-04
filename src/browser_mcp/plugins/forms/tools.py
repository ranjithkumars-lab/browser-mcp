"""MCP tool registrations for the form automation plugin."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

from browser_mcp.plugins.forms.actions import FormActions
from browser_mcp.tools.aliases import register_underscore_alias
from enterprise_mcp.tools.decorators import tool

__all__ = ["FormToolkit"]

TOOL_NAMESPACE = "browser.form"


class FormToolkit:
    """Factory of form automation MCP tools."""

    def __init__(
        self,
        actions: FormActions,
        page_resolver: Callable[[str, str], Any],
    ) -> None:
        self._actions = actions
        self._page_resolver = page_resolver

    async def _page(self, session_id: str, page_id: str) -> Any:
        """Resolve the live Playwright page for ``session_id``/``page_id``."""
        resolved = self._page_resolver(session_id, page_id)
        if inspect.isawaitable(resolved):
            return await resolved
        return resolved

    @tool(
        name=f"{TOOL_NAMESPACE}.fill",
        description=(
            "Fill a text input field with a value. "
            "The field is located by explicit selector, name, id, "
            "placeholder, or associated label."
        ),
        returns="json",
    )
    async def fill(
        self,
        session_id: str,
        page_id: str,
        field: str,
        value: str,
        *,
        selector: str | None = None,
    ) -> dict[str, Any]:
        """Fill a text field."""
        page = await self._page(session_id, page_id)
        return await self._actions.fill(
            page=page,
            session_id=session_id,
            browser_id="",
            context_id="",
            page_id=page_id,
            field=field,
            value=value,
            selector=selector,
        )

    @tool(
        name=f"{TOOL_NAMESPACE}.check",
        description="Check a checkbox or radio button.",
        returns="json",
    )
    async def check(
        self,
        session_id: str,
        page_id: str,
        field: str,
        *,
        selector: str | None = None,
    ) -> dict[str, Any]:
        """Check a checkbox or radio."""
        page = await self._page(session_id, page_id)
        return await self._actions.check(
            page=page,
            session_id=session_id,
            browser_id="",
            context_id="",
            page_id=page_id,
            field=field,
            selector=selector,
        )

    @tool(
        name=f"{TOOL_NAMESPACE}.uncheck",
        description="Uncheck a checkbox or radio button.",
        returns="json",
    )
    async def uncheck(
        self,
        session_id: str,
        page_id: str,
        field: str,
        *,
        selector: str | None = None,
    ) -> dict[str, Any]:
        """Uncheck a checkbox or radio."""
        page = await self._page(session_id, page_id)
        return await self._actions.uncheck(
            page=page,
            session_id=session_id,
            browser_id="",
            context_id="",
            page_id=page_id,
            field=field,
            selector=selector,
        )

    @tool(
        name=f"{TOOL_NAMESPACE}.select",
        description="Select an option in a <select> element.",
        returns="json",
    )
    async def select(
        self,
        session_id: str,
        page_id: str,
        field: str,
        value: str,
        *,
        selector: str | None = None,
    ) -> dict[str, Any]:
        """Select an option."""
        page = await self._page(session_id, page_id)
        return await self._actions.select(
            page=page,
            session_id=session_id,
            browser_id="",
            context_id="",
            page_id=page_id,
            field=field,
            value=value,
            selector=selector,
        )

    @tool(
        name=f"{TOOL_NAMESPACE}.submit",
        description="Submit a form. Optionally target a submit button.",
        returns="json",
    )
    async def submit(
        self,
        session_id: str,
        page_id: str,
        field: str | None = None,
        *,
        selector: str | None = None,
    ) -> dict[str, Any]:
        """Submit a form."""
        page = await self._page(session_id, page_id)
        return await self._actions.submit(
            page=page,
            session_id=session_id,
            browser_id="",
            context_id="",
            page_id=page_id,
            field=field,
            selector=selector,
        )

    def register(self, registry: Any) -> None:
        """Register every tool in this toolkit with ``registry``."""
        registry_register = registry.register
        for name in _TOOL_METHODS:
            method = getattr(self, name)
            registry_register(method)
            register_underscore_alias(registry, method, TOOL_NAMESPACE, name)


_TOOL_METHODS = frozenset({"fill", "check", "uncheck", "select", "submit"})
