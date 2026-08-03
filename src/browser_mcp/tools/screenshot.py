"""Structured screenshot tools.

``browser.screenshot`` captures an image of a live page (viewport, full page,
or a single element) and returns structured metadata including the on-disk
path so clients can locate the artifact.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from browser_mcp.browser.screenshot import ScreenshotManager
from enterprise_mcp.tools.decorators import tool

__all__ = ["ScreenshotToolkit", "build_screenshot_tools"]

TOOL_NAMESPACE = "browser"


def _ok(**fields: Any) -> dict[str, Any]:
    return {
        "success": True,
        "timestamp": datetime.now(UTC).isoformat(),
        **fields,
    }


def _err(error: str, **fields: Any) -> dict[str, Any]:
    return {
        "success": False,
        "error": error,
        "timestamp": datetime.now(UTC).isoformat(),
        **fields,
    }


class ScreenshotToolkit:
    """Factory of structured screenshot tools bound to a screenshot manager."""

    def __init__(self, manager: ScreenshotManager) -> None:
        self._manager = manager

    @tool(
        name=f"{TOOL_NAMESPACE}.screenshot",
        description=(
            "Capture a screenshot of a page. By default captures the visible "
            "viewport as PNG. Pass full_page=true to capture the entire "
            "scrollable page, or selector=<CSS> to capture a single element. "
            "output_format is one of 'png' or 'jpeg'; quality (1-100) only "
            "applies to jpeg. Returns the absolute screenshot_path."
        ),
        returns="json",
    )
    async def screenshot(
        self,
        session_id: str,
        page_id: str,
        selector: str | None = None,
        output_format: str = "png",
        full_page: bool | None = None,
        quality: int | None = None,
        directory: str | None = None,
    ) -> dict[str, Any]:
        """Capture a screenshot of ``page_id``."""
        try:
            result = await self._manager.capture(
                session_id,
                page_id,
                selector=selector,
                output_format=output_format,
                full_page=full_page,
                quality=quality,
                directory=directory,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    def register(self, registry: Any) -> None:
        """Register every tool in this toolkit with ``registry``."""
        registry_register = registry.register
        for name in _TOOL_METHODS:
            registry_register(getattr(self, name))


_TOOL_METHODS = frozenset({"screenshot"})


def build_screenshot_tools(manager: ScreenshotManager) -> list[Callable[..., Any]]:
    """Return the screenshot tool callables bound to ``manager``."""
    toolkit = ScreenshotToolkit(manager)
    return [getattr(toolkit, name) for name in _TOOL_METHODS]
