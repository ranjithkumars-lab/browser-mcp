from __future__ import annotations

from browser_mcp.api.ui.provider import WebSocketProvider
from browser_mcp.events.models import BrowserEvent


class WebSocketAdapter:
    def __init__(self, provider: WebSocketProvider) -> None:
        self.provider = provider

    async def publish(self, event: BrowserEvent) -> None:
        await self.provider.send_json(event.model_dump(mode="json"))
