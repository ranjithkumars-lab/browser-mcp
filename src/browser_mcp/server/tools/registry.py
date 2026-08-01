from __future__ import annotations

from typing import Any


class ToolRegistry:
    """MCP JSON-schema facade over the application tool registry."""

    def __init__(self, tools: Any) -> None:
        self._tools = tools

    def list(self) -> list[dict[str, Any]]:
        return [
            {
                "name": meta.name,
                "description": meta.description,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        p.name: {"type": p.type, "description": p.description}
                        for p in meta.parameters
                    },
                    "required": [p.name for p in meta.parameters if p.required],
                },
            }
            for meta in self._tools.list()
        ]

    async def call(self, name: str, arguments: dict[str, Any]) -> Any:
        return await self._tools.call(name, **arguments)
