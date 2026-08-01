from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from browser_mcp.events.models import BrowserEvent
from browser_mcp.events.store import topic_matches

logger = logging.getLogger(__name__)

Subscriber = Callable[[BrowserEvent], Awaitable[None] | None]


class EventRouter:
    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self._timeout = timeout_seconds
        self._subscribers: list[tuple[str, Subscriber]] = []

    def subscribe(self, pattern: str, handler: Subscriber) -> None:
        self._subscribers.append((pattern, handler))

    def unsubscribe(self, handler: Subscriber) -> None:
        self._subscribers = [(p, h) for p, h in self._subscribers if h is not handler]

    async def dispatch(self, event: BrowserEvent) -> None:
        for pattern, handler in tuple(self._subscribers):
            if topic_matches(pattern, event.event_type):
                try:
                    result = handler(event)
                    if asyncio.iscoroutine(result):
                        await asyncio.wait_for(result, self._timeout)
                except Exception as exc:
                    # Listener errors/timeouts are deliberately isolated, but logged.
                    logger.debug("subscriber failed for %s", event.event_type, exc_info=exc)
