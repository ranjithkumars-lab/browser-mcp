"""History navigation (back / forward).

:class:`HistoryManager` wraps Playwright's ``go_back`` and ``go_forward`` and
reports the resulting navigation metadata in the same structured shape as
:class:`NavigationManager`.
"""

from __future__ import annotations

import time
from typing import Any

from browser_mcp.browser.navigation._common import (
    emit_navigation_completed,
    emit_navigation_failed,
    emit_navigation_started,
    redirect_count,
    safe_title,
)
from browser_mcp.browser.navigation.state import StateManager
from browser_mcp.browser.navigation.timeouts import resolve_timeout
from browser_mcp.config.models import BrowserSettings
from browser_mcp.errors import NavigationError
from enterprise_mcp.events.bus import EventBus

__all__ = ["HistoryManager"]


class HistoryManager:
    """Navigates backward and forward through page history."""

    def __init__(
        self,
        state: StateManager,
        events: EventBus,
        settings: BrowserSettings,
    ) -> None:
        self._state = state
        self._events = events
        self._settings = settings

    async def back(
        self, session_id: str, page_id: str, *, timeout_ms: int | None = None
    ) -> dict[str, Any]:
        """Navigate one step back in ``page_id``'s history."""
        return await self._navigate(session_id, page_id, "back", timeout_ms)

    async def forward(
        self, session_id: str, page_id: str, *, timeout_ms: int | None = None
    ) -> dict[str, Any]:
        """Navigate one step forward in ``page_id``'s history."""
        return await self._navigate(session_id, page_id, "forward", timeout_ms)

    async def _navigate(
        self,
        session_id: str,
        page_id: str,
        direction: str,
        timeout_ms: int | None,
    ) -> dict[str, Any]:
        handle = self._state.page_in_session(session_id, page_id)
        page = handle.page
        timeout = resolve_timeout(self._settings, "navigation", timeout_ms)
        start = time.monotonic()

        await emit_navigation_started(
            self._events,
            session_id=session_id,
            browser_id=handle.browser_id,
            context_id=handle.context_id,
            page_id=page_id,
            url=page.url,
            strategy=direction,
            timeout_ms=timeout,
        )

        try:
            response = (
                await page.go_back(timeout=timeout)
                if direction == "back"
                else await page.go_forward(timeout=timeout)
            )
            duration_ms = round((time.monotonic() - start) * 1000, 3)
            navigated_url = page.url
            handle.state.url = navigated_url
            title = await safe_title(page)
            status = response.status if response is not None else None
            redirects = redirect_count(response)
            payload = self._payload(
                session_id=session_id,
                handle=handle,
                page_id=page_id,
                url=navigated_url,
                title=title,
                status=status,
                navigation_time_ms=duration_ms,
                duration_ms=duration_ms,
                redirect_count=redirects,
                direction=direction,
            )
            await emit_navigation_completed(self._events, **payload)
            return payload
        except NavigationError:
            raise
        except Exception as exc:
            duration_ms = round((time.monotonic() - start) * 1000, 3)
            await emit_navigation_failed(
                self._events,
                session_id=session_id,
                browser_id=handle.browser_id,
                context_id=handle.context_id,
                page_id=page_id,
                url=page.url,
                direction=direction,
                error=str(exc),
                duration_ms=duration_ms,
            )
            raise NavigationError(f"failed to go {direction} on page '{page_id}': {exc}") from exc

    @staticmethod
    def _payload(
        *,
        session_id: str,
        handle: Any,
        page_id: str,
        url: str,
        title: str,
        status: int | None,
        navigation_time_ms: float,
        duration_ms: float,
        redirect_count: int,
        direction: str,
    ) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "browser_id": handle.browser_id,
            "context_id": handle.context_id,
            "page_id": page_id,
            "url": url,
            "title": title,
            "status": status,
            "navigation_time_ms": navigation_time_ms,
            "duration_ms": duration_ms,
            "redirect_count": redirect_count,
            "direction": direction,
        }
