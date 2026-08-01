from __future__ import annotations

import json

from browser_mcp.events.models import BrowserEvent


class EventStreamAdapter:
    @staticmethod
    def websocket(event: BrowserEvent) -> dict[str, object]:
        return event.model_dump(mode="json")

    @staticmethod
    def sse(event: BrowserEvent) -> str:
        return f"event: {event.event_type}\ndata: {json.dumps(event.model_dump(mode='json'))}\n\n"
