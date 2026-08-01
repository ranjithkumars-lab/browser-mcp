"""Event value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

__all__ = ["DomainEvent"]


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Base class for all domain events published on the event bus."""

    event_name: str
    payload: dict[str, object] = field(default_factory=dict[str, object])
    event_id: str = field(default_factory=lambda: uuid4().hex)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
