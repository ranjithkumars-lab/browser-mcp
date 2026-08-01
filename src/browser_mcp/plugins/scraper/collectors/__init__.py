"""Collector package for the scraper plugin.

Each collector extracts *raw* data from a Playwright page into plain Python
dicts.  Normalisers then convert the raw dicts into typed models.
"""

from __future__ import annotations

from browser_mcp.plugins.scraper.collectors.base import BaseCollector
from browser_mcp.plugins.scraper.collectors.images import ImagesCollector
from browser_mcp.plugins.scraper.collectors.jsonld import JsonLdCollector
from browser_mcp.plugins.scraper.collectors.links import LinksCollector
from browser_mcp.plugins.scraper.collectors.metadata import MetadataCollector
from browser_mcp.plugins.scraper.collectors.product import ProductCollector
from browser_mcp.plugins.scraper.collectors.table import TableCollector
from browser_mcp.plugins.scraper.collectors.text import TextCollector

__all__ = [
    "BaseCollector",
    "ImagesCollector",
    "JsonLdCollector",
    "LinksCollector",
    "MetadataCollector",
    "ProductCollector",
    "TableCollector",
    "TextCollector",
]
