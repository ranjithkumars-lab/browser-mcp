from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from browser_mcp.server.capabilities import CapabilityRegistry
from browser_mcp.server.errors import translate_error
from browser_mcp.server.tools.registry import ToolRegistry


@dataclass
class SessionContext:
    connection_id: str
    browser_sessions: set[str] = field(default_factory=lambda: set())


class BrowserMCPServer:
    def __init__(self, context: Any) -> None:
        self.context, self.tools = context, ToolRegistry(context.tools)
        settings = context.settings
        self.capabilities = CapabilityRegistry(
            tools=True,
            notifications=settings.server.enable_notifications,
            resources=settings.server.enable_resources,
            prompts=settings.server.enable_prompts,
        )
        self.connections: dict[str, SessionContext] = {}

    def connect(self, connection_id: str) -> SessionContext:
        session = SessionContext(connection_id)
        self.connections[connection_id] = session
        return session

    async def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        request_id = request.get("id")
        try:
            method = request.get("method")
            if method == "initialize":
                result = {
                    "protocolVersion": self.context.settings.server.protocol_version,
                    "capabilities": self.capabilities.negotiate(
                        request.get("params", {}).get("capabilities")
                    ),
                }
            elif method == "tools/list":
                result = {"tools": self.tools.list()}
            elif method == "tools/call":
                params = request.get("params", {})
                result = {
                    "content": [
                        {
                            "type": "json",
                            "json": await self.tools.call(
                                params["name"], params.get("arguments", {})
                            ),
                        }
                    ]
                }
            else:
                raise ValueError(f"unsupported MCP method '{method}'")
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as exc:
            return {"jsonrpc": "2.0", "id": request_id, "error": translate_error(exc)}
