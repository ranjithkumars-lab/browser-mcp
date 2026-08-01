"""Unit tests for scraper pipeline formatters."""

from __future__ import annotations

import json

import pytest

from browser_mcp.errors import FormattingError
from browser_mcp.plugins.scraper.formatters import FORMATTERS, get_formatter
from browser_mcp.plugins.scraper.formatters.base import BaseFormatter
from browser_mcp.plugins.scraper.formatters.csv import CsvFormatter
from browser_mcp.plugins.scraper.formatters.html import HtmlFormatter
from browser_mcp.plugins.scraper.formatters.json import JsonFormatter
from browser_mcp.plugins.scraper.formatters.markdown import MarkdownFormatter
from browser_mcp.plugins.scraper.formatters.xml import XmlFormatter
from browser_mcp.plugins.scraper.formatters.yaml import YamlFormatter
from browser_mcp.plugins.scraper.models import (
    ImageResult,
    JsonLdResult,
    LinkResult,
    MetadataResult,
    ProductResult,
    ScrapeMeta,
    TableCell,
    TableResult,
    TableRow,
    TextResult,
)

pytestmark = pytest.mark.unit

_META = ScrapeMeta(
    session_id="s1",
    page_id="p1",
    url="https://example.com",
    title="Test",
)


# ---------------------------------------------------------------------------
# get_formatter / FORMATTERS registry
# ---------------------------------------------------------------------------


class TestFormatterRegistry:
    def test_get_formatter_json(self) -> None:
        fmt = get_formatter("json")
        assert isinstance(fmt, JsonFormatter)

    def test_get_formatter_csv(self) -> None:
        fmt = get_formatter("csv")
        assert isinstance(fmt, CsvFormatter)

    def test_get_formatter_markdown(self) -> None:
        fmt = get_formatter("markdown")
        assert isinstance(fmt, MarkdownFormatter)

    def test_get_formatter_html(self) -> None:
        fmt = get_formatter("html")
        assert isinstance(fmt, HtmlFormatter)

    def test_get_formatter_unsupported(self) -> None:
        with pytest.raises(FormattingError, match="unsupported output format"):
            get_formatter("xml")

    def test_get_formatter_case_insensitive(self) -> None:
        fmt = get_formatter("JSON")
        assert isinstance(fmt, JsonFormatter)

    def test_format_name_property(self) -> None:
        assert JsonFormatter().format_name == "json"
        assert CsvFormatter().format_name == "csv"
        assert MarkdownFormatter().format_name == "markdown"
        assert HtmlFormatter().format_name == "html"


# ---------------------------------------------------------------------------
# JsonFormatter
# ---------------------------------------------------------------------------


class TestJsonFormatter:
    def test_format_text_result(self) -> None:
        model = TextResult(meta=_META, text="hello world", word_count=2, char_count=11)
        result = JsonFormatter().format([model])
        data = json.loads(result)
        assert data[0]["text"] == "hello world"
        assert data[0]["word_count"] == 2

    def test_format_table_result(self) -> None:
        model = TableResult(
            meta=_META,
            index=0,
            caption="T",
            headers=["A", "B"],
            rows=[TableRow(cells=[TableCell(value="1"), TableCell(value="2")])],
            row_count=1,
            col_count=2,
        )
        result = JsonFormatter().format([model])
        data = json.loads(result)
        assert data[0]["headers"] == ["A", "B"]
        assert data[0]["row_count"] == 1

    def test_format_datetime_serialised(self) -> None:
        model = TextResult(meta=_META, text="x", word_count=1, char_count=1)
        result = JsonFormatter().format([model])
        data = json.loads(result)
        assert "timestamp" in data[0]["meta"]


# ---------------------------------------------------------------------------
# CsvFormatter
# ---------------------------------------------------------------------------


class TestCsvFormatter:
    def test_format_with_models(self) -> None:
        model = LinkResult(
            meta=_META,
            href="/about",
            resolved_url="https://example.com/about",
            text="About",
        )
        result = CsvFormatter().format([model])
        assert "About" in result
        assert "/about" in result

    def test_format_empty(self) -> None:
        assert CsvFormatter().format([]) == ""

    def test_format_with_dict(self) -> None:
        result = CsvFormatter().format([{"name": "test", "value": "123"}])
        assert "test" in result
        assert "123" in result


# ---------------------------------------------------------------------------
# MarkdownFormatter
# ---------------------------------------------------------------------------


class TestMarkdownFormatter:
    def test_format_simple_model(self) -> None:
        model = TextResult(meta=_META, text="hello", word_count=1, char_count=5)
        result = MarkdownFormatter().format([model])
        assert "hello" in result
        assert "| Field | Value |" in result

    def test_format_empty(self) -> None:
        assert MarkdownFormatter().format([]) == ""

    def test_format_nested_list(self) -> None:
        model = MetadataResult(
            meta=_META,
            title="T",
            og={"og:title": "T"},
            twitter={},
            other={},
        )
        result = MarkdownFormatter().format([model])
        assert "og" in result.lower() or "og:title" in result

    def test_multiple_items_separated(self) -> None:
        m1 = TextResult(meta=_META, text="first", word_count=1, char_count=5)
        m2 = TextResult(meta=_META, text="second", word_count=1, char_count=6)
        result = MarkdownFormatter().format([m1, m2])
        assert "first" in result
        assert "second" in result


# ---------------------------------------------------------------------------
# HtmlFormatter
# ---------------------------------------------------------------------------


class TestHtmlFormatter:
    def test_format_wraps_in_doctype(self) -> None:
        model = TextResult(meta=_META, text="hello", word_count=1, char_count=5)
        result = HtmlFormatter().format([model])
        assert "<!DOCTYPE html>" in result
        assert "</body></html>" in result

    def test_format_escapes_content(self) -> None:
        model = TextResult(meta=_META, text="<script>alert(1)</script>", word_count=1, char_count=25)
        result = HtmlFormatter().format([model])
        assert "<script>alert(1)</script>" not in result or "&lt;script&gt;" in result

    def test_format_empty(self) -> None:
        result = HtmlFormatter().format([])
        assert "<!DOCTYPE html>" in result

    def test_format_image_result(self) -> None:
        model = ImageResult(
            meta=_META,
            src="/img.png",
            resolved_url="https://example.com/img.png",
            alt="An image",
        )
        result = HtmlFormatter().format([model])
        assert "/img.png" in result
        assert "An image" in result


# ---------------------------------------------------------------------------
# Reserved scaffolds
# ---------------------------------------------------------------------------


class TestReservedFormatters:
    def test_yaml_raises(self) -> None:
        with pytest.raises(FormattingError, match="not yet implemented"):
            YamlFormatter().format([])

    def test_xml_raises(self) -> None:
        with pytest.raises(FormattingError, match="not yet implemented"):
            XmlFormatter().format([])


# ---------------------------------------------------------------------------
# BaseFormatter
# ---------------------------------------------------------------------------


class TestBaseFormatter:
    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            BaseFormatter()  # type: ignore[abstract]
