"""MCP tool registrations for the form automation plugin."""

from __future__ import annotations

from typing import Any

from browser_mcp.plugins.forms.actions import FormActions
from enterprise_mcp.tools.decorators import tool

__all__ = ["FormToolkit"]

TOOL_NAMESPACE = "browser.form"


class FormToolkit:
    """Factory of form automation MCP tools."""

    def __init__(self, actions: FormActions) -> None:
        self._actions = actions

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
        return await self._actions.fill(
            page=None,
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
        return await self._actions.check(
            page=None,
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
        return await self._actions.uncheck(
            page=None,
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
        return await self._actions.select(
            page=None,
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
        return await self._actions.submit(
            page=None,
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
            registry_register(getattr(self, name))


_TOOL_METHODS = frozenset({"fill", "check", "uncheck", "select", "submit"})
