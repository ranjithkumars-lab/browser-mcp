"""Scraper action implementations — the orchestration layer.

Each method implements the full pipeline:

    Tool → [Collector] → [Normalizer] → [Formatter] → PayloadSizer → Response

The actions receive a resolved Playwright page, run the collector(s), normalise
the raw output, format it to the requested output type, and decide inline vs
artifact storage.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from browser_mcp.browser.navigation.state import StateManager
from browser_mcp.errors import ExtractionError, ProductExtractionError, ScraperError
from browser_mcp.plugins.scraper.collectors.images import ImagesCollector
from browser_mcp.plugins.scraper.collectors.jsonld import JsonLdCollector
from browser_mcp.plugins.scraper.collectors.links import LinksCollector
from browser_mcp.plugins.scraper.collectors.metadata import MetadataCollector
from browser_mcp.plugins.scraper.collectors.product import ProductCollector
from browser_mcp.plugins.scraper.collectors.table import TableCollector
from browser_mcp.plugins.scraper.collectors.text import TextCollector
from browser_mcp.plugins.scraper.events import (
    emit_collect_completed,
    emit_format_completed,
    emit_scrape_completed,
    emit_scrape_failed,
    emit_scrape_started,
)
from browser_mcp.plugins.scraper.formatters import get_formatter
from browser_mcp.plugins.scraper.models import (
    ScrapeMeta,
    ScrapePayload,
)
from browser_mcp.plugins.scraper.normalizers.images import ImagesNormalizer
from browser_mcp.plugins.scraper.normalizers.jsonld import JsonLdNormalizer
from browser_mcp.plugins.scraper.normalizers.links import LinksNormalizer
from browser_mcp.plugins.scraper.normalizers.metadata import MetadataNormalizer
from browser_mcp.plugins.scraper.normalizers.product import ProductNormalizer
from browser_mcp.plugins.scraper.normalizers.table import TableNormalizer
from browser_mcp.plugins.scraper.normalizers.text import TextNormalizer
from browser_mcp.plugins.scraper.sizer import PayloadSizer
from enterprise_mcp.events.bus import EventBus

__all__ = ["ScraperActions"]


class ScraperActions:
    """Orchestrates the scrape pipeline for every MCP tool."""

    def __init__(
        self,
        state: StateManager,
        events: EventBus,
        sizer: PayloadSizer | None = None,
    ) -> None:
        self._state = state
        self._events = events
        self._sizer = sizer or PayloadSizer()
        self._text_collector = TextCollector()
        self._table_collector = TableCollector()
        self._image_collector = ImagesCollector()
        self._metadata_collector = MetadataCollector()
        self._jsonld_collector = JsonLdCollector()
        self._links_collector = LinksCollector()
        self._product_collector = ProductCollector()
        self._text_normalizer = TextNormalizer()
        self._table_normalizer = TableNormalizer()
        self._image_normalizer = ImagesNormalizer()
        self._metadata_normalizer = MetadataNormalizer()
        self._jsonld_normalizer = JsonLdNormalizer()
        self._links_normalizer = LinksNormalizer()
        self._product_normalizer = ProductNormalizer()

    # -- helpers -----------------------------------------------------------

    async def _resolve_page(self, session_id: str, page_id: str) -> tuple[Any, dict[str, Any]]:
        """Resolve a page handle and return ``(page, meta_dict)``."""
        handle = self._state.page_in_session(session_id, page_id)
        page = handle.page
        url = handle.state.url or page.url
        title: str | None = None
        try:
            title = await page.title()
        except Exception:
            title = None
        meta_dict: dict[str, Any] = {
            "session_id": session_id,
            "page_id": page_id,
            "url": url,
            "title": title,
            "timestamp": datetime.now(UTC),
        }
        return page, meta_dict

    async def _run_pipeline(
        self,
        session_id: str,
        page_id: str,
        tool_name: str,
        collector_name: str,
        collect_fn: Any,
        normalize_fn: Any,
        output_format: str = "json",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generic pipeline runner shared by all scrape tools.

        Parameters
        ----------
        collect_fn:
            Bound collector method, e.g. ``self._text_collector.collect``.
        normalize_fn:
            Bound normalizer method, e.g. ``self._text_normalizer.normalize``.
        """
        start = time.monotonic()
        await emit_scrape_started(
            self._events,
            tool=tool_name,
            session_id=session_id,
            page_id=page_id,
            url=None,
        )
        try:
            page, meta_dict = await self._resolve_page(session_id, page_id)
            url = meta_dict["url"]
            collect_start = time.monotonic()

            raw_items = await collect_fn(page, **kwargs)

            if raw_items and isinstance(raw_items[0], dict) and "_error" in raw_items[0]:
                raise ExtractionError(raw_items[0]["_error"])

            meta = ScrapeMeta(**meta_dict)
            models = [normalize_fn(ri, meta) for ri in raw_items]
            item_count = len(models)

            await emit_collect_completed(
                self._events,
                tool=tool_name,
                session_id=session_id,
                page_id=page_id,
                collectors=[collector_name],
                item_count=item_count,
                duration_ms=int((time.monotonic() - collect_start) * 1000),
            )

            formatter = get_formatter(output_format)
            formatted = formatter.format(models)
            size_bytes = len(formatted.encode("utf-8"))

            await emit_format_completed(
                self._events,
                tool=tool_name,
                session_id=session_id,
                page_id=page_id,
                output_format=output_format,
                inline=size_bytes <= self._sizer.threshold,
                size_bytes=size_bytes,
            )

            payload = self._sizer.decide(
                formatted,
                tool=tool_name,
                meta_dict=meta_dict,
                output_format=output_format,
                item_count=item_count,
            )
            payload.duration_ms = float((time.monotonic() - start) * 1000)

            await emit_scrape_completed(
                self._events,
                tool=tool_name,
                session_id=session_id,
                page_id=page_id,
                item_count=item_count,
                duration_ms=payload.duration_ms,
            )
            return self._payload_to_dict(payload, url)

        except ScraperError as exc:
            duration = (time.monotonic() - start) * 1000
            await emit_scrape_failed(
                self._events,
                tool=tool_name,
                session_id=session_id,
                page_id=page_id,
                error=str(exc),
                duration_ms=duration,
            )
            return self._error_dict(tool_name, session_id, page_id, str(exc), duration)
        except Exception as exc:
            duration = (time.monotonic() - start) * 1000
            await emit_scrape_failed(
                self._events,
                tool=tool_name,
                session_id=session_id,
                page_id=page_id,
                error=str(exc),
                duration_ms=duration,
            )
            raise

    def _payload_to_dict(self, payload: ScrapePayload, url: str | None) -> dict[str, Any]:
        d = payload.model_dump(mode="json")
        if payload.inline_data is not None:
            d["data"] = payload.inline_data
        else:
            d["data"] = None
        d["url"] = url
        return d

    def _error_dict(
        self, tool: str, session_id: str, page_id: str, error: str, duration_ms: float
    ) -> dict[str, Any]:
        return {
            "success": False,
            "tool": tool,
            "session_id": session_id,
            "page_id": page_id,
            "error": error,
            "timestamp": datetime.now(UTC).isoformat(),
            "duration_ms": round(duration_ms, 3),
        }

    # -- individual tool methods ------------------------------------------

    async def scrape_text(
        self,
        session_id: str,
        page_id: str,
        selector: str | None = None,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Extract visible text from the page body."""
        return await self._run_pipeline(
            session_id,
            page_id,
            "browser.scrape.text",
            self._text_collector.name,
            self._text_collector.collect,
            self._text_normalizer.normalize,
            output_format=output_format,
            selector=selector,
        )

    async def scrape_tables(
        self,
        session_id: str,
        page_id: str,
        selector: str | None = None,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Extract structured ``<table>`` data."""
        return await self._run_pipeline(
            session_id,
            page_id,
            "browser.scrape.tables",
            self._table_collector.name,
            self._table_collector.collect,
            self._table_normalizer.normalize,
            output_format=output_format,
            selector=selector,
        )

    async def scrape_images(
        self,
        session_id: str,
        page_id: str,
        selector: str | None = None,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Extract ``<img>`` tags with resolved URLs and dimensions."""
        return await self._run_pipeline(
            session_id,
            page_id,
            "browser.scrape.images",
            self._image_collector.name,
            self._image_collector.collect,
            self._image_normalizer.normalize,
            output_format=output_format,
            selector=selector,
        )

    async def scrape_metadata(
        self,
        session_id: str,
        page_id: str,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Extract ``<meta>``, ``<title>``, OpenGraph and Twitter card data."""
        return await self._run_pipeline(
            session_id,
            page_id,
            "browser.scrape.metadata",
            self._metadata_collector.name,
            self._metadata_collector.collect,
            self._metadata_normalizer.normalize,
            output_format=output_format,
        )

    async def scrape_jsonld(
        self,
        session_id: str,
        page_id: str,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Extract and parse ``application/ld+json`` blocks."""
        return await self._run_pipeline(
            session_id,
            page_id,
            "browser.scrape.jsonld",
            self._jsonld_collector.name,
            self._jsonld_collector.collect,
            self._jsonld_normalizer.normalize,
            output_format=output_format,
        )

    async def scrape_links(
        self,
        session_id: str,
        page_id: str,
        selector: str | None = None,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Extract ``<a>`` tags with normalised, de-duplicated URLs."""
        return await self._run_pipeline(
            session_id,
            page_id,
            "browser.scrape.links",
            self._links_collector.name,
            self._links_collector.collect,
            self._links_normalizer.normalize,
            output_format=output_format,
            selector=selector,
        )

    async def scrape_products(
        self,
        session_id: str,
        page_id: str,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Composite extraction: JSON-LD → OG → Microdata → DOM → Meta."""
        start = time.monotonic()
        await emit_scrape_started(
            self._events,
            tool="browser.scrape.products",
            session_id=session_id,
            page_id=page_id,
            url=None,
        )
        try:
            page, meta_dict = await self._resolve_page(session_id, page_id)
            collect_start = time.monotonic()

            raw_items = await self._product_collector.collect(page, base_url=meta_dict["url"])
            if not raw_items:
                raise ProductExtractionError(
                    "no product data could be extracted from any source signal"
                )

            models = [
                self._product_normalizer.normalize(ri, ScrapeMeta(**meta_dict)) for ri in raw_items
            ]

            await emit_collect_completed(
                self._events,
                tool="browser.scrape.products",
                session_id=session_id,
                page_id=page_id,
                collectors=[self._product_collector.name],
                item_count=len(models),
                duration_ms=int((time.monotonic() - collect_start) * 1000),
            )

            formatter = get_formatter(output_format)
            formatted = formatter.format(models)
            size_bytes = len(formatted.encode("utf-8"))

            await emit_format_completed(
                self._events,
                tool="browser.scrape.products",
                session_id=session_id,
                page_id=page_id,
                output_format=output_format,
                inline=size_bytes <= self._sizer.threshold,
                size_bytes=size_bytes,
            )

            payload = self._sizer.decide(
                formatted,
                tool="browser.scrape.products",
                meta_dict=meta_dict,
                output_format=output_format,
                item_count=len(models),
            )
            payload.duration_ms = float((time.monotonic() - start) * 1000)

            await emit_scrape_completed(
                self._events,
                tool="browser.scrape.products",
                session_id=session_id,
                page_id=page_id,
                item_count=len(models),
                duration_ms=payload.duration_ms,
            )
            return self._payload_to_dict(payload, meta_dict["url"])

        except ScraperError as exc:
            duration = (time.monotonic() - start) * 1000
            await emit_scrape_failed(
                self._events,
                tool="browser.scrape.products",
                session_id=session_id,
                page_id=page_id,
                error=str(exc),
                duration_ms=duration,
            )
            return self._error_dict(
                "browser.scrape.products", session_id, page_id, str(exc), duration
            )
