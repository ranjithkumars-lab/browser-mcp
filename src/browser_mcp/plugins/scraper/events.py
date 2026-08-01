"""Namespaced event helpers for the scraper plugin.

Emits the following lifecycle events on the event bus:

``scrape.started``
    Fired when a scrape tool begins execution.
``scrape.collect.completed``
    Fired after all collectors finish.
``scrape.format.completed``
    Fired after the formatter serialises the result.
``scrape.completed``
    Fired when the full pipeline succeeds.
``scrape.failed``
    Fired when any stage raises an exception.
"""

from __future__ import annotations

from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.events.types import DomainEvent

__all__ = [
    "ScrapeEvent",
    "emit_collect_completed",
    "emit_format_completed",
    "emit_scrape_completed",
    "emit_scrape_failed",
    "emit_scrape_started",
]


async def emit_scrape_started(
    events: EventBus,
    *,
    tool: str,
    session_id: str,
    page_id: str,
    url: str | None,
) -> None:
    await events.publish(
        ScrapeEvent(
            "scrape.started",
            {
                "tool": tool,
                "session_id": session_id,
                "page_id": page_id,
                "url": url,
            },
        )
    )


async def emit_collect_completed(
    events: EventBus,
    *,
    tool: str,
    session_id: str,
    page_id: str,
    collectors: list[str],
    item_count: int,
    duration_ms: int,
) -> None:
    await events.publish(
        ScrapeEvent(
            "scrape.collect.completed",
            {
                "tool": tool,
                "session_id": session_id,
                "page_id": page_id,
                "collectors": collectors,
                "item_count": item_count,
                "duration_ms": duration_ms,
            },
        )
    )


async def emit_format_completed(
    events: EventBus,
    *,
    tool: str,
    session_id: str,
    page_id: str,
    output_format: str,
    inline: bool,
    size_bytes: int,
) -> None:
    await events.publish(
        ScrapeEvent(
            "scrape.format.completed",
            {
                "tool": tool,
                "session_id": session_id,
                "page_id": page_id,
                "output_format": output_format,
                "inline": inline,
                "size_bytes": size_bytes,
            },
        )
    )


async def emit_scrape_completed(
    events: EventBus,
    *,
    tool: str,
    session_id: str,
    page_id: str,
    item_count: int,
    duration_ms: float,
) -> None:
    await events.publish(
        ScrapeEvent(
            "scrape.completed",
            {
                "tool": tool,
                "session_id": session_id,
                "page_id": page_id,
                "item_count": item_count,
                "duration_ms": round(duration_ms, 3),
            },
        )
    )


async def emit_scrape_failed(
    events: EventBus,
    *,
    tool: str,
    session_id: str,
    page_id: str,
    error: str,
    duration_ms: float,
) -> None:
    await events.publish(
        ScrapeEvent(
            "scrape.failed",
            {
                "tool": tool,
                "session_id": session_id,
                "page_id": page_id,
                "error": error,
                "duration_ms": round(duration_ms, 3),
            },
        )
    )


class ScrapeEvent(DomainEvent):
    """Thin :class:`DomainEvent` subclass for scrape events."""
