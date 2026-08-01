"""Text locator strategy."""

from __future__ import annotations

from typing import Any

from browser_mcp.browser.elements.locators.registry import LocatorStrategy

__all__ = ["TextStrategy"]


class TextStrategy(LocatorStrategy):
    """Locates elements by their rendered visible text."""

    name = "text"

    def create(self, target: Any, value: str) -> Any:
        return self._provider.create_text(target, value, exact=True)
