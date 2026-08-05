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
        name=f"{TOOL_NAMESPACE}.screenshot.full_page",
        description="Capture a screenshot of the entire scrollable page. output_format is one of 'png' or 'jpeg'.",
        returns="json",
    )
    async def capture_full_page(
        self,
        session_id: str,
        page_id: str,
        output_format: str = "png",
        quality: int | None = None,
    ) -> dict[str, Any]:
        """Capture the entire page."""
        try:
            result = await self._manager.capture_full_page(
                session_id,
                page_id,
                output_format=output_format,
                quality=quality,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.screenshot.viewport",
        description="Capture a screenshot of the visible viewport only. output_format is one of 'png' or 'jpeg'.",
        returns="json",
    )
    async def capture_viewport(
        self,
        session_id: str,
        page_id: str,
        output_format: str = "png",
        quality: int | None = None,
    ) -> dict[str, Any]:
        """Capture the viewport."""
        try:
            result = await self._manager.capture_viewport(
                session_id,
                page_id,
                output_format=output_format,
                quality=quality,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.screenshot.element",
        description="Capture a screenshot of a specific element using a CSS selector. output_format is one of 'png' or 'jpeg'.",
        returns="json",
    )
    async def capture_element(
        self,
        session_id: str,
        page_id: str,
        selector: str,
        output_format: str = "png",
        quality: int | None = None,
    ) -> dict[str, Any]:
        """Capture a specific element."""
        try:
            result = await self._manager.capture_element(
                session_id,
                page_id,
                selector=selector,
                output_format=output_format,
                quality=quality,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    def register(self, registry: Any) -> None:
        """Register every tool in this toolkit with ``registry``."""
        registry_register = registry.register
        for name in _TOOL_METHODS:
            registry_register(getattr(self, name))


_TOOL_METHODS = frozenset({"capture_full_page", "capture_viewport", "capture_element"})


def build_screenshot_tools(manager: ScreenshotManager) -> list[Callable[..., Any]]:
    """Return the screenshot tool callables bound to ``manager``."""
    toolkit = ScreenshotToolkit(manager)
    return [getattr(toolkit, name) for name in _TOOL_METHODS]
