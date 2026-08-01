"""Tests for the authentication event helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from browser_mcp.auth.events import (
    emit_auth_expired,
    emit_auth_failed,
    emit_auth_headers_updated,
    emit_auth_started,
    emit_auth_state_loaded,
    emit_auth_state_saved,
    emit_auth_success,
)
from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.events.types import DomainEvent

pytestmark = pytest.mark.unit


async def test_emit_auth_started() -> None:
    bus = EventBus()
    received: list[DomainEvent] = []

    async def handler(event: DomainEvent) -> None:
        received.append(event)

    bus.subscribe("auth.started", handler)
    await emit_auth_started(bus, strategy="form", context_id="ctx-1", session_id="ses-1")

    assert len(received) == 1
    assert received[0].event_name == "auth.started"
    assert received[0].payload["strategy"] == "form"


async def test_emit_auth_success() -> None:
    bus = EventBus()
    received: list[DomainEvent] = []

    async def handler(event: DomainEvent) -> None:
        received.append(event)

    bus.subscribe("auth.success", handler)
    await emit_auth_success(
        bus, strategy="header", context_id="ctx-1", session_id="ses-1", duration_ms=42.5
    )

    assert received[0].payload["duration_ms"] == 42.5


async def test_emit_auth_failed() -> None:
    bus = EventBus()
    received: list[DomainEvent] = []

    async def handler(event: DomainEvent) -> None:
        received.append(event)

    bus.subscribe("auth.failed", handler)
    await emit_auth_failed(
        bus, strategy="form", context_id="ctx-1", session_id="ses-1", error="bad", duration_ms=10.0
    )

    assert received[0].payload["error"] == "bad"


async def test_emit_auth_state_saved(tmp_path: Path) -> None:
    bus = EventBus()
    received: list[DomainEvent] = []

    async def handler(event: DomainEvent) -> None:
        received.append(event)

    bus.subscribe("auth.state.saved", handler)
    await emit_auth_state_saved(
        bus,
        context_id="ctx-1",
        session_id="ses-1",
        path=str(tmp_path / "state.json"),
        encrypted=True,
    )

    assert received[0].payload["path"] == str(tmp_path / "state.json")
    assert received[0].payload["encrypted"] is True


async def test_emit_auth_state_loaded(tmp_path: Path) -> None:
    bus = EventBus()
    received: list[DomainEvent] = []

    async def handler(event: DomainEvent) -> None:
        received.append(event)

    bus.subscribe("auth.state.loaded", handler)
    await emit_auth_state_loaded(
        bus,
        context_id="ctx-1",
        session_id="ses-1",
        path=str(tmp_path / "state.json"),
    )

    assert received[0].event_name == "auth.state.loaded"


async def test_emit_auth_headers_updated() -> None:
    bus = EventBus()
    received: list[DomainEvent] = []

    async def handler(event: DomainEvent) -> None:
        received.append(event)

    bus.subscribe("auth.headers.updated", handler)
    await emit_auth_headers_updated(
        bus, context_id="ctx-1", session_id="ses-1", headers=["Authorization"]
    )

    assert received[0].payload["headers"] == ["Authorization"]


async def test_emit_auth_expired() -> None:
    bus = EventBus()
    received: list[DomainEvent] = []

    async def handler(event: DomainEvent) -> None:
        received.append(event)

    bus.subscribe("auth.expired", handler)
    await emit_auth_expired(bus, context_id="ctx-1", session_id="ses-1", reason="ttl exceeded")

    assert received[0].payload["reason"] == "ttl exceeded"
