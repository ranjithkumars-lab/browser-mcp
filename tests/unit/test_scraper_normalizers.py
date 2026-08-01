"""Unit tests for scraper pipeline normalisers."""

from __future__ import annotations

import pytest

from browser_mcp.plugins.scraper.models import ScrapeMeta
from browser_mcp.plugins.scraper.normalizers.images import ImagesNormalizer
from browser_mcp.plugins.scraper.normalizers.jsonld import JsonLdNormalizer
from browser_mcp.plugins.scraper.normalizers.links import LinksNormalizer
from browser_mcp.plugins.scraper.normalizers.metadata import MetadataNormalizer
from browser_mcp.plugins.scraper.normalizers.product import ProductNormalizer
from browser_mcp.plugins.scraper.normalizers.table import TableNormalizer
from browser_mcp.plugins.scraper.normalizers.text import TextNormalizer

pytestmark = pytest.mark.unit

_META = ScrapeMeta(
    session_id="s1",
    page_id="p1",
    url="https://example.com/page",
    title="Test Page",
)


# ---------------------------------------------------------------------------
# TextNormalizer
# ---------------------------------------------------------------------------


class TestTextNormalizer:
    def test_full_text(self) -> None:
        raw = {"text": "Hello   World\nFoo", "word_count": 3, "char_count": 14}
        result = TextNormalizer().normalize(raw, _META)
        assert result.text == "Hello World Foo"
        assert result.word_count == 3
        assert result.char_count == 14
        assert result.meta is _META

    def test_selector_text(self) -> None:
        raw = {"texts": ["Alpha", "Beta"]}
        result = TextNormalizer().normalize(raw, _META)
        assert result.text == "Alpha Beta"
        assert result.word_count == 2
        assert result.selectors_only == []

    def test_empty_text(self) -> None:
        result = TextNormalizer().normalize({}, _META)
        assert result.text == ""
        assert result.word_count == 0
        assert result.char_count == 0

    def test_missing_char_count_uses_default(self) -> None:
        raw = {"text": "hello world"}
        result = TextNormalizer().normalize(raw, _META)
        assert result.char_count == 11


# ---------------------------------------------------------------------------
# TableNormalizer
# ---------------------------------------------------------------------------


class TestTableNormalizer:
    def test_normalize_with_headers(self) -> None:
        raw = {
            "index": 0,
            "caption": "Users",
            "rows": [
                {
                    "cells": [
                        {"value": "Name", "is_header": True, "col_span": 1, "row_span": 1},
                        {"value": "Age", "is_header": True, "col_span": 1, "row_span": 1},
                    ]
                },
                {
                    "cells": [
                        {"value": "Alice", "is_header": False, "col_span": 1, "row_span": 1},
                        {"value": "30", "is_header": False, "col_span": 1, "row_span": 1},
                    ]
                },
            ],
        }
        result = TableNormalizer().normalize(raw, _META)
        assert result.index == 0
        assert result.caption == "Users"
        assert "Name" in result.headers
        assert "Age" in result.headers
        assert result.row_count == 1
        assert result.col_count == 2

    def test_normalize_no_headers(self) -> None:
        raw = {
            "index": 1,
            "caption": "",
            "rows": [
                {"cells": [{"value": "a", "is_header": False}, {"value": "b", "is_header": False}]},
                {"cells": [{"value": "c", "is_header": False}, {"value": "d", "is_header": False}]},
            ],
        }
        result = TableNormalizer().normalize(raw, _META)
        assert result.headers == ["a", "b"]
        assert result.row_count == 2

    def test_normalize_empty_rows(self) -> None:
        raw = {"index": 0, "caption": None, "rows": []}
        result = TableNormalizer().normalize(raw, _META)
        assert result.row_count == 0
        assert result.col_count == 0
        assert result.caption is None

    def test_normalize_missing_caption(self) -> None:
        raw = {"rows": []}
        result = TableNormalizer().normalize(raw, _META)
        assert result.caption is None

    def test_normalize_colspan_rowspan(self) -> None:
        raw = {
            "index": 0,
            "rows": [
                {"cells": [{"value": "A", "is_header": True, "col_span": 2, "row_span": 1}]},
            ],
        }
        result = TableNormalizer().normalize(raw, _META)
        assert "A" in result.headers


# ---------------------------------------------------------------------------
# ImagesNormalizer
# ---------------------------------------------------------------------------


class TestImagesNormalizer:
    def test_full_image(self) -> None:
        raw = {
            "src": "/hero.jpg",
            "resolved_url": "https://example.com/hero.jpg",
            "alt": "Hero",
            "loading": "eager",
            "width": 1200,
            "height": 400,
            "natural_width": 1200,
            "natural_height": 400,
            "complete": True,
            "is_decorative": False,
        }
        result = ImagesNormalizer().normalize(raw, _META)
        assert result.src == "/hero.jpg"
        assert result.resolved_url == "https://example.com/hero.jpg"
        assert result.alt == "Hero"
        assert result.width == 1200
        assert result.complete is True

    def test_default_values(self) -> None:
        raw = {"src": "/img.png", "resolved_url": "https://example.com/img.png"}
        result = ImagesNormalizer().normalize(raw, _META)
        assert result.alt is None
        assert result.loading is None
        assert result.width is None
        assert result.complete is True
        assert result.is_decorative is False

    def test_string_numeric_values(self) -> None:
        raw = {
            "src": "/img.png",
            "resolved_url": "https://example.com/img.png",
            "width": "100",
            "height": "50",
            "natural_width": "200",
            "natural_height": "100",
        }
        result = ImagesNormalizer().normalize(raw, _META)
        assert result.width == 100
        assert result.height == 50

    def test_invalid_numeric_values(self) -> None:
        raw = {
            "src": "/img.png",
            "resolved_url": "",
            "width": "abc",
        }
        result = ImagesNormalizer().normalize(raw, _META)
        assert result.width is None


# ---------------------------------------------------------------------------
# MetadataNormalizer
# ---------------------------------------------------------------------------


class TestMetadataNormalizer:
    def test_full_metadata(self) -> None:
        raw = {
            "title": "My Page",
            "description": "A description",
            "keywords": "key1, key2",
            "og": {"og:title": "My Page", "og:type": "article"},
            "twitter": {"twitter:card": "summary"},
            "other": {"author": "John"},
        }
        result = MetadataNormalizer().normalize(raw, _META)
        assert result.title == "My Page"
        assert result.description == "A description"
        assert result.keywords == "key1, key2"
        assert result.og["og:title"] == "My Page"
        assert result.twitter["twitter:card"] == "summary"
        assert result.other["author"] == "John"

    def test_empty_og_twitter_other(self) -> None:
        raw = {"title": "T"}
        result = MetadataNormalizer().normalize(raw, _META)
        assert result.og == {}
        assert result.twitter == {}
        assert result.other == {}

    def test_none_values(self) -> None:
        raw = {"title": "T", "description": None, "keywords": None, "og": None}
        result = MetadataNormalizer().normalize(raw, _META)
        assert result.description is None
        assert result.keywords is None
        assert result.og == {}


# ---------------------------------------------------------------------------
# JsonLdNormalizer
# ---------------------------------------------------------------------------


class TestJsonLdNormalizer:
    def test_full_jsonld(self) -> None:
        raw = {
            "raw": '{"@type": "Product"}',
            "data": {"@context": "https://schema.org", "@type": "Product", "name": "X"},
            "type": "Product",
        }
        result = JsonLdNormalizer().normalize(raw, _META)
        assert result.raw == '{"@type": "Product"}'
        assert result.data["@type"] == "Product"
        assert result.type == "Product"

    def test_parse_error(self) -> None:
        raw = {"raw": "bad", "data": {}, "type": None, "_parse_error": "boom"}
        result = JsonLdNormalizer().normalize(raw, _META)
        assert result.data == {}
        assert result.type is None

    def test_default_values(self) -> None:
        result = JsonLdNormalizer().normalize({}, _META)
        assert result.raw == ""
        assert result.data == {}


# ---------------------------------------------------------------------------
# LinksNormalizer
# ---------------------------------------------------------------------------


class TestLinksNormalizer:
    def test_full_link(self) -> None:
        raw = {
            "href": "/about",
            "resolved_url": "https://example.com/about",
            "text": "About Us",
            "rel": "nofollow",
            "is_internal": True,
            "is_anchor": False,
            "link_type": "internal",
        }
        result = LinksNormalizer().normalize(raw, _META)
        assert result.href == "/about"
        assert result.resolved_url == "https://example.com/about"
        assert result.text == "About Us"
        assert result.rel == "nofollow"
        assert result.is_internal is True
        assert result.link_type == "internal"

    def test_invalid_link_type_falls_back(self) -> None:
        raw = {
            "href": "/x",
            "resolved_url": "https://example.com/x",
            "text": "X",
            "link_type": "bogus",
        }
        result = LinksNormalizer().normalize(raw, _META)
        assert result.link_type == "other"

    def test_default_values(self) -> None:
        raw = {"href": "#", "text": ""}
        result = LinksNormalizer().normalize(raw, _META)
        assert result.rel is None
        assert result.is_internal is None
        assert result.link_type == "other"


# ---------------------------------------------------------------------------
# ProductNormalizer
# ---------------------------------------------------------------------------


class TestProductNormalizer:
    def test_jsonld_product(self) -> None:
        raw = {
            "raw": {
                "name": "Widget",
                "offers": {"price": "19.99", "priceCurrency": "USD"},
                "brand": {"name": "Acme"},
                "sku": "W-1",
            },
            "source": "jsonld",
            "base_url": "https://shop.example.com",
        }
        result = ProductNormalizer().normalize(raw, _META)
        assert result.name == "Widget"
        assert result.price == 19.99
        assert result.currency == "USD"
        assert result.brand == "Acme"
        assert result.sku == "W-1"
        assert result.source == "jsonld"
        assert result.url == "https://shop.example.com/W-1"

    def test_price_with_currency_symbol(self) -> None:
        raw = {
            "raw": {"price": "$1,299.99"},
            "source": "dom",
            "base_url": "https://example.com",
        }
        result = ProductNormalizer().normalize(raw, _META)
        assert result.price == 1299.99

    def test_image_url_resolution(self) -> None:
        raw = {
            "raw": {"image": "/products/main.jpg", "url": "/products/item"},
            "source": "jsonld",
            "base_url": "https://shop.example.com",
        }
        result = ProductNormalizer().normalize(raw, _META)
        assert result.image == "https://shop.example.com/products/main.jpg"
        assert result.url == "https://shop.example.com/products/item"

    def test_nested_keys(self) -> None:
        raw = {
            "raw": {
                "brand": {"name": "BrandCo"},
                "offers": {"price": "49.00"},
                "aggregateRating": {"ratingValue": "4.5", "reviewCount": "10"},
            },
            "source": "jsonld",
            "base_url": "https://example.com",
        }
        result = ProductNormalizer().normalize(raw, _META)
        assert result.brand == "BrandCo"
        assert result.price == 49.0
        assert result.rating_value == 4.5
        assert result.rating_count == 10

    def test_empty_raw(self) -> None:
        raw = {"raw": {}, "source": "unknown", "base_url": "https://example.com"}
        result = ProductNormalizer().normalize(raw, _META)
        assert result.name is None
        assert result.price is None

    def test_availability_and_condition(self) -> None:
        raw = {
            "raw": {
                "availability": "https://schema.org/InStock",
                "itemCondition": "https://schema.org/NewCondition",
            },
            "source": "jsonld",
            "base_url": "https://example.com",
        }
        result = ProductNormalizer().normalize(raw, _META)
        assert "InStock" in result.availability or result.availability is not None
        assert result.condition is not None
