from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from datetime import datetime

from browser_mcp.events.models import BrowserEvent


class EventHistoryStore:
    """Bounded chronological history with query and reconnect replay support."""

    def __init__(self, max_size: int = 1000) -> None:
        self._events: deque[BrowserEvent] = deque(maxlen=max_size)

    def append(self, event: BrowserEvent) -> None:
        self._events.append(event)

    def query(
        self,
        *,
        pattern: str | None = None,
        category: str | None = None,
        correlation_id: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[BrowserEvent]:
        events: Iterable[BrowserEvent] = self._events
        if category:
            events = (e for e in events if e.category == category)
        if correlation_id:
            events = (e for e in events if e.header.correlation_id == correlation_id)
        if since:
            events = (e for e in events if e.header.timestamp >= since)
        if pattern:
            events = (e for e in events if topic_matches(pattern, e.event_type))
        return list(events)[-limit:]

    def replay(self, event_id: str | None = None) -> list[BrowserEvent]:
        items = list(self._events)
        if event_id is None:
            return items
        for index, event in enumerate(items):
            if event.event_id == event_id:
                return items[index + 1 :]
        return []


def topic_matches(pattern: str, topic: str) -> bool:
    if pattern in ("*", "#"):
        return True
    parts, values = pattern.split("."), topic.split(".")
    for index, part in enumerate(parts):
        if part == "#":
            return True
        if index >= len(values) or (part != "*" and part != values[index]):
            return False
    return len(parts) == len(values)
