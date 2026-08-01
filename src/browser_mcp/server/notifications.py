from __future__ import annotations

from typing import Any

from browser_mcp.events.models import BrowserEvent


class NotificationManager:
    def __init__(self) -> None:
        self._subscribers: list[tuple[str, Any]] = []

    def subscribe(self, pattern: str, transport: Any) -> None:
        self._subscribers.append((pattern, transport))

    async def publish(self, event: BrowserEvent) -> None:
        from browser_mcp.events.store import topic_matches

        payload = {
            "jsonrpc": "2.0",
            "method": "notifications/browser.event",
            "params": event.model_dump(mode="json"),
        }
        for pattern, transport in tuple(self._subscribers):
            if topic_matches(pattern, event.event_type):
                await transport.send(payload)
