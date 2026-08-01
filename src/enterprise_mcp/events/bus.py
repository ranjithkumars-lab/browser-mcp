"""Async-first in-process event bus."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import structlog

from enterprise_mcp.events.types import DomainEvent

Subscriber = Callable[[DomainEvent], Awaitable[None] | None]

__all__ = ["EventBus"]


class EventBus:
    """Publish/subscribe event bus with subscriber error isolation.

    Subscribers may be synchronous or asynchronous callables. A failing
    subscriber never breaks delivery to other subscribers; the failure is
    logged and isolated.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = {}
        self._wildcard: list[Subscriber] = []
        self._logger = structlog.get_logger("enterprise_mcp.events")

    def subscribe(self, event_name: str | None, handler: Subscriber) -> None:
        """Register ``handler`` for ``event_name`` (or all events when ``None``)."""
        if event_name is None:
            self._wildcard.append(handler)
            return
        self._subscribers.setdefault(event_name, []).append(handler)

    def unsubscribe(self, event_name: str | None, handler: Subscriber) -> None:
        """Remove ``handler`` for ``event_name`` (or from all events when ``None``)."""
        if event_name is None:
            self._wildcard.remove(handler)
            return
        subscribers = self._subscribers.get(event_name, [])
        if handler in subscribers:
            subscribers.remove(handler)

    def handler_count(self, event_name: str) -> int:
        """Return the number of handlers registered for ``event_name``."""
        return len(self._subscribers.get(event_name, [])) + len(self._wildcard)

    async def publish(self, event: DomainEvent) -> None:
        """Deliver ``event`` to all matching subscribers."""
        handlers = list(self._subscribers.get(event.event_name, [])) + list(self._wildcard)
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:
                self._logger.exception(
                    "subscriber_failed",
                    event_name=event.event_name,
                    error=str(exc),
                    event_id=event.event_id,
                )

    def publish_sync(self, event: DomainEvent) -> None:
        """Fire-and-forget publish for synchronous contexts."""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            task = asyncio.ensure_future(self.publish(event))
            task.add_done_callback(self._log_task_failure)
        else:
            loop.run_until_complete(self.publish(event))

    def _log_task_failure(self, task: asyncio.Task[Any]) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            self._logger.error("event_publish_task_failed", error=str(exc))
