"""Integration tests for the scraper plugin — full pipeline coverage.

Tests exercise the ``ScraperActions`` orchestration layer using a mock page
that simulates Playwright's ``evaluate`` for each collector's JS expression.
Each test verifies the end-to-end flow: Collector -> Normalizer -> Formatter
-> PayloadSizer -> Response dict.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from browser_mcp.browser.models import PageHandle, PageState
from browser_mcp.errors import ScraperError
from browser_mcp.plugins.scraper.actions import ScraperActions
from browser_mcp.plugins.scraper.sizer import PayloadSizer
from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.events.types import DomainEvent

pytestmark = pytest.mark.integration

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "html"


def _meta_dict() -> dict:
    return {
        "session_id": "s1",
        "page_id": "p1",
        "url": "https://example.com/page",
        "title": "Test Page",
        "timestamp": datetime.now(),
    }


class MockPage:
    """Minimal page stub returning scripted ``evaluate`` results."""

    def __init__(
        self,
        evaluate_results: list,
        url: str = "https://example.com/page",
        title: str = "Test Page",
    ):
        self._evaluate_results: list = list(evaluate_results)
        self._index = 0
        self._url = url
        self._title = title
        self.evaluate_call_count = 0

    @property
    def url(self) -> str:
        return self._url

    async def title(self) -> str:
        return self._title

    async def evaluate(self, expression: str, arg: object = None) -> object:
        self.evaluate_call_count += 1
        if self._index < len(self._evaluate_results):
            val = self._evaluate_results[self._index]
            self._index += 1
            return val
        return self._evaluate_results[-1] if self._evaluate_results else None


class MockStateManager:
    """Stand-in for ``StateManager`` returning a pre-bound page handle."""

    def __init__(self, page: MockPage) -> None:
        handle = PageHandle(
            page_id="p1",
            context_id="c1",
            browser_id="b1",
            page=page,  # type: ignore[arg-type]
            state=PageState(page_id="p1", context_id="c1", url=page.url),
        )
        self._handle = handle

    def page_in_session(self, session_id: str, page_id: str) -> PageHandle:
        return self._handle


def _build_actions(
    page: MockPage,
    *,
    threshold: int = 65536,
    artifact_dir: str | None = None,
) -> tuple[ScraperActions, MockStateManager, EventBus]:
    state = MockStateManager(page)
    events = EventBus()
    sizer = PayloadSizer(inline_threshold=threshold)
    if artifact_dir:
        sizer = PayloadSizer(inline_threshold=threshold, artifact_dir=artifact_dir)
    actions = ScraperActions(state=state, events=events, sizer=sizer)
    return actions, state, events


def _collect_events(events: EventBus) -> list[DomainEvent]:
    collected: list[DomainEvent] = []

    async def _handler(event: DomainEvent) -> None:
        collected.append(event)

    events.subscribe(None, _handler)
    return collected


# ---------------------------------------------------------------------------
# ScraperActions — scrape_text
# ---------------------------------------------------------------------------


class TestScrapeText:
    @pytest.mark.asyncio
    async def test_full_text_extraction(self) -> None:
        page = MockPage(
            evaluate_results=[
                {"text": "Hello World\nFoo bar", "word_count": 4, "char_count": 15},
            ]
        )
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_text("s1", "p1")
        assert result["success"] is True
        assert result["data"] is not None
        assert "Hello World" in result["data"]
        assert result["item_count"] == 1

    @pytest.mark.asyncio
    async def test_selector_text_extraction(self) -> None:
        page = MockPage(
            evaluate_results=[
                ["Heading", "Subheading"],
            ]
        )
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_text("s1", "p1", selector="h1, h2")
        assert result["success"] is True
        assert "Heading" in result["data"]

    @pytest.mark.asyncio
    async def test_csv_output_format(self) -> None:
        page = MockPage(
            evaluate_results=[{"text": "hello world", "word_count": 2, "char_count": 11}]
        )
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_text("s1", "p1", output_format="csv")
        assert result["success"] is True
        assert "hello world" in result["data"]

    @pytest.mark.asyncio
    async def test_markdown_output_format(self) -> None:
        page = MockPage(evaluate_results=[{"text": "hello", "word_count": 1, "char_count": 5}])
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_text("s1", "p1", output_format="markdown")
        assert result["success"] is True
        assert "hello" in result["data"]

    @pytest.mark.asyncio
    async def test_html_output_format(self) -> None:
        page = MockPage(evaluate_results=[{"text": "hello", "word_count": 1, "char_count": 5}])
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_text("s1", "p1", output_format="html")
        assert result["success"] is True
        assert "<!DOCTYPE html>" in result["data"]

    @pytest.mark.asyncio
    async def test_unsupported_format_raises(self) -> None:
        page = MockPage(evaluate_results=[{"text": "x", "word_count": 1, "char_count": 1}])
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_text("s1", "p1", output_format="xml")
        assert result["success"] is False
        assert "not yet implemented" in result["error"]

    @pytest.mark.asyncio
    async def test_scrape_started_event_emitted(self) -> None:
        page = MockPage(evaluate_results=[{"text": "x", "word_count": 1, "char_count": 1}])
        actions, _, events = _build_actions(page)
        collected = _collect_events(events)
        await actions.scrape_text("s1", "p1")
        names = [e.event_name for e in collected]
        assert "scrape.started" in names
        assert "scrape.collect.completed" in names
        assert "scrape.format.completed" in names
        assert "scrape.completed" in names


# ---------------------------------------------------------------------------
# ScraperActions — scrape_tables
# ---------------------------------------------------------------------------


class TestScrapeTables:
    @pytest.mark.asyncio
    async def test_full_table_extraction(self) -> None:
        page = MockPage(
            evaluate_results=[
                [
                    {
                        "index": 0,
                        "caption": "Users",
                        "rows": [
                            {
                                "cells": [
                                    {
                                        "value": "Name",
                                        "is_header": True,
                                        "col_span": 1,
                                        "row_span": 1,
                                    },
                                    {
                                        "value": "Age",
                                        "is_header": True,
                                        "col_span": 1,
                                        "row_span": 1,
                                    },
                                ]
                            },
                            {
                                "cells": [
                                    {
                                        "value": "Alice",
                                        "is_header": False,
                                        "col_span": 1,
                                        "row_span": 1,
                                    },
                                    {
                                        "value": "30",
                                        "is_header": False,
                                        "col_span": 1,
                                        "row_span": 1,
                                    },
                                ]
                            },
                        ],
                    },
                ],
            ]
        )
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_tables("s1", "p1")
        assert result["success"] is True
        assert "Users" in result["data"]
        assert "Alice" in result["data"]
        assert result["item_count"] == 1


# ---------------------------------------------------------------------------
# ScraperActions — scrape_images
# ---------------------------------------------------------------------------


class TestScrapeImages:
    @pytest.mark.asyncio
    async def test_full_image_extraction(self) -> None:
        page = MockPage(
            evaluate_results=[
                [
                    {
                        "src": "/hero.jpg",
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
                    {
                        "src": "/decorative.png",
                        "current_src": "",
                        "alt": "",
                        "loading": "lazy",
                        "width": 0,
                        "height": 0,
                        "natural_width": 0,
                        "natural_height": 0,
                        "complete": True,
                        "decoded": True,
                        "is_decorative": True,
                    },
                ],
            ]
        )
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_images("s1", "p1")
        assert result["success"] is True
        assert "hero.jpg" in result["data"]
        assert result["item_count"] == 2


# ---------------------------------------------------------------------------
# ScraperActions — scrape_metadata
# ---------------------------------------------------------------------------


class TestScrapeMetadata:
    @pytest.mark.asyncio
    async def test_full_metadata_extraction(self) -> None:
        page = MockPage(
            evaluate_results=[
                {
                    "title": "My Page",
                    "description": "A description",
                    "keywords": "key1, key2",
                    "og": {"og:title": "My Page", "og:type": "article"},
                    "twitter": {"twitter:card": "summary"},
                    "other": {"author": "John"},
                },
            ]
        )
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_metadata("s1", "p1")
        assert result["success"] is True
        assert "My Page" in result["data"]
        assert "A description" in result["data"]
        assert result["item_count"] == 1


# ---------------------------------------------------------------------------
# ScraperActions — scrape_jsonld
# ---------------------------------------------------------------------------


class TestScrapeJsonLd:
    @pytest.mark.asyncio
    async def test_full_jsonld_extraction(self) -> None:
        page = MockPage(
            evaluate_results=[
                [
                    '{"@context": "https://schema.org/", "@type": "Product", "name": "Widget"}',
                    '{"@context": "https://schema.org/", "@type": "Organization", "name": "Acme"}',
                ],
            ]
        )
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_jsonld("s1", "p1")
        assert result["success"] is True
        assert "Widget" in result["data"]
        assert result["item_count"] == 2


# ---------------------------------------------------------------------------
# ScraperActions — scrape_links
# ---------------------------------------------------------------------------


class TestScrapeLinks:
    @pytest.mark.asyncio
    async def test_full_links_extraction(self) -> None:
        page = MockPage(
            url="https://example.com/blog/post-1",
            evaluate_results=[
                [
                    {"href": "https://example.com/home", "text": "Home", "rel": ""},
                    {"href": "/about", "text": "About", "rel": ""},
                    {"href": "#section-1", "text": "Section 1", "rel": ""},
                    {"href": "mailto:test@example.com", "text": "Email", "rel": ""},
                    {"href": "https://external.com", "text": "External", "rel": "nofollow"},
                ],
            ],
        )
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_links("s1", "p1")
        assert result["success"] is True
        assert "example.com/about" in result["data"]
        assert "external.com" in result["data"]
        assert "mailto" not in result["data"]
        assert result["item_count"] == 4


# ---------------------------------------------------------------------------
# ScraperActions — scrape_products
# ---------------------------------------------------------------------------


class TestScrapeProducts:
    @pytest.mark.asyncio
    async def test_jsonld_product(self) -> None:
        page = MockPage(
            url="https://shop.example.com/product",
            evaluate_results=[
                {
                    "@type": "Product",
                    "name": "Widget",
                    "offers": {"price": "19.99", "priceCurrency": "USD"},
                },
                None,  # og
                None,  # microdata
                None,  # dom
                None,  # meta
            ],
        )
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_products("s1", "p1")
        assert result["success"] is True
        assert "Widget" in result["data"]
        assert "jsonld" in result["data"]

    @pytest.mark.asyncio
    async def test_no_product_data_raises(self) -> None:
        page = MockPage(url="https://example.com", evaluate_results=[None, None, None, None, None])
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_products("s1", "p1")
        assert result["success"] is False
        assert "no product data" in result["error"]

    @pytest.mark.asyncio
    async def test_og_product(self) -> None:
        page = MockPage(
            url="https://example.com",
            evaluate_results=[
                None,
                {
                    "og:type": "product",
                    "og:title": "Gadget",
                    "og:price:amount": "49.99",
                    "og:price:currency": "EUR",
                },
                None,
                None,
                None,
            ],
        )
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_products("s1", "p1")
        assert result["success"] is True
        assert "opengraph" in result["data"]

    @pytest.mark.asyncio
    async def test_product_error_emits_failed_event(self) -> None:
        page = MockPage(url="https://example.com", evaluate_results=[None, None, None, None, None])
        actions, _, events = _build_actions(page)
        collected = _collect_events(events)
        result = await actions.scrape_products("s1", "p1")
        assert result["success"] is False
        names = [e.event_name for e in collected]
        assert "scrape.started" in names
        assert "scrape.failed" in names


# ---------------------------------------------------------------------------
# PayloadSizer integration (artifact storage)
# ---------------------------------------------------------------------------


class TestArtifactStorage:
    @pytest.mark.asyncio
    async def test_large_payload_stored_as_artifact(self, tmp_path: Path) -> None:
        page = MockPage(evaluate_results=[{"text": "x" * 200, "word_count": 1, "char_count": 200}])
        actions, _, _ = _build_actions(page, threshold=10, artifact_dir=str(tmp_path))
        result = await actions.scrape_text("s1", "p1")
        assert result["success"] is True
        assert result["inline_data"] is None
        assert result["artifact_path"] is not None
        assert Path(result["artifact_path"]).exists()

    @pytest.mark.asyncio
    async def test_small_payload_inline(self) -> None:
        page = MockPage(evaluate_results=[{"text": "hi", "word_count": 1, "char_count": 2}])
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_text("s1", "p1")
        assert result["success"] is True
        assert result["inline_data"] is not None
        assert result["artifact_path"] is None


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_page_resolution_failure(self) -> None:
        state = MagicMock()
        state.page_in_session = MagicMock(side_effect=ScraperError("page not found"))
        events = EventBus()
        actions = ScraperActions(state=state, events=events)
        result = await actions.scrape_text("s1", "p1")
        assert result["success"] is False
        assert "page not found" in result["error"]

    @pytest.mark.asyncio
    async def test_extraction_error_in_pipeline(self) -> None:
        page = MockPage(evaluate_results=[{"_error": "JS evaluation failed", "_collector": "text"}])
        actions, _, _ = _build_actions(page)
        result = await actions.scrape_text("s1", "p1")
        assert result["success"] is False
        assert "JS evaluation failed" in result["error"]

    @pytest.mark.asyncio
    async def test_unexpected_exception_reraises(self) -> None:
        page = MockPage(evaluate_results=[])
        page.evaluate = AsyncMock(side_effect=RuntimeError("unexpected"))
        actions, _, _ = _build_actions(page)
        with pytest.raises(RuntimeError, match="unexpected"):
            await actions.scrape_text("s1", "p1")
