"""Shared navigation helpers (redirects, titles, event emission)."""

from __future__ import annotations

from typing import Any

from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.events.types import DomainEvent

__all__ = [
    "emit_navigation_completed",
    "emit_navigation_failed",
    "emit_navigation_started",
    "redirect_count",
    "safe_title",
]


def redirect_count(response: Any) -> int:
    """Return the number of redirect hops in ``response``'s request chain."""
    count = 0
    request = getattr(response, "request", None)
    while request is not None:
        previous = getattr(request, "redirected_from", None)
        if previous is None:
            break
        count += 1
        request = previous
    return count


async def safe_title(page: Any) -> str:
    """Return ``page.title()``, tolerating pages that have closed."""
    try:
        return await page.title()
    except Exception:
        return ""


async def emit_navigation_started(
    events: EventBus,
    *,
    session_id: str,
    browser_id: str,
    context_id: str,
    page_id: str,
    url: str,
    strategy: str,
    timeout_ms: int,
) -> None:
    """Publish ``navigation.started``."""
    await events.publish(
        DomainEvent(
            event_name="navigation.started",
            payload={
                "session_id": session_id,
                "browser_id": browser_id,
                "context_id": context_id,
                "page_id": page_id,
                "url": url,
                "strategy": strategy,
                "timeout_ms": timeout_ms,
            },
        )
    )


async def emit_navigation_completed(events: EventBus, **payload: Any) -> None:
    """Publish ``navigation.completed``."""
    await events.publish(DomainEvent(event_name="navigation.completed", payload=dict(payload)))


async def emit_navigation_failed(events: EventBus, **payload: Any) -> None:
    """Publish ``navigation.failed``."""
    await events.publish(DomainEvent(event_name="navigation.failed", payload=dict(payload)))
