"""Element property extraction.

:class:`ElementProperties` exposes the ``text()``, ``html()`` and
``attribute()`` extractors used by the element engine and its MCP tools. All
methods take a resolved locator handle and delegate to the provider, so the
extractors stay engine-agnostic.
"""

from __future__ import annotations

from typing import Any

from browser_mcp.browser.elements.provider import LocatorProvider

__all__ = ["ElementProperties"]


class ElementProperties:
    """Extractors for element text, HTML and attributes."""

    def __init__(self, provider: LocatorProvider) -> None:
        self._provider = provider

    async def text(self, locator: Any) -> str:
        """Return the rendered inner text of the first match."""
        return await self._provider.inner_text(locator)

    async def html(self, locator: Any, *, outer: bool = False) -> str:
        """Return the inner HTML, or the outer HTML when ``outer`` is true."""
        if outer:
            return await self._provider.outer_html(locator)
        return await self._provider.inner_html(locator)

    async def attribute(self, locator: Any, name: str) -> str | None:
        """Return the value of attribute ``name``, or ``None`` when absent."""
        return await self._provider.get_attribute(locator, name)
