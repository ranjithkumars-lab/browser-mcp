"""Event payloads for the authentication engine.

Events are thin :class:`~enterprise_mcp.events.types.DomainEvent` subclasses
with the ``event_name`` fixed at the class level. The ``payload`` carries
structured data for downstream consumers.
"""

from __future__ import annotations

from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.events.types import DomainEvent

__all__ = [
    "AuthEvent",
    "emit_auth_expired",
    "emit_auth_failed",
    "emit_auth_headers_updated",
    "emit_auth_started",
    "emit_auth_state_loaded",
    "emit_auth_state_saved",
    "emit_auth_success",
]


class AuthEvent(DomainEvent):
    """Base :class:`DomainEvent` for authentication events."""


async def emit_auth_started(
    events: EventBus,
    *,
    strategy: str,
    context_id: str,
    session_id: str,
) -> None:
    await events.publish(
        AuthEvent(
            "auth.started",
            {
                "strategy": strategy,
                "context_id": context_id,
                "session_id": session_id,
            },
        )
    )


async def emit_auth_success(
    events: EventBus,
    *,
    strategy: str,
    context_id: str,
    session_id: str,
    duration_ms: float,
) -> None:
    await events.publish(
        AuthEvent(
            "auth.success",
            {
                "strategy": strategy,
                "context_id": context_id,
                "session_id": session_id,
                "duration_ms": round(duration_ms, 3),
            },
        )
    )


async def emit_auth_failed(
    events: EventBus,
    *,
    strategy: str,
    context_id: str,
    session_id: str,
    error: str,
    duration_ms: float,
) -> None:
    await events.publish(
        AuthEvent(
            "auth.failed",
            {
                "strategy": strategy,
                "context_id": context_id,
                "session_id": session_id,
                "error": error,
                "duration_ms": round(duration_ms, 3),
            },
        )
    )


async def emit_auth_state_saved(
    events: EventBus,
    *,
    context_id: str,
    session_id: str,
    path: str,
    encrypted: bool,
) -> None:
    await events.publish(
        AuthEvent(
            "auth.state.saved",
            {
                "context_id": context_id,
                "session_id": session_id,
                "path": path,
                "encrypted": encrypted,
            },
        )
    )


async def emit_auth_state_loaded(
    events: EventBus,
    *,
    context_id: str,
    session_id: str,
    path: str,
) -> None:
    await events.publish(
        AuthEvent(
            "auth.state.loaded",
            {
                "context_id": context_id,
                "session_id": session_id,
                "path": path,
            },
        )
    )


async def emit_auth_headers_updated(
    events: EventBus,
    *,
    context_id: str,
    session_id: str,
    headers: list[str],
) -> None:
    await events.publish(
        AuthEvent(
            "auth.headers.updated",
            {
                "context_id": context_id,
                "session_id": session_id,
                "headers": headers,
            },
        )
    )


async def emit_auth_expired(
    events: EventBus,
    *,
    context_id: str,
    session_id: str,
    reason: str,
) -> None:
    await events.publish(
        AuthEvent(
            "auth.expired",
            {
                "context_id": context_id,
                "session_id": session_id,
                "reason": reason,
            },
        )
    )
