"""Tests for the locator registry and individual strategies."""

from __future__ import annotations

import pytest
from tests.fakes import FakeElement, FakeLocator, FakeLocatorProvider, FakePage
from tests.helpers import build_runtime

from browser_mcp.browser.elements.locators.aria import AriaStrategy
from browser_mcp.browser.elements.locators.css import CssStrategy
from browser_mcp.browser.elements.locators.playwright import PlaywrightStrategy
from browser_mcp.browser.elements.locators.registry import LocatorRegistry
from browser_mcp.browser.elements.locators.text import TextStrategy
from browser_mcp.browser.elements.locators.xpath import XPathStrategy
from browser_mcp.browser.elements.models import LocatorModel
from browser_mcp.errors import (
    ElementNotFoundError,
    ElementStateError,
    InvalidLocatorStrategyError,
)

pytestmark = pytest.mark.unit


async def test_registry_registers_default_strategies() -> None:
    registry = LocatorRegistry(FakeLocatorProvider())
    assert set(registry.names()) == {"css", "xpath", "aria", "text", "playwright"}


async def test_registry_returns_unknown_strategy_error() -> None:
    registry = LocatorRegistry(FakeLocatorProvider())
    with pytest.raises(InvalidLocatorStrategyError):
        registry.get("bogus")


async def test_registry_register_custom_strategy() -> None:
    registry = LocatorRegistry(FakeLocatorProvider(), register_defaults=False)

    class Custom(CssStrategy):
        name = "custom"

    registry.register(Custom(FakeLocatorProvider()))
    assert registry.names() == ["custom"]


async def test_css_strategy_builds_css_locator() -> None:
    runtime = await build_runtime()
    locator = runtime["registry"].build(runtime["page"], LocatorModel(strategy="css", value="#a"))
    assert isinstance(locator, FakeLocator)
    assert locator.selector == "#a"
    assert locator.frame is None


async def test_xpath_strategy_builds_xpath_locator() -> None:
    runtime = await build_runtime()
    locator = runtime["registry"].build(
        runtime["page"], LocatorModel(strategy="xpath", value="//div")
    )
    assert locator.selector == "xpath=//div"


async def test_text_strategy_builds_exact_text_locator() -> None:
    runtime = await build_runtime()
    locator = runtime["registry"].build(
        runtime["page"], LocatorModel(strategy="text", value="hello")
    )
    assert locator.selector == "text=hello"


async def test_aria_strategy_builds_role_locator() -> None:
    runtime = await build_runtime()
    locator = runtime["registry"].build(
        runtime["page"], LocatorModel(strategy="aria", value="button")
    )
    assert locator.selector == "role=button"


async def test_aria_strategy_builds_role_name_locator() -> None:
    runtime = await build_runtime()
    locator = runtime["registry"].build(
        runtime["page"], LocatorModel(strategy="aria", value="button:Submit")
    )
    assert locator.selector == "role=button:Submit"


async def test_aria_strategy_rejects_missing_role() -> None:
    registry = LocatorRegistry(FakeLocatorProvider())
    with pytest.raises(InvalidLocatorStrategyError):
        registry.build(FakePage(), LocatorModel(strategy="aria", value=":Submit"))


async def test_playwright_strategy_passes_raw_selector() -> None:
    runtime = await build_runtime()
    locator = runtime["registry"].build(
        runtime["page"], LocatorModel(strategy="playwright", value="text=hello")
    )
    assert locator.selector == "text=hello"


async def test_resolve_passes_single_match() -> None:
    runtime = await build_runtime()
    locator = await runtime["registry"].resolve(
        runtime["page"], LocatorModel(strategy="css", value="#single")
    )
    assert isinstance(locator, FakeLocator)


async def test_resolve_raises_on_multiple_matches_when_strict() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements("#dup", [FakeElement(), FakeElement()])
    with pytest.raises(ElementStateError):
        await runtime["registry"].resolve(
            runtime["page"], LocatorModel(strategy="css", value="#dup", strict=True)
        )


async def test_resolve_allows_multiple_matches_when_not_strict() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements("#many", [FakeElement(), FakeElement()])
    locator = await runtime["registry"].resolve(
        runtime["page"], LocatorModel(strategy="css", value="#many", strict=False)
    )
    assert (await locator.count()) == 2


async def test_resolve_waits_and_reports_missing_element() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements("#missing", [])
    with pytest.raises(ElementNotFoundError):
        await runtime["registry"].resolve(
            runtime["page"],
            LocatorModel(strategy="css", value="#missing", timeout=50),
        )


async def test_strategy_classes_expose_names() -> None:
    assert CssStrategy.name == "css"
    assert XPathStrategy.name == "xpath"
    assert AriaStrategy.name == "aria"
    assert TextStrategy.name == "text"
    assert PlaywrightStrategy.name == "playwright"
