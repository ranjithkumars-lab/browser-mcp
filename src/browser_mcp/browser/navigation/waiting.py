"""Waiting tools for navigation, popups, downloads and URLs.

:class:`WaitingManager` implements the split wait API. ``wait_element`` is
reserved for Phase 3 (the Element Engine) and is intentionally not exposed
here.
"""

from __future__ import annotations

import asyncio
from typing import Any, Literal

from browser_mcp.browser.navigation.state import StateManager
from browser_mcp.browser.navigation.timeouts import resolve_timeout
from browser_mcp.browser.navigation.windows import WindowManager
from browser_mcp.config.models import BrowserSettings
from browser_mcp.errors import NavigationTimeoutError
from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.events.types import DomainEvent

__all__ = ["WaitingManager"]

LoadState = Literal["load", "domcontentloaded", "networkidle"]


class WaitingManager:
    """Waits for pages, URLs, popups and downloads."""

    def __init__(
        self,
        state: StateManager,
        windows: WindowManager,
        events: EventBus,
        settings: BrowserSettings,
    ) -> None:
        self._state = state
        self._windows = windows
        self._events = events
        self._settings = settings

    async def wait_timeout(
        self, session_id: str, page_id: str, milliseconds: int
    ) -> dict[str, Any]:
        """Sleep for ``milliseconds`` (test/debug helper)."""
        if milliseconds < 0:
            raise NavigationTimeoutError("milliseconds must not be negative")
        self._state.page_in_session(session_id, page_id)
        await asyncio.sleep(milliseconds / 1000)
        return {"page_id": page_id, "waited_ms": milliseconds}

    async def wait_navigation(
        self,
        session_id: str,
        page_id: str,
        *,
        state: LoadState = "load",
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Wait until ``page_id`` reaches the requested load state."""
        handle = self._state.page_in_session(session_id, page_id)
        timeout = resolve_timeout(self._settings, "wait", timeout_ms)
        try:
            await handle.page.wait_for_load_state(state=state, timeout=timeout)
        except Exception as exc:
            raise NavigationTimeoutError(
                f"page '{page_id}' did not reach load state '{state}' within {timeout}ms: {exc}"
            ) from exc
        return {
            "page_id": page_id,
            "load_state": state,
            "url": handle.page.url,
        }

    async def wait_popup(
        self,
        session_id: str,
        page_id: str,
        *,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Wait for a popup opened by ``page_id``."""
        result = await self._windows.wait_for_popup(session_id, page_id, timeout_ms=timeout_ms)
        await self._events.publish(
            DomainEvent(
                event_name="wait.popup",
                payload=dict(result),
            )
        )
        return result

    async def wait_download(
        self,
        session_id: str,
        page_id: str,
        *,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Wait for a download to start on ``page_id``."""
        handle = self._state.page_in_session(session_id, page_id)
        timeout = resolve_timeout(self._settings, "wait", timeout_ms)
        queue: asyncio.Queue[Any] = asyncio.Queue()

        def on_download(download: Any) -> None:
            queue.put_nowait(download)

        handle.page.on("download", on_download)
        try:
            try:
                download = await asyncio.wait_for(queue.get(), timeout=timeout / 1000)
            except TimeoutError:
                raise NavigationTimeoutError(
                    f"no download started on page '{page_id}' within {timeout}ms"
                ) from None
        finally:
            handle.page.remove_listener("download", on_download)

        suggested = download.suggested_filename
        try:
            download_url = download.url
        except Exception:
            download_url = None
        return {
            "page_id": page_id,
            "suggested_filename": suggested,
            "url": download_url,
        }

    async def wait_url(
        self,
        session_id: str,
        page_id: str,
        pattern: str,
        *,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Wait until ``page_id``'s URL matches ``pattern`` (glob syntax)."""
        handle = self._state.page_in_session(session_id, page_id)
        timeout = resolve_timeout(self._settings, "wait", timeout_ms)
        try:
            await handle.page.wait_for_url(pattern, timeout=timeout)
        except Exception as exc:
            raise NavigationTimeoutError(
                f"page '{page_id}' URL did not match '{pattern}' within {timeout}ms: {exc}"
            ) from exc
        return {"page_id": page_id, "url": handle.page.url, "pattern": pattern}
