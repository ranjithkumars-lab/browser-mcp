"""Typed output models for the Web Scraping Plugin.

All structured results returned by scraper tools are instances of the models
defined here. They are plain Pydantic models so they can be serialised to any
output format by the formatters.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

__all__ = [
    "ImageResult",
    "JsonLdResult",
    "LinkResult",
    "MetadataResult",
    "ProductResult",
    "ScrapeMeta",
    "ScrapePayload",
    "TableCell",
    "TableResult",
    "TableRow",
    "TextResult",
]


class ScrapeMeta(BaseModel):
    """Shared metadata attached to every scrape result."""

    session_id: str
    page_id: str
    url: str | None = None
    title: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TextResult(BaseModel):
    """Extracted visible text from the page body."""

    meta: ScrapeMeta
    text: str
    word_count: int = 0
    char_count: int = 0
    selectors_only: list[str] = Field(default_factory=list[str])


class TableCell(BaseModel):
    """A single cell within a table row."""

    value: str
    is_header: bool = False
    col_span: int = 1
    row_span: int = 1


class TableRow(BaseModel):
    """A row within a table."""

    cells: list[TableCell] = Field(default_factory=list[TableCell])


class TableResult(BaseModel):
    """Structured data extracted from a single ``<table>`` element."""

    meta: ScrapeMeta
    index: int
    caption: str | None = None
    headers: list[str] = Field(default_factory=list[str])
    rows: list[TableRow] = Field(default_factory=list[TableRow])
    row_count: int = 0
    col_count: int = 0


class ImageResult(BaseModel):
    """Information about a single ``<img>`` element."""

    meta: ScrapeMeta
    src: str
    resolved_url: str
    alt: str | None = None
    loading: str | None = None
    width: int | None = None
    height: int | None = None
    natural_width: int | None = None
    natural_height: int | None = None
    complete: bool = True
    is_decorative: bool = False


class LinkResult(BaseModel):
    """Information about a single ``<a>`` element."""

    meta: ScrapeMeta
    href: str
    resolved_url: str
    text: str
    rel: str | None = None
    is_internal: bool | None = None
    is_anchor: bool | None = None
    link_type: Literal["internal", "external", "anchor", "other"] = "other"


class MetadataResult(BaseModel):
    """Page-level metadata extracted from ``<meta>``, ``<title>`` and friends."""

    meta: ScrapeMeta
    title: str
    description: str | None = None
    keywords: str | None = None
    og: dict[str, str] = Field(default_factory=dict)
    twitter: dict[str, str] = Field(default_factory=dict)
    other: dict[str, str] = Field(default_factory=dict)


class JsonLdResult(BaseModel):
    """Parsed ``application/ld+json`` block."""

    meta: ScrapeMeta
    raw: str
    data: dict[str, Any]
    type: str | None = None


class ProductResult(BaseModel):
    """A product extracted through the composite collector."""

    meta: ScrapeMeta
    name: str | None = None
    description: str | None = None
    price: float | None = None
    currency: str | None = None
    brand: str | None = None
    sku: str | None = None
    availability: str | None = None
    condition: str | None = None
    image: str | None = None
    url: str | None = None
    rating_value: float | None = None
    rating_count: int | None = None
    source: str = "jsonld"
    raw: dict[str, Any] = Field(default_factory=dict[str, Any])


class ScrapePayload(BaseModel):
    """Serialisable envelope returned to the MCP client.

    When the formatted output exceeds the inline size threshold the data is
    stored to an artifact file and ``artifact_path`` / ``artifact_size`` are
    set instead of ``inline_data``.
    """

    success: bool = True
    tool: str
    meta: ScrapeMeta
    format: str = "json"
    inline_data: str | None = None
    artifact_path: str | None = None
    artifact_size: int | None = None
    item_count: int = 0
    duration_ms: float = 0.0
    error: str | None = None
