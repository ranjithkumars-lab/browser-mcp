"""Locator strategy implementations for the element engine."""

from browser_mcp.browser.elements.locators.aria import AriaStrategy
from browser_mcp.browser.elements.locators.css import CssStrategy
from browser_mcp.browser.elements.locators.playwright import PlaywrightStrategy
from browser_mcp.browser.elements.locators.registry import LocatorRegistry, LocatorStrategy
from browser_mcp.browser.elements.locators.text import TextStrategy
from browser_mcp.browser.elements.locators.xpath import XPathStrategy

__all__ = [
    "AriaStrategy",
    "CssStrategy",
    "LocatorRegistry",
    "LocatorStrategy",
    "PlaywrightStrategy",
    "TextStrategy",
    "XPathStrategy",
]
