"""Tab and popup (window) management.

:class:`WindowManager` detects popups — pages opened by ``window.open`` or a
targeted link — registers them in the pool so they are first-class pages, and
exposes structured popup/window queries for tools.

Popup detection works in two ways:

1. **Already open**: pages in the context that are not yet registered in the
   pool are adopted immediately.
2. **Pending**: a new ``page`` event is awaited for ``timeout`` milliseconds.
"""

from __future__ import annotations

import asyncio
from typing import Any

from browser_mcp.browser.navigation.state import PopupState, StateManager
from browser_mcp.browser.navigation.timeouts import resolve_timeout
from browser_mcp.browser.page import PageManager
from browser_mcp.browser.pool import BrowserPool
from browser_mcp.config.models import BrowserSettings
from browser_mcp.errors import NavigationTimeoutError
from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.events.types import DomainEvent

__all__ = ["WindowManager"]


class WindowManager:
    """Tracks popups and exposes structured window management."""

    def __init__(
        self,
        pool: BrowserPool,
        state: StateManager,
        pages: PageManager,
        events: EventBus,
        settings: BrowserSettings,
    ) -> None:
        self._pool = pool
        self._state = state
        self._pages = pages
        self._events = events
        self._settings = settings

    async def wait_for_popup(
        self,
        session_id: str,
        page_id: str,
        *,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Wait for a popup opened by ``page_id`` and register it."""
        handle = self._state.page_in_session(session_id, page_id)
        context = handle.page.context
        context_id = handle.context_id
        browser_id = handle.browser_id
        timeout = resolve_timeout(self._settings, "wait", timeout_ms)

        already_open = self._unregistered_pages(handle.page)
        if already_open:
            return await self._register_popup(
                session_id, page_id, context_id, browser_id, already_open[0]
            )

        queue: asyncio.Queue[Any] = asyncio.Queue()
        page = await self._await_new_page(context, queue, timeout)
        if page is None:
            raise NavigationTimeoutError(
                f"no popup opened from page '{page_id}' within {timeout}ms"
            )
        return await self._register_popup(session_id, page_id, context_id, browser_id, page)

    async def list_windows(self, session_id: str, page_id: str) -> list[dict[str, Any]]:
        """Return every page (tab/window) in the same context as ``page_id``."""
        handle = self._state.page_in_session(session_id, page_id)
        context_id = handle.context_id
        windows: list[dict[str, Any]] = []
        for page_handle in self._pool.all_pages():
            if page_handle.context_id != context_id:
                continue
            is_popup = self._is_popup(page_handle.page_id)
            windows.append(
                {
                    "page_id": page_handle.page_id,
                    "url": page_handle.state.url,
                    "is_popup": is_popup,
                }
            )
        return windows

    async def close_popup(self, session_id: str, popup_id: str) -> dict[str, Any]:
        """Close ``popup_id`` and stop tracking it."""
        self._state.popup(popup_id)
        self._state.page_in_session(session_id, popup_id)
        await self._pages.close(popup_id)
        self._state.close_popup(popup_id)
        return {"popup_id": popup_id, "closed": True}

    async def activate(self, session_id: str, page_id: str) -> dict[str, Any]:
        """Bring ``page_id`` to the front of its context."""
        handle = self._state.page_in_session(session_id, page_id)
        await handle.page.bring_to_front()
        return {"page_id": page_id, "activated": True}

    # -- internals -----------------------------------------------------

    def _unregistered_pages(self, origin_page: Any) -> list[Any]:
        # Context.pages recreates wrapper objects on each access, so compare
        # impl-object identity against pages already known to the pool.
        known_impl_ids = {id(getattr(h.page, "_impl_obj", None)) for h in self._pool.all_pages()}
        return [
            p
            for p in origin_page.context.pages
            if p is not origin_page and id(getattr(p, "_impl_obj", None)) not in known_impl_ids
        ]

    async def _await_new_page(
        self, context: Any, queue: asyncio.Queue[Any], timeout_ms: int
    ) -> Any | None:
        def on_page(page: Any) -> None:
            queue.put_nowait(page)

        context.on("page", on_page)
        try:
            try:
                return await asyncio.wait_for(queue.get(), timeout=timeout_ms / 1000)
            except TimeoutError:
                return None
        finally:
            context.remove_listener("page", on_page)

    def _is_popup(self, page_id: str) -> bool:
        return any(popup.popup_id == page_id for popup in self._state.popups())

    async def _register_popup(
        self,
        session_id: str,
        origin_page_id: str,
        context_id: str,
        browser_id: str,
        page: Any,
    ) -> dict[str, Any]:
        existing = self._registered_impl(context_id, page)
        if existing is not None:
            popup_id = existing.state.page_id
        else:
            state = await self._pages.register(context_id, page)
            popup_id = state.page_id
        url = page.url
        title = await self._safe_title(page)
        self._state.register_popup(
            PopupState(
                popup_id=popup_id,
                origin_page_id=origin_page_id,
                context_id=context_id,
                browser_id=browser_id,
                url=url,
                title=title,
            )
        )
        await self._events.publish(
            DomainEvent(
                event_name="popup.opened",
                payload={
                    "popup_id": popup_id,
                    "origin_page_id": origin_page_id,
                    "session_id": session_id,
                    "context_id": context_id,
                    "browser_id": browser_id,
                    "url": url,
                },
            )
        )
        return {
            "popup_id": popup_id,
            "origin_page_id": origin_page_id,
            "url": url,
            "title": title,
        }

    def _registered_impl(self, context_id: str, page: Any) -> Any | None:
        page_impl = getattr(page, "_impl_obj", None)
        for page_handle in self._pool.all_pages():
            if page_handle.context_id != context_id:
                continue
            if getattr(page_handle.page, "_impl_obj", None) is page_impl:
                return page_handle
        return None

    @staticmethod
    async def _safe_title(page: Any) -> str | None:
        try:
            return await page.title()
        except Exception:
            return None
