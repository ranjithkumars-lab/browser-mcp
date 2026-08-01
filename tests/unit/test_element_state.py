"""Tests for ElementState (exists, visible, enabled, editable, checked)."""

from __future__ import annotations

import pytest
from tests.fakes import FakeElement, FakeLocator, FakeLocatorProvider

from browser_mcp.browser.elements.state import ElementState

pytestmark = pytest.mark.unit


def _locator(*elements: FakeElement) -> FakeLocator:
    locator = FakeLocator("#x")
    locator.elements = list(elements)
    return locator


def _state() -> ElementState:
    return ElementState(FakeLocatorProvider())


async def test_exists_true_when_matched() -> None:
    assert await _state().exists(_locator(FakeElement())) is True


async def test_exists_false_when_no_match() -> None:
    assert await _state().exists(_locator()) is False


async def test_visible_honours_element() -> None:
    assert await _state().visible(_locator(FakeElement(visible=True))) is True
    assert await _state().visible(_locator(FakeElement(visible=False))) is False


async def test_enabled_honours_element() -> None:
    assert await _state().enabled(_locator(FakeElement(enabled=True))) is True
    assert await _state().enabled(_locator(FakeElement(enabled=False))) is False


async def test_editable_honours_element() -> None:
    assert await _state().editable(_locator(FakeElement(editable=True))) is True
    assert await _state().editable(_locator(FakeElement(editable=False))) is False


async def test_checked_honours_element() -> None:
    assert await _state().checked(_locator(FakeElement(checked=True))) is True
    assert await _state().checked(_locator(FakeElement(checked=False))) is False


async def test_state_on_missing_element_is_absent() -> None:
    checks = await _state().snapshot(_locator())
    assert checks == {
        "exists": False,
        "visible": False,
        "enabled": False,
        "editable": False,
        "checked": False,
    }


async def test_snapshot_reports_full_state() -> None:
    element = FakeElement(visible=True, enabled=True, editable=True, checked=True)
    checks = await _state().snapshot(_locator(element))
    assert checks["exists"] is True
    assert checks["visible"] is True
    assert checks["enabled"] is True
    assert checks["editable"] is True
    assert checks["checked"] is True
