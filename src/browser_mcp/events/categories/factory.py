from __future__ import annotations

from collections.abc import Callable
from typing import Any

from browser_mcp.events.models import BrowserEvent


class EventFactoryRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, Callable[..., BrowserEvent]] = {}

    def register(self, category: str, factory: Callable[..., BrowserEvent]) -> None:
        self._factories[category] = factory

    def create(self, category: str, event_type: str, **kwargs: Any) -> BrowserEvent:
        factory = self._factories.get(category)
        return (
            factory(event_type, **kwargs)
            if factory
            else BrowserEvent(event_type=event_type, category=category, **kwargs)
        )
