"""Locator resolution (upgraded from Phase 2).

The Phase 2 ``LocatorResolver`` only understood a plain CSS selector. This
Phase 3 upgrade keeps the same single-seam responsibility — turn a caller
request into a resolved locator — but routes every request through the
:class:`ElementEngine`, so all strategies (CSS, XPath, ARIA, text,
Playwright) are available and interactions can alternatively consume a cached
``element_id``.
"""

from __future__ import annotations

from typing import Any

from browser_mcp.browser.elements.engine import ElementEngine
from browser_mcp.browser.navigation.frames import FrameManager

__all__ = ["LocatorResolver"]


class LocatorResolver:
    """Resolves a selector (or cached element id) to a browser locator."""

    def __init__(self, frames: FrameManager, engine: ElementEngine) -> None:
        self._frames = frames
        self._engine = engine

    async def resolve(
        self,
        session_id: str,
        page_id: str,
        selector: str,
        *,
        frame_id: str | None = None,
        timeout_ms: int | None = None,
        strict: bool = True,
    ) -> Any:
        """Return the locator for ``selector`` (treated as a CSS locator)."""
        return await self._engine.resolve_locator(
            session_id,
            page_id,
            "css",
            selector,
            frame_id=frame_id,
            timeout_ms=timeout_ms,
            strict=strict,
        )

    async def resolve_element(self, element_id: str, page_id: str) -> Any:
        """Return the locator for a previously resolved ``element_id``."""
        return await self._engine.locator_for(element_id, page_id)
