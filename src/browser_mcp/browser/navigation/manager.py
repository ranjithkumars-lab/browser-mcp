"""Core navigation management (goto / reload).

:class:`NavigationManager` orchestrates navigation from a policy check,
through Playwright, to a rich structured result with navigation metadata.
Every navigation emits ``navigation.started``, ``navigation.completed`` or
``navigation.failed`` events on the event bus.
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
from browser_mcp.browser.navigation.policy import NavigationPolicy
from browser_mcp.browser.navigation.state import StateManager
from browser_mcp.browser.navigation.timeouts import resolve_timeout
from browser_mcp.config.models import BrowserSettings, NavigationStrategy
from browser_mcp.errors import NavigationError
from enterprise_mcp.events.bus import EventBus

__all__ = ["NavigationManager"]


class NavigationManager:
    """Performs and reports page navigation."""

    def __init__(
        self,
        state: StateManager,
        policy: NavigationPolicy,
        events: EventBus,
        settings: BrowserSettings,
    ) -> None:
        self._state = state
        self._policy = policy
        self._events = events
        self._settings = settings

    async def goto(
        self,
        session_id: str,
        page_id: str,
        url: str,
        *,
        strategy: NavigationStrategy | str | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Navigate ``page_id`` to ``url``, applying navigation policy."""
        handle = self._state.page_in_session(session_id, page_id)
        page = handle.page
        resolved_strategy = self._policy.resolve_strategy(strategy)
        timeout = resolve_timeout(self._settings, "navigation", timeout_ms)
        policy = self._policy.validate(url)
        start = time.monotonic()

        await emit_navigation_started(
            self._events,
            session_id=session_id,
            browser_id=handle.browser_id,
            context_id=handle.context_id,
            page_id=page_id,
            url=policy.normalized_url or url,
            strategy=resolved_strategy.value,
            timeout_ms=timeout,
        )

        try:
            response = await page.goto(
                policy.normalized_url or url,
                wait_until=resolved_strategy.wait_until(),
                timeout=timeout,
            )
            redirects = redirect_count(response)
            self._policy.enforce_redirects(redirects)
            navigation_time_ms = round((time.monotonic() - start) * 1000, 3)
            navigated_url = page.url
            handle.state.url = navigated_url
            title = await safe_title(page)
            status = response.status if response is not None else None
            payload = self._payload(
                session_id=session_id,
                handle=handle,
                page_id=page_id,
                url=navigated_url,
                title=title,
                status=status,
                navigation_time_ms=navigation_time_ms,
                redirect_count=redirects,
                strategy=resolved_strategy.value,
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
                url=url,
                strategy=resolved_strategy.value,
                error=str(exc),
                duration_ms=duration_ms,
            )
            raise NavigationError(f"failed to navigate to '{url}': {exc}") from exc

    async def reload(
        self,
        session_id: str,
        page_id: str,
        *,
        strategy: NavigationStrategy | str | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Reload ``page_id`` in place."""
        handle = self._state.page_in_session(session_id, page_id)
        page = handle.page
        resolved_strategy = self._policy.resolve_strategy(strategy)
        timeout = resolve_timeout(self._settings, "navigation", timeout_ms)
        start = time.monotonic()

        await emit_navigation_started(
            self._events,
            session_id=session_id,
            browser_id=handle.browser_id,
            context_id=handle.context_id,
            page_id=page_id,
            url=page.url,
            strategy=resolved_strategy.value,
            timeout_ms=timeout,
        )

        try:
            response = await page.reload(
                wait_until=resolved_strategy.wait_until(),
                timeout=timeout,
            )
            navigation_time_ms = round((time.monotonic() - start) * 1000, 3)
            navigated_url = page.url
            handle.state.url = navigated_url
            title = await safe_title(page)
            status = response.status if response is not None else None
            payload = self._payload(
                session_id=session_id,
                handle=handle,
                page_id=page_id,
                url=navigated_url,
                title=title,
                status=status,
                navigation_time_ms=navigation_time_ms,
                redirect_count=0,
                strategy=resolved_strategy.value,
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
                strategy=resolved_strategy.value,
                error=str(exc),
                duration_ms=duration_ms,
            )
            raise NavigationError(f"failed to reload page '{page_id}': {exc}") from exc

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
        redirect_count: int,
        strategy: str,
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
            "duration_ms": navigation_time_ms,
            "redirect_count": redirect_count,
            "strategy": strategy,
        }
