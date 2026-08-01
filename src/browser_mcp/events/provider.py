from __future__ import annotations

from abc import ABC, abstractmethod

from browser_mcp.events.models import BrowserEvent


class EventProvider(ABC):
    @abstractmethod
    async def publish(self, event: BrowserEvent) -> None: ...


class InMemoryEventProvider(EventProvider):
    def __init__(self) -> None: self.events: list[BrowserEvent] = []
    async def publish(self, event: BrowserEvent) -> None: self.events.append(event)
