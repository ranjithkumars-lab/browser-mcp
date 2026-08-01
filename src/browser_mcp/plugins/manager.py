from __future__ import annotations

from typing import Any

from browser_mcp.plugins.errors import PluginNotFoundError
from browser_mcp.plugins.registry import ActivePluginRegistry, InstalledPluginRegistry
from browser_mcp.plugins.runtime import PluginRuntime


class PluginLifecycleManager:
    def __init__(self) -> None:
        self.installed, self.active = InstalledPluginRegistry(), ActivePluginRegistry()

    def list(self) -> list[str]:
        return self.installed.names()

    def info(self, name: str) -> Any:
        try:
            return self.installed.get(name)
        except KeyError as exc:
            raise PluginNotFoundError(f"plugin '{name}' not found") from exc

    async def activate(self, runtime: PluginRuntime) -> None:
        await runtime.activate()
        self.installed.register(runtime.manifest)
        self.active.register(runtime.manifest.name, runtime)

    async def execute(self, name: str, payload: dict[str, Any]) -> Any:
        runtime = self.active.get(name)
        return await runtime.execute(payload)

    async def reload(self, name: str) -> None:
        runtime = self.active.get(name)
        await runtime.deactivate()
        await runtime.activate()
