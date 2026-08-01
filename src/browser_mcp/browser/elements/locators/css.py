"""CSS selector locator strategy."""

from __future__ import annotations

from typing import Any

from browser_mcp.browser.elements.locators.registry import LocatorStrategy

__all__ = ["CssStrategy"]


class CssStrategy(LocatorStrategy):
    """Locates elements with a plain CSS selector."""

    name = "css"

    def create(self, target: Any, value: str) -> Any:
        return self._provider.create_css(target, value)
