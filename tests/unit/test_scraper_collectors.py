"""Unit tests for scraper pipeline collectors."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from browser_mcp.plugins.scraper.collectors.base import BaseCollector
from browser_mcp.plugins.scraper.collectors.images import ImagesCollector
from browser_mcp.plugins.scraper.collectors.jsonld import JsonLdCollector
from browser_mcp.plugins.scraper.collectors.links import LinksCollector
from browser_mcp.plugins.scraper.collectors.metadata import MetadataCollector
from browser_mcp.plugins.scraper.collectors.product import ProductCollector
from browser_mcp.plugins.scraper.collectors.table import TableCollector
from browser_mcp.plugins.scraper.collectors.text import TextCollector

pytestmark = pytest.mark.unit


def _mock_page(url: str = "https://example.com") -> MagicMock:
    """Return a mock page with an AsyncMock ``evaluate`` and ``url``."""
    page = MagicMock()
    page.evaluate = AsyncMock()
    page.url = url
    return page


# ---------------------------------------------------------------------------
# BaseCollector
# ---------------------------------------------------------------------------


class TestBaseCollector:
    def test_default_name_strips_suffix(self) -> None:
        assert BaseCollector.__name__ == "BaseCollector"
        collector = TextCollector()
        assert collector.name == "text"

    @pytest.mark.asyncio
    async def test_safe_collect_wraps_error(self) -> None:
        class BoomCollector(BaseCollector):
            async def collect(self, page: object, **kwargs: object) -> list[dict[str, object]]:
                raise RuntimeError("kaboom")

        result = await BoomCollector().safe_collect(MagicMock())
        assert result == [{"_error": "kaboom", "_collector": "boom"}]


# ---------------------------------------------------------------------------
# TextCollector
# ---------------------------------------------------------------------------


class TestTextCollector:
    @pytest.mark.asyncio
    async def test_collect_full_text(self) -> None:
        page = _mock_page()
        page.evaluate.return_value = {
            "text": "Hello World\nFoo bar",
            "word_count": 4,
            "char_count": 15,
        }
        result = await TextCollector().collect(page)
        assert result == [{"text": "Hello World\nFoo bar", "word_count": 4, "char_count": 15}]

    @pytest.mark.asyncio
    async def test_collect_with_selector(self) -> None:
        page = _mock_page()
        page.evaluate.return_value = ["Alpha", "Beta"]
        result = await TextCollector().collect(page, selector="h1, h2")
        assert result == [{"texts": ["Alpha", "Beta"]}]


# ---------------------------------------------------------------------------
# TableCollector
# ---------------------------------------------------------------------------


class TestTableCollector:
    @pytest.mark.asyncio
    async def test_collect_all_tables(self) -> None:
        page = _mock_page()
        page.evaluate.return_value = [
            {
                "index": 0,
                "caption": "Users",
                "rows": [
                    {"cells": [{"value": "Name", "is_header": True, "col_span": 1, "row_span": 1}]},
                    {
                        "cells": [
                            {"value": "Alice", "is_header": False, "col_span": 1, "row_span": 1}
                        ]
                    },
                ],
            },
        ]
        result = await TableCollector().collect(page)
        assert len(result) == 1
        assert result[0]["caption"] == "Users"

    @pytest.mark.asyncio
    async def test_collect_by_selector(self) -> None:
        page = _mock_page()
        page.evaluate.return_value = [
            {
                "index": 0,
                "caption": "Single",
                "rows": [
                    {"cells": [{"value": "A", "is_header": True, "col_span": 1, "row_span": 1}]}
                ],
            }
        ]
        result = await TableCollector().collect(page, selector="#main-table")
        assert len(result) == 1
        assert result[0]["index"] == 0


# ---------------------------------------------------------------------------
# ImagesCollector
# ---------------------------------------------------------------------------


class TestImagesCollector:
    @pytest.mark.asyncio
    async def test_collect_resolves_urls(self) -> None:
        page = _mock_page(url="https://example.com/page")
        page.evaluate.return_value = [
            {
                "src": "/assets/hero.jpg",
                "current_src": "",
                "alt": "Hero",
                "loading": "eager",
                "width": 1200,
                "height": 400,
                "natural_width": 1200,
                "natural_height": 400,
                "complete": True,
                "decoded": True,
                "is_decorative": False,
            },
        ]
        result = await ImagesCollector().collect(page)
        assert len(result) == 1
        assert result[0]["resolved_url"] == "https://example.com/assets/hero.jpg"

    @pytest.mark.asyncio
    async def test_collect_with_selector(self) -> None:
        page = _mock_page(url="https://example.com")
        page.evaluate.return_value = [
            {
                "src": "/a.png",
                "current_src": "",
                "alt": "A",
                "loading": "lazy",
                "width": 0,
                "height": 0,
                "natural_width": 0,
                "natural_height": 0,
                "complete": True,
                "decoded": True,
                "is_decorative": True,
            }
        ]
        result = await ImagesCollector().collect(page, selector=".gallery img")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_collect_empty_result(self) -> None:
        page = _mock_page(url="https://example.com")
        page.evaluate.return_value = []
        result = await ImagesCollector().collect(page)
        assert result == []


# ---------------------------------------------------------------------------
# MetadataCollector
# ---------------------------------------------------------------------------


class TestMetadataCollector:
    @pytest.mark.asyncio
    async def test_collect_metadata(self) -> None:
        page = _mock_page()
        page.evaluate.return_value = {
            "title": "Test Page",
            "description": "A test page",
            "keywords": "test, page",
            "og": {"og:title": "Test Page"},
            "twitter": {"twitter:card": "summary"},
            "other": {"author": "Test"},
        }
        result = await MetadataCollector().collect(page)
        assert len(result) == 1
        assert result[0]["title"] == "Test Page"
        assert result[0]["og"]["og:title"] == "Test Page"


# ---------------------------------------------------------------------------
# JsonLdCollector
# ---------------------------------------------------------------------------


class TestJsonLdCollector:
    @pytest.mark.asyncio
    async def test_collect_valid_jsonld(self) -> None:
        page = _mock_page()
        page.evaluate.return_value = [
            '{"@context": "https://schema.org/", "@type": "Product", "name": "Widget"}',
            '{"@context": "https://schema.org/", "@type": "Organization", "name": "Acme"}',
        ]
        result = await JsonLdCollector().collect(page)
        assert len(result) == 2
        assert result[0]["data"]["@type"] == "Product"
        assert result[1]["data"]["@type"] == "Organization"

    @pytest.mark.asyncio
    async def test_collect_malformed_jsonld(self) -> None:
        page = _mock_page()
        page.evaluate.return_value = ["{not valid json}"]
        result = await JsonLdCollector().collect(page)
        assert len(result) == 1
        assert result[0]["type"] is None
        assert "_parse_error" in result[0]

    @pytest.mark.asyncio
    async def test_collect_type_is_list(self) -> None:
        page = _mock_page()
        page.evaluate.return_value = [
            '{"@context": "https://schema.org", "@type": ["Product", "Thing"], "name": "X"}'
        ]
        result = await JsonLdCollector().collect(page)
        assert result[0]["type"] == "Product"

    @pytest.mark.asyncio
    async def test_collect_no_scripts(self) -> None:
        page = _mock_page()
        page.evaluate.return_value = []
        result = await JsonLdCollector().collect(page)
        assert result == []

    @pytest.mark.asyncio
    async def test_collect_type_missing(self) -> None:
        page = _mock_page()
        page.evaluate.return_value = [
            '{"@context": "https://schema.org", "name": "NoType"}',
        ]
        result = await JsonLdCollector().collect(page)
        assert result[0]["type"] is None

    @pytest.mark.asyncio
    async def test_extract_type_with_list_empty(self) -> None:
        result = JsonLdCollector._extract_type({"@type": []})
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_type_non_dict(self) -> None:
        result = JsonLdCollector._extract_type([1, 2, 3])
        assert result is None


# ---------------------------------------------------------------------------
# LinksCollector
# ---------------------------------------------------------------------------


class TestLinksCollector:
    @pytest.mark.asyncio
    async def test_collect_links_with_normalisation(self) -> None:
        page = _mock_page(url="https://example.com/blog/post-1")
        page.evaluate.return_value = [
            {"href": "https://example.com/home", "text": "Home", "rel": ""},
            {"href": "/about", "text": "About", "rel": ""},
            {"href": "#section-1", "text": "Section 1", "rel": ""},
            {"href": "mailto:test@example.com", "text": "Email", "rel": ""},
            {"href": "https://external.com", "text": "External", "rel": "nofollow"},
            {"href": "/about", "text": "Duplicate About", "rel": ""},
        ]
        result = await LinksCollector().collect(page)
        # mailto should be filtered out, duplicate /about should be removed
        assert len(result) == 4
        urls = {r["resolved_url"] for r in result}
        assert "https://example.com/home" in urls
        assert "https://example.com/about" in urls
        assert "https://external.com" in urls

    @pytest.mark.asyncio
    async def test_collect_links_empty(self) -> None:
        page = _mock_page(url="https://example.com")
        page.evaluate.return_value = []
        result = await LinksCollector().collect(page)
        assert result == []

    @pytest.mark.asyncio
    async def test_classify_internal(self) -> None:
        assert LinksCollector._classify("https://example.com/page", True, False) == "internal"

    @pytest.mark.asyncio
    async def test_classify_external(self) -> None:
        assert LinksCollector._classify("https://external.com/page", False, False) == "external"

    @pytest.mark.asyncio
    async def test_classify_anchor(self) -> None:
        assert LinksCollector._classify("https://example.com/page#section", False, True) == "anchor"

    @pytest.mark.asyncio
    async def test_classify_other(self) -> None:
        assert LinksCollector._classify("ftp://example.com/file", None, None) == "other"


# ---------------------------------------------------------------------------
# ProductCollector
# ---------------------------------------------------------------------------


class TestProductCollector:
    @pytest.mark.asyncio
    async def test_collect_jsonld_product(self) -> None:
        page = _mock_page(url="https://example.com/product")
        page.evaluate.side_effect = [
            {
                "@type": "Product",
                "name": "Widget",
                "offers": {"price": "19.99", "priceCurrency": "USD"},
            },
            None,
            None,
            None,
            None,
        ]
        result = await ProductCollector().collect(page)
        assert len(result) == 1
        assert result[0]["source"] == "jsonld"
        assert result[0]["raw"]["name"] == "Widget"

    @pytest.mark.asyncio
    async def test_collect_empty(self) -> None:
        page = _mock_page(url="https://example.com")
        page.evaluate.side_effect = [None, None, None, None, None]
        result = await ProductCollector().collect(page, base_url="https://example.com")
        assert result == []

    @pytest.mark.asyncio
    async def test_collect_priority_chain(self) -> None:
        page = _mock_page(url="https://example.com")
        page.evaluate.side_effect = [
            None,  # jsonld
            {"og:title": "Widget", "og:type": "product"},  # opengraph
            None,
            None,
            None,
        ]
        result = await ProductCollector().collect(page, base_url="https://example.com")
        assert len(result) == 1
        assert result[0]["source"] == "opengraph"

    @pytest.mark.asyncio
    async def test_collect_eval_error_silently_continues(self) -> None:
        page = _mock_page(url="https://example.com")
        page.evaluate.side_effect = [
            RuntimeError("eval failed"),
            None,
            None,
            None,
            None,
        ]
        result = await ProductCollector().collect(page, base_url="https://example.com")
        assert result == []
