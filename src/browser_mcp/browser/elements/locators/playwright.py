"""Raw engine selector locator strategy.

The ``playwright`` strategy passes the value straight to the underlying engine's
native selector parser (e.g. ``#id``, ``.class``, ``text=...``, ``xpath=...``).
It is the escape hatch for selector syntax the other strategies do not cover.
"""

from __future__ import annotations

from typing import Any

from browser_mcp.browser.elements.locators.registry import LocatorStrategy

__all__ = ["PlaywrightStrategy"]


class PlaywrightStrategy(LocatorStrategy):
    """Locates elements with a raw engine selector string."""

    name = "playwright"

    def create(self, target: Any, value: str) -> Any:
        return self._provider.create_playwright(target, value)
