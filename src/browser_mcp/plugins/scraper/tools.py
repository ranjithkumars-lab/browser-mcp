"""MCP tool registrations for the web scraping plugin.

Every tool returns a structured JSON mapping with full ID tracking
(session/browser/context/page), the formatted result, and timing metadata.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from browser_mcp.plugins.scraper.actions import ScraperActions
from enterprise_mcp.tools.decorators import tool

__all__ = ["ScraperToolkit", "build_scraper_tools"]

TOOL_NAMESPACE = "browser.scrape"


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


class ScraperToolkit:
    """Factory of structured scraping MCP tools bound to ``ScraperActions``."""

    def __init__(self, actions: ScraperActions) -> None:
        self._actions = actions

    @tool(
        name=f"{TOOL_NAMESPACE}.text",
        description=(
            "Extract visible text from the page body. Optionally restrict "
            "extraction to elements matching a CSS selector. output_format is "
            "one of: 'json', 'markdown', 'text', 'csv', 'html'."
        ),
        returns="json",
    )
    async def text(
        self,
        session_id: str,
        page_id: str,
        selector: str | None = None,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Extract visible text from the page body."""
        try:
            return _ok(
                **await self._actions.scrape_text(
                    session_id, page_id, selector=selector, output_format=output_format
                )
            )
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.tables",
        description=(
            "Extract structured ``<table>`` data as rows and cells. "
            "Optionally target a single table via a CSS selector."
        ),
        returns="json",
    )
    async def tables(
        self,
        session_id: str,
        page_id: str,
        selector: str | None = None,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Extract structured table data from the page."""
        try:
            return _ok(
                **await self._actions.scrape_tables(
                    session_id, page_id, selector=selector, output_format=output_format
                )
            )
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.images",
        description=(
            "Extract ``<img>`` tags including resolved URLs, alt text, "
            "dimensions, natural dimensions, and loading attribute."
        ),
        returns="json",
    )
    async def images(
        self,
        session_id: str,
        page_id: str,
        selector: str | None = None,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Extract image elements from the page."""
        try:
            return _ok(
                **await self._actions.scrape_images(
                    session_id, page_id, selector=selector, output_format=output_format
                )
            )
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.metadata",
        description=(
            "Extract ``<meta>`` tags, ``<title>``, OpenGraph and Twitter card data from the page."
        ),
        returns="json",
    )
    async def metadata(
        self,
        session_id: str,
        page_id: str,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Extract page-level metadata."""
        try:
            return _ok(
                **await self._actions.scrape_metadata(
                    session_id, page_id, output_format=output_format
                )
            )
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.jsonld",
        description=(
            "Extract and parse embedded ``application/ld+json`` JSON-LD structured-data blocks."
        ),
        returns="json",
    )
    async def jsonld(
        self,
        session_id: str,
        page_id: str,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Extract JSON-LD structured data from the page."""
        try:
            return _ok(
                **await self._actions.scrape_jsonld(
                    session_id, page_id, output_format=output_format
                )
            )
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.links",
        description=(
            "Extract ``<a>`` tags with strict URL normalisation: relative URLs "
            "are resolved to absolute, duplicates are removed, and unsupported "
            "schemes (mailto, tel, javascript, …) are filtered."
        ),
        returns="json",
    )
    async def links(
        self,
        session_id: str,
        page_id: str,
        selector: str | None = None,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Extract links from the page with URL normalisation."""
        try:
            return _ok(
                **await self._actions.scrape_links(
                    session_id, page_id, selector=selector, output_format=output_format
                )
            )
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.products",
        description=(
            "Composite product extraction using a priority chain: "
            "JSON-LD (Product schema) -> Open Graph -> Microdata -> DOM heuristics -> "
            "Meta tags. Returns the first non-empty signal."
        ),
        returns="json",
    )
    async def products(
        self,
        session_id: str,
        page_id: str,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Extract product data using the composite collector."""
        try:
            return _ok(
                **await self._actions.scrape_products(
                    session_id, page_id, output_format=output_format
                )
            )
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    def register(self, registry: Any) -> None:
        """Register every tool in this toolkit with ``registry``."""
        registry_register = registry.register
        for name in _TOOL_METHODS:
            registry_register(getattr(self, name))


_TOOL_METHODS = frozenset({"text", "tables", "images", "metadata", "jsonld", "links", "products"})


def build_scraper_tools(actions: ScraperActions) -> list[Callable[..., Any]]:
    """Return the seven scrape tool callables bound to ``actions``."""
    toolkit = ScraperToolkit(actions)
    return [getattr(toolkit, name) for name in _TOOL_METHODS]
