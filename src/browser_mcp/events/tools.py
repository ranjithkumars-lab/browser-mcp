from __future__ import annotations

from typing import Any

from browser_mcp.events.manager import BrowserEventManager
from enterprise_mcp.tools.decorators import tool


class EventsToolkit:
    def __init__(self, manager: BrowserEventManager) -> None:
        self._manager = manager

    @tool(
        name="browser.events.query",
        description="Query typed browser event history.",
        returns="json",
    )
    async def query(
        self,
        pattern: str | None = None,
        category: str | None = None,
        correlation_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        return {
            "success": True,
            "events": [
                event.model_dump(mode="json")
                for event in self._manager.query(
                    pattern=pattern, category=category, correlation_id=correlation_id, limit=limit
                )
            ],
        }

    @tool(
        name="browser.events.replay",
        description="Replay events after a previous event ID.",
        returns="json",
    )
    async def replay(self, event_id: str | None = None) -> dict[str, Any]:
        return {
            "success": True,
            "events": [event.model_dump(mode="json") for event in self._manager.replay(event_id)],
        }

    @tool(
        name="browser.events.listen",
        description="Register a server-side event listener pattern.",
        returns="json",
    )
    async def listen(self, pattern: str) -> dict[str, Any]:
        # MCP is request/response; live subscriptions are exposed to transport adapters.
        return {"success": True, "pattern": pattern, "streaming": "use SSE/WebSocket adapter"}

    def register(self, registry: Any) -> None:
        for name in ("query", "replay", "listen"):
            registry.register(getattr(self, name))
