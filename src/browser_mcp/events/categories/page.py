from typing import Any

from browser_mcp.events.models import BrowserEvent


def create(event_type: str, **kwargs: Any) -> BrowserEvent:
    return BrowserEvent(event_type=event_type, category="page", **kwargs)
