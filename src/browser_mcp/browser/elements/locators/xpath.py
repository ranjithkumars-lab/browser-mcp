"""XPath locator strategy."""

from __future__ import annotations

from typing import Any

from browser_mcp.browser.elements.locators.registry import LocatorStrategy

__all__ = ["XPathStrategy"]


class XPathStrategy(LocatorStrategy):
    """Locates elements with an XPath expression."""

    name = "xpath"

    def create(self, target: Any, value: str) -> Any:
        return self._provider.create_xpath(target, value)
