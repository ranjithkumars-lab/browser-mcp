"""Tests for ElementProperties (text, html, attribute extractors)."""

from __future__ import annotations

import pytest
from tests.fakes import FakeElement, FakeLocator, FakeLocatorProvider

from browser_mcp.browser.elements.properties import ElementProperties

pytestmark = pytest.mark.unit


def _locator(*elements: FakeElement) -> FakeLocator:
    locator = FakeLocator("#x")
    locator.elements = list(elements)
    return locator


def _properties() -> ElementProperties:
    return ElementProperties(FakeLocatorProvider())


async def test_text_returns_inner_text() -> None:
    result = await _properties().text(_locator(FakeElement(text="hello world")))
    assert result == "hello world"


async def test_html_inner_by_default() -> None:
    element = FakeElement(text="x", tag="span", attrs={"data-html": "<b>bold</b>"})
    assert await _properties().html(_locator(element)) == "<b>bold</b>"


async def test_html_outer_flag() -> None:
    assert (
        await _properties().html(_locator(FakeElement(text="hi", tag="p")), outer=True)
        == "<p>hi</p>"
    )


async def test_attribute_returns_value() -> None:
    element = FakeElement(attrs={"href": "https://example.com", "title": "Home"})
    assert await _properties().attribute(_locator(element), "href") == "https://example.com"


async def test_attribute_missing_returns_none() -> None:
    assert await _properties().attribute(_locator(FakeElement()), "data-missing") is None
