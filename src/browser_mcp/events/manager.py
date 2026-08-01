from __future__ import annotations

from typing import Any

from enterprise_mcp.events.types import DomainEvent

from browser_mcp.events.middleware import EventMiddleware, run_pipeline
from browser_mcp.events.models import BrowserEvent, EventHeader, EventPriority
from browser_mcp.events.provider import EventProvider
from browser_mcp.events.router import EventRouter, Subscriber
from browser_mcp.events.store import EventHistoryStore


class BrowserEventManager:
    """Typed event facade and backward-compatible bridge from EventBus events."""
    def __init__(self, provider: EventProvider, store: EventHistoryStore, router: EventRouter, middleware: list[EventMiddleware] | None = None) -> None:
        self._provider, self._store, self._router = provider, store, router
        self._middleware = middleware or []

    async def publish(self, event: BrowserEvent) -> None:
        result = await run_pipeline(event, self._middleware)
        if result is None: return
        self._store.append(result)
        await self._provider.publish(result)
        await self._router.dispatch(result)

    async def publish_domain_event(self, event: DomainEvent) -> None:
        category = event.event_name.split(".", 1)[0]
        priority = EventPriority.HIGH if event.event_name.endswith((".failed", ".error")) else EventPriority.NORMAL
        await self.publish(BrowserEvent(header=EventHeader(event_id=event.event_id, timestamp=event.occurred_at, priority=priority), event_type=event.event_name, category=category, payload=dict(event.payload)))

    def listen(self, pattern: str, handler: Subscriber) -> None: self._router.subscribe(pattern, handler)
    def query(self, **filters: Any) -> list[BrowserEvent]: return self._store.query(**filters)
    def replay(self, event_id: str | None = None) -> list[BrowserEvent]: return self._store.replay(event_id)
