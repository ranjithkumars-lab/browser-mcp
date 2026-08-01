"""Element state validators.

:class:`ElementState` exposes ``exists()``, ``visible()``, ``enabled()``,
``editable()`` and ``checked()``. The last two are Phase 4 (Form Automation)
preparatory abstractions: they are fully implemented now so the state contract
stays stable, but form-specific behaviour lands with the forms engine.
"""

from __future__ import annotations

from typing import Any

from browser_mcp.browser.elements.provider import LocatorProvider

__all__ = ["ElementState"]


class ElementState:
    """Validators for the presence and interactive state of an element."""

    def __init__(self, provider: LocatorProvider) -> None:
        self._provider = provider

    async def exists(self, locator: Any) -> bool:
        """Return whether at least one match exists in the DOM."""
        return await self._provider.count(locator) > 0

    async def visible(self, locator: Any) -> bool:
        """Return whether the first match is visible."""
        return await self._provider.is_visible(locator)

    async def enabled(self, locator: Any) -> bool:
        """Return whether the first match is enabled."""
        return await self._provider.is_enabled(locator)

    async def editable(self, locator: Any) -> bool:
        """Return whether the first match is editable."""
        return await self._provider.is_editable(locator)

    async def checked(self, locator: Any) -> bool:
        """Return whether the first match is checked."""
        return await self._provider.is_checked(locator)

    async def snapshot(self, locator: Any) -> dict[str, bool]:
        """Return the full state snapshot as a boolean mapping.

        ``editable`` and ``checked`` are Phase 4 (Form Automation) preparatory
        checks. Playwright raises for elements that can never be editable or
        checked (plain divs, links, ...), so those two are guarded and reported
        as ``False`` for inapplicable elements instead of failing the snapshot.
        """
        editable = checked = False
        try:
            editable = await self.editable(locator)
        except Exception:
            editable = False
        try:
            checked = await self.checked(locator)
        except Exception:
            checked = False
        return {
            "exists": await self.exists(locator),
            "visible": await self.visible(locator),
            "enabled": await self.enabled(locator),
            "editable": editable,
            "checked": checked,
        }
