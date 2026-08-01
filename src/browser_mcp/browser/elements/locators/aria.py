"""ARIA role/name locator strategy.

The strategy value uses the ``role`` or ``role:accessible name`` syntax:

- ``button`` matches any element with the ``button`` role.
- ``button:Submit`` matches an element with the ``button`` role whose
  accessible name is ``Submit``.

Names are matched exactly so agent queries are deterministic.
"""

from __future__ import annotations

from typing import Any

from browser_mcp.browser.elements.locators.registry import LocatorStrategy
from browser_mcp.errors import InvalidLocatorStrategyError

__all__ = ["AriaStrategy"]


class AriaStrategy(LocatorStrategy):
    """Locates elements by ARIA role and optional accessible name."""

    name = "aria"

    def create(self, target: Any, value: str) -> Any:
        role, _, name = value.partition(":")
        role = role.strip()
        if not role:
            raise InvalidLocatorStrategyError("aria locator requires a role before ':'")
        return self._provider.create_role(
            target,
            role,
            name=name.strip() or None,
            exact=True,
        )
