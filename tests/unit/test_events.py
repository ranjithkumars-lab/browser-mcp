"""Tests for the event bus."""

from __future__ import annotations

import pytest

from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.events.types import DomainEvent

pytestmark = pytest.mark.unit


async def test_subscribe_and_publish() -> None:
    bus = EventBus()
    received: list[DomainEvent] = []

    async def handler(event: DomainEvent) -> None:
        received.append(event)

    bus.subscribe("order.created", handler)
    await bus.publish(DomainEvent(event_name="order.created", payload={"id": "1"}))

    assert len(received) == 1
    assert received[0].payload["id"] == "1"


async def test_wildcard_subscriber_receives_all() -> None:
    bus = EventBus()
    received: list[str] = []

    async def handler(event: DomainEvent) -> None:
        received.append(event.event_name)

    bus.subscribe(None, handler)
    await bus.publish(DomainEvent(event_name="a"))
    await bus.publish(DomainEvent(event_name="b"))

    assert received == ["a", "b"]


async def test_non_matching_subscriber_not_called() -> None:
    bus = EventBus()
    called = False

    async def handler(event: DomainEvent) -> None:
        nonlocal called
        called = True

    bus.subscribe("other", handler)
    await bus.publish(DomainEvent(event_name="unrelated"))
    assert not called


async def test_sync_subscriber_supported() -> None:
    bus = EventBus()
    received: list[DomainEvent] = []

    def handler(event: DomainEvent) -> None:
        received.append(event)

    bus.subscribe("sync", handler)
    await bus.publish(DomainEvent(event_name="sync"))
    assert len(received) == 1


async def test_failing_subscriber_is_isolated() -> None:
    bus = EventBus()
    received: list[str] = []

    async def failing(event: DomainEvent) -> None:
        raise RuntimeError("boom")

    async def ok(event: DomainEvent) -> None:
        received.append(event.event_name)

    bus.subscribe("topic", failing)
    bus.subscribe("topic", ok)
    await bus.publish(DomainEvent(event_name="topic"))

    assert received == ["topic"]


async def test_unsubscribe() -> None:
    bus = EventBus()

    async def handler(event: DomainEvent) -> None:
        pass

    bus.subscribe("topic", handler)
    assert bus.handler_count("topic") == 1
    bus.unsubscribe("topic", handler)
    assert bus.handler_count("topic") == 0
