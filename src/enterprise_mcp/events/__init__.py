"""Event-driven architecture primitives.

A lightweight, async-first event bus supporting publish/subscribe with
subscriber error isolation.
"""

from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.events.types import DomainEvent

__all__ = ["DomainEvent", "EventBus"]
