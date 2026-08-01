"""Tests for the element error hierarchy."""

from __future__ import annotations

import pytest

from browser_mcp.errors import (
    BrowserError,
    ElementError,
    ElementNotFoundError,
    ElementStateError,
    InvalidLocatorStrategyError,
    PageError,
    StaleElementReferenceError,
)

pytestmark = pytest.mark.unit


async def test_element_error_is_a_page_and_browser_error() -> None:
    assert issubclass(ElementError, PageError)
    assert issubclass(ElementError, BrowserError)


async def test_all_specific_errors_derive_from_element_error() -> None:
    for error in (
        ElementNotFoundError,
        ElementStateError,
        InvalidLocatorStrategyError,
        StaleElementReferenceError,
    ):
        assert issubclass(error, ElementError)
        assert issubclass(error, BrowserError)


async def test_errors_carry_readable_messages() -> None:
    assert "not found" in str(ElementNotFoundError("element not found"))
    assert "strict" in str(ElementStateError("strict match required"))
    assert "strategy" in str(InvalidLocatorStrategyError("unknown strategy 'bogus'"))
    assert "stale" in str(StaleElementReferenceError("element is stale"))
