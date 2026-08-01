"""Unit tests for the ScraperToolkit (tool registration)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from browser_mcp.plugins.scraper.tools import TOOL_NAMESPACE, ScraperToolkit, build_scraper_tools
from enterprise_mcp.tools.decorators import get_tool_metadata

pytestmark = pytest.mark.unit


class TestScraperToolkit:
    def test_init_stores_actions(self) -> None:
        actions = MagicMock()
        toolkit = ScraperToolkit(actions)
        assert toolkit._actions is actions

    def test_tool_namespace(self) -> None:
        assert TOOL_NAMESPACE == "browser.scrape"

    def test_tool_methods_have_metadata(self) -> None:
        toolkit = ScraperToolkit(MagicMock())
        for name in ("text", "tables", "images", "metadata", "jsonld", "links", "products"):
            method = getattr(toolkit, name)
            metadata = get_tool_metadata(method)
            assert metadata is not None
            assert metadata.name == f"browser.scrape.{name}"
            assert metadata.returns == "json"

    def test_register_calls_registry(self) -> None:
        toolkit = ScraperToolkit(MagicMock())
        registry = MagicMock()
        registry.register = MagicMock()
        toolkit.register(registry)
        assert registry.register.call_count == 7

    @pytest.mark.asyncio
    async def test_text_tool_success(self) -> None:
        actions = MagicMock()
        actions.scrape_text = AsyncMock(return_value={"success": True, "data": "[]"})
        toolkit = ScraperToolkit(actions)
        result = await toolkit.text("s1", "p1")
        assert result["success"] is True
        actions.scrape_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_text_tool_error(self) -> None:
        actions = MagicMock()
        actions.scrape_text = AsyncMock(side_effect=RuntimeError("page not found"))
        toolkit = ScraperToolkit(actions)
        result = await toolkit.text("s1", "p1")
        assert result["success"] is False
        assert "page not found" in result["error"]

    @pytest.mark.asyncio
    async def test_tables_tool_success(self) -> None:
        actions = MagicMock()
        actions.scrape_tables = AsyncMock(return_value={"success": True, "data": "[]"})
        toolkit = ScraperToolkit(actions)
        result = await toolkit.tables("s1", "p1")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_tables_tool_error(self) -> None:
        actions = MagicMock()
        actions.scrape_tables = AsyncMock(side_effect=ValueError("bad"))
        toolkit = ScraperToolkit(actions)
        result = await toolkit.tables("s1", "p1")
        assert result["success"] is False
        assert "bad" in result["error"]

    @pytest.mark.asyncio
    async def test_images_tool_success(self) -> None:
        actions = MagicMock()
        actions.scrape_images = AsyncMock(return_value={"success": True, "data": "[]"})
        toolkit = ScraperToolkit(actions)
        result = await toolkit.images("s1", "p1")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_images_tool_error(self) -> None:
        actions = MagicMock()
        actions.scrape_images = AsyncMock(side_effect=RuntimeError("img error"))
        toolkit = ScraperToolkit(actions)
        result = await toolkit.images("s1", "p1")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_metadata_tool_success(self) -> None:
        actions = MagicMock()
        actions.scrape_metadata = AsyncMock(return_value={"success": True, "data": "{}"})
        toolkit = ScraperToolkit(actions)
        result = await toolkit.metadata("s1", "p1")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_metadata_tool_error(self) -> None:
        actions = MagicMock()
        actions.scrape_metadata = AsyncMock(side_effect=RuntimeError("meta err"))
        toolkit = ScraperToolkit(actions)
        result = await toolkit.metadata("s1", "p1")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_jsonld_tool_success(self) -> None:
        actions = MagicMock()
        actions.scrape_jsonld = AsyncMock(return_value={"success": True, "data": "[]"})
        toolkit = ScraperToolkit(actions)
        result = await toolkit.jsonld("s1", "p1")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_jsonld_tool_error(self) -> None:
        actions = MagicMock()
        actions.scrape_jsonld = AsyncMock(side_effect=RuntimeError("jsonld err"))
        toolkit = ScraperToolkit(actions)
        result = await toolkit.jsonld("s1", "p1")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_links_tool_success(self) -> None:
        actions = MagicMock()
        actions.scrape_links = AsyncMock(return_value={"success": True, "data": "[]"})
        toolkit = ScraperToolkit(actions)
        result = await toolkit.links("s1", "p1")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_links_tool_error(self) -> None:
        actions = MagicMock()
        actions.scrape_links = AsyncMock(side_effect=RuntimeError("links err"))
        toolkit = ScraperToolkit(actions)
        result = await toolkit.links("s1", "p1")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_products_tool_success(self) -> None:
        actions = MagicMock()
        actions.scrape_products = AsyncMock(return_value={"success": True, "data": "{}"})
        toolkit = ScraperToolkit(actions)
        result = await toolkit.products("s1", "p1")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_products_tool_error(self) -> None:
        actions = MagicMock()
        actions.scrape_products = AsyncMock(side_effect=RuntimeError("product err"))
        toolkit = ScraperToolkit(actions)
        result = await toolkit.products("s1", "p1")
        assert result["success"] is False


def test_build_scraper_tools_returns_all() -> None:
    actions = MagicMock()
    tools = build_scraper_tools(actions)
    assert len(tools) == 7
    names = {t.__name__ for t in tools}
    assert names == {"text", "tables", "images", "metadata", "jsonld", "links", "products"}
