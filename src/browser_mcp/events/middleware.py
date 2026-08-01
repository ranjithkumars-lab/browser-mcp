from __future__ import annotations

from abc import ABC, abstractmethod
from browser_mcp.events.models import BrowserEvent


class EventMiddleware(ABC):
    @abstractmethod
    async def process(self, event: BrowserEvent) -> BrowserEvent | None: ...


class LoggingMiddleware(EventMiddleware):
    async def process(self, event: BrowserEvent) -> BrowserEvent: return event


class MetricsMiddleware(EventMiddleware):
    def __init__(self) -> None: self.count = 0
    async def process(self, event: BrowserEvent) -> BrowserEvent:
        self.count += 1
        return event


class AuditMiddleware(EventMiddleware):
    def __init__(self) -> None: self.records: list[str] = []
    async def process(self, event: BrowserEvent) -> BrowserEvent:
        self.records.append(event.event_id)
        return event


class SamplingMiddleware(EventMiddleware):
    def __init__(self, rate: float = 1.0) -> None: self.rate = rate
    async def process(self, event: BrowserEvent) -> BrowserEvent | None:
        return event if self.rate >= 1 else None


async def run_pipeline(event: BrowserEvent, middleware: list[EventMiddleware]) -> BrowserEvent | None:
    current: BrowserEvent | None = event
    for item in middleware:
        if current is None: return None
        current = await item.process(current)
    return current
