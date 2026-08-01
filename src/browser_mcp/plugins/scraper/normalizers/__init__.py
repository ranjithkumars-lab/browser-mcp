"""Normaliser package — converts raw collector dicts into typed models."""

from __future__ import annotations

from browser_mcp.plugins.scraper.normalizers.images import ImagesNormalizer
from browser_mcp.plugins.scraper.normalizers.jsonld import JsonLdNormalizer
from browser_mcp.plugins.scraper.normalizers.links import LinksNormalizer
from browser_mcp.plugins.scraper.normalizers.metadata import MetadataNormalizer
from browser_mcp.plugins.scraper.normalizers.product import ProductNormalizer
from browser_mcp.plugins.scraper.normalizers.table import TableNormalizer
from browser_mcp.plugins.scraper.normalizers.text import TextNormalizer

__all__ = [
    "ImagesNormalizer",
    "JsonLdNormalizer",
    "LinksNormalizer",
    "MetadataNormalizer",
    "ProductNormalizer",
    "TableNormalizer",
    "TextNormalizer",
]
