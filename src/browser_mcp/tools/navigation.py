"""Structured navigation & interaction tools (Phase 2).

Every tool returns a JSON mapping (``{"success": true, ...}``) with full ID
tracking (session/browser/context/page) plus navigation metadata and a
timestamp, so clients can programmatically inspect results.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from browser_mcp.browser.navigation.frames import FrameManager
from browser_mcp.browser.navigation.history import HistoryManager
from browser_mcp.browser.navigation.interactions import InteractionManager
from browser_mcp.browser.navigation.manager import NavigationManager
from browser_mcp.browser.navigation.waiting import LoadState, WaitingManager
from browser_mcp.browser.navigation.windows import WindowManager
from browser_mcp.config.models import NavigationStrategy
from enterprise_mcp.tools.decorators import tool

__all__ = ["NavigationToolkit", "build_navigation_tools"]

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


class NavigationToolkit:
    """Factory of structured navigation tools bound to the Phase 2 managers."""

    def __init__(
        self,
        navigation: NavigationManager,
        history: HistoryManager,
        frames: FrameManager,
        windows: WindowManager,
        interactions: InteractionManager,
        waiting: WaitingManager,
    ) -> None:
        self._navigation = navigation
        self._history = history
        self._frames = frames
        self._windows = windows
        self._interactions = interactions
        self._waiting = waiting

    # -- navigation ----------------------------------------------------

    @tool(
        name=f"{TOOL_NAMESPACE}.goto",
        description=(
            "Navigate a page to a URL and wait until the requested load state. "
            "navigation_strategy is vendor-neutral: 'fast' (DOM content loaded), "
            "'normal' (load event), 'complete' (network idle)."
        ),
        returns="json",
    )
    async def goto(
        self,
        session_id: str,
        page_id: str,
        url: str,
        navigation_strategy: str = "normal",
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Navigate a page to ``url``."""
        try:
            result = await self._navigation.goto(
                session_id,
                page_id,
                url,
                strategy=NavigationStrategy(navigation_strategy),
                timeout_ms=timeout_ms,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.back",
        description="Navigate the page one step back in its history.",
        returns="json",
    )
    async def back(
        self, session_id: str, page_id: str, timeout_ms: int | None = None
    ) -> dict[str, Any]:
        """Go back one history entry."""
        try:
            result = await self._history.back(session_id, page_id, timeout_ms=timeout_ms)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.forward",
        description="Navigate the page one step forward in its history.",
        returns="json",
    )
    async def forward(
        self, session_id: str, page_id: str, timeout_ms: int | None = None
    ) -> dict[str, Any]:
        """Go forward one history entry."""
        try:
            result = await self._history.forward(session_id, page_id, timeout_ms=timeout_ms)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.reload",
        description="Reload the current page using the given navigation strategy.",
        returns="json",
    )
    async def reload(
        self,
        session_id: str,
        page_id: str,
        navigation_strategy: str = "normal",
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Reload the current page."""
        try:
            result = await self._navigation.reload(
                session_id,
                page_id,
                strategy=NavigationStrategy(navigation_strategy),
                timeout_ms=timeout_ms,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    # -- waiting -------------------------------------------------------

    @tool(
        name=f"{TOOL_NAMESPACE}.wait_timeout",
        description="Sleep for a fixed number of milliseconds (debug helper).",
        returns="json",
    )
    async def wait_timeout(
        self, session_id: str, page_id: str, milliseconds: int
    ) -> dict[str, Any]:
        """Wait for ``milliseconds``."""
        try:
            result = await self._waiting.wait_timeout(session_id, page_id, milliseconds)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.wait_navigation",
        description=(
            "Wait until the page reaches a load state. state is one of "
            "'load', 'domcontentloaded', 'networkidle'."
        ),
        returns="json",
    )
    async def wait_navigation(
        self,
        session_id: str,
        page_id: str,
        state: LoadState = "load",
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Wait for a page load state."""
        try:
            result = await self._waiting.wait_navigation(
                session_id,
                page_id,
                state=state,
                timeout_ms=timeout_ms,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.wait_popup",
        description="Wait for a popup (new tab/window) opened by the page.",
        returns="json",
    )
    async def wait_popup(
        self, session_id: str, page_id: str, timeout_ms: int | None = None
    ) -> dict[str, Any]:
        """Wait for a popup from ``page_id``."""
        try:
            result = await self._waiting.wait_popup(session_id, page_id, timeout_ms=timeout_ms)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.wait_download",
        description="Wait for a download to start on the page.",
        returns="json",
    )
    async def wait_download(
        self, session_id: str, page_id: str, timeout_ms: int | None = None
    ) -> dict[str, Any]:
        """Wait for a download to start."""
        try:
            result = await self._waiting.wait_download(session_id, page_id, timeout_ms=timeout_ms)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.wait_url",
        description="Wait until the page URL matches a glob pattern.",
        returns="json",
    )
    async def wait_url(
        self,
        session_id: str,
        page_id: str,
        pattern: str,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Wait until the page URL matches ``pattern``."""
        try:
            result = await self._waiting.wait_url(
                session_id, page_id, pattern, timeout_ms=timeout_ms
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    # -- scrolling -----------------------------------------------------

    @tool(
        name=f"{TOOL_NAMESPACE}.scroll_to",
        description="Scroll the page viewport to an absolute (x, y) position.",
        returns="json",
    )
    async def scroll_to(
        self,
        session_id: str,
        page_id: str,
        x: int,
        y: int,
        frame_id: str | None = None,
    ) -> dict[str, Any]:
        """Scroll the page to absolute coordinates."""
        try:
            result = await self._interactions.scroll_to(
                session_id, page_id, x, y, frame_id=frame_id
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.scroll_by",
        description="Scroll the page viewport by (delta_x, delta_y) pixels.",
        returns="json",
    )
    async def scroll_by(
        self,
        session_id: str,
        page_id: str,
        delta_x: int,
        delta_y: int,
        frame_id: str | None = None,
    ) -> dict[str, Any]:
        """Scroll the page by a relative offset."""
        try:
            result = await self._interactions.scroll_by(
                session_id, page_id, delta_x, delta_y, frame_id=frame_id
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.scroll_element",
        description="Scroll the element matching a selector into the viewport.",
        returns="json",
    )
    async def scroll_element(
        self,
        session_id: str,
        page_id: str,
        selector: str,
        frame_id: str | None = None,
        align: str = "center",
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Scroll a specific element into view."""
        try:
            result = await self._interactions.scroll_element(
                session_id,
                page_id,
                selector,
                frame_id=frame_id,
                align=align,  # type: ignore[arg-type]
                timeout_ms=timeout_ms,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    # -- interactions --------------------------------------------------

    @tool(
        name=f"{TOOL_NAMESPACE}.click",
        description=(
            "Click the element matching a selector. button is one of "
            "'left', 'right', 'middle'; click_count controls the number of clicks."
        ),
        returns="json",
    )
    async def click(
        self,
        session_id: str,
        page_id: str,
        selector: str,
        frame_id: str | None = None,
        timeout_ms: int | None = None,
        button: str = "left",
        click_count: int = 1,
        delay_ms: int | None = None,
    ) -> dict[str, Any]:
        """Click an element."""
        try:
            result = await self._interactions.click(
                session_id,
                page_id,
                selector,
                frame_id=frame_id,
                timeout_ms=timeout_ms,
                button=button,  # type: ignore[arg-type]
                click_count=click_count,
                delay_ms=delay_ms,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.hover",
        description="Hover the element matching a selector.",
        returns="json",
    )
    async def hover(
        self,
        session_id: str,
        page_id: str,
        selector: str,
        frame_id: str | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Hover an element."""
        try:
            result = await self._interactions.hover(
                session_id, page_id, selector, frame_id=frame_id, timeout_ms=timeout_ms
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.double_click",
        description="Double-click the element matching a selector.",
        returns="json",
    )
    async def double_click(
        self,
        session_id: str,
        page_id: str,
        selector: str,
        frame_id: str | None = None,
        timeout_ms: int | None = None,
        delay_ms: int | None = None,
    ) -> dict[str, Any]:
        """Double-click an element."""
        try:
            result = await self._interactions.double_click(
                session_id,
                page_id,
                selector,
                frame_id=frame_id,
                timeout_ms=timeout_ms,
                delay_ms=delay_ms,
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.right_click",
        description="Right-click the element matching a selector.",
        returns="json",
    )
    async def right_click(
        self,
        session_id: str,
        page_id: str,
        selector: str,
        frame_id: str | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Right-click an element."""
        try:
            result = await self._interactions.right_click(
                session_id, page_id, selector, frame_id=frame_id, timeout_ms=timeout_ms
            )
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    # -- frames & windows ----------------------------------------------

    @tool(
        name=f"{TOOL_NAMESPACE}.list_frames",
        description="List the frames (iframes) currently present in a page.",
        returns="json",
    )
    async def list_frames(self, session_id: str, page_id: str) -> dict[str, Any]:
        """List frames of a page."""
        try:
            frames = await self._frames.list_frames(session_id, page_id)
            return _ok(page_id=page_id, frames=frames)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.list_windows",
        description="List the tabs/windows (pages) in the same context as a page.",
        returns="json",
    )
    async def list_windows(self, session_id: str, page_id: str) -> dict[str, Any]:
        """List windows of a page's context."""
        try:
            windows = await self._windows.list_windows(session_id, page_id)
            return _ok(page_id=page_id, windows=windows)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.close_popup",
        description="Close a popup (new tab/window) by its popup/page id.",
        returns="json",
    )
    async def close_popup(self, session_id: str, popup_id: str) -> dict[str, Any]:
        """Close a tracked popup."""
        try:
            result = await self._windows.close_popup(session_id, popup_id)
            return _ok(session_id=session_id, **result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, popup_id=popup_id)

    @tool(
        name=f"{TOOL_NAMESPACE}.activate_window",
        description="Bring a page (tab/window) to the front of its context.",
        returns="json",
    )
    async def activate_window(self, session_id: str, page_id: str) -> dict[str, Any]:
        """Activate a window/tab."""
        try:
            result = await self._windows.activate(session_id, page_id)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    # -- registration ---------------------------------------------------

    def register(self, registry: Any) -> None:
        """Register every tool in this toolkit with ``registry``."""
        registry_register = registry.register
        for name in _TOOL_METHODS:
            registry_register(getattr(self, name))


_TOOL_METHODS = frozenset(
    {
        "goto",
        "back",
        "forward",
        "reload",
        "wait_timeout",
        "wait_navigation",
        "wait_popup",
        "wait_download",
        "wait_url",
        "scroll_to",
        "scroll_by",
        "scroll_element",
        "click",
        "hover",
        "double_click",
        "right_click",
        "list_frames",
        "list_windows",
        "close_popup",
        "activate_window",
    }
)


def build_navigation_tools(
    navigation: NavigationManager,
    history: HistoryManager,
    frames: FrameManager,
    windows: WindowManager,
    interactions: InteractionManager,
    waiting: WaitingManager,
) -> list[Callable[..., Any]]:
    """Return the Phase 2 navigation tool callables bound to the managers."""
    toolkit = NavigationToolkit(navigation, history, frames, windows, interactions, waiting)
    return [getattr(toolkit, name) for name in _TOOL_METHODS]
