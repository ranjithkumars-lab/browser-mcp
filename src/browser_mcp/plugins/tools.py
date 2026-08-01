from __future__ import annotations
from typing import Any
from browser_mcp.plugins.manager import PluginLifecycleManager
from enterprise_mcp.tools.decorators import tool


class PluginToolkit:
    def __init__(self, manager: PluginLifecycleManager) -> None: self._manager = manager

    @tool(name="browser.plugins.list", description="List installed plugins.", returns="json")
    async def list_plugins(self) -> dict[str, Any]: return {"success": True, "plugins": self._manager.list()}

    @tool(name="browser.plugins.info", description="Get plugin manifest details.", returns="json")
    async def info(self, name: str) -> dict[str, Any]:
        try:
            value = self._manager.info(name)
            return {"success": True, "plugin": value.model_dump(mode="json") if hasattr(value, "model_dump") else value.to_dict()}
        except Exception as exc: return {"success": False, "error": str(exc)}

    @tool(name="browser.plugins.execute", description="Execute an active plugin.", returns="json")
    async def execute(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        try: return {"success": True, "result": await self._manager.execute(name, payload)}
        except Exception as exc: return {"success": False, "error": str(exc)}

    @tool(name="browser.plugins.reload", description="Reload an active plugin.", returns="json")
    async def reload(self, name: str) -> dict[str, Any]:
        try: await self._manager.reload(name); return {"success": True}
        except Exception as exc: return {"success": False, "error": str(exc)}

    def register(self, registry: Any) -> None:
        for name in ("list_plugins", "info", "execute", "reload"): registry.register(getattr(self, name))
