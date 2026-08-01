from __future__ import annotations

from typing import Any

from browser_mcp.plugins.executor import PluginExecutor
from browser_mcp.plugins.models import PluginManifestV2, PluginState
from browser_mcp.plugins.schemas.validator import PluginSchemaValidator


class PluginRuntime:
    def __init__(
        self,
        manifest: PluginManifestV2,
        plugin: Any,
        context: Any,
        *,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.manifest, self.plugin, self.context = manifest, plugin, context
        self.timeout_seconds, self.state = timeout_seconds, PluginState.LOADED
        self._executor, self._schemas = PluginExecutor(), PluginSchemaValidator()

    async def activate(self) -> None:
        await self.plugin.initialize(self.context)
        self.state = PluginState.ACTIVATED

    async def execute(self, payload: dict[str, Any]) -> Any:
        self._schemas.validate(payload, self.manifest.inputs)
        result = await self._executor.execute(
            self.plugin, payload, timeout_seconds=self.timeout_seconds
        )
        self._schemas.validate(result, self.manifest.outputs)
        return result

    async def deactivate(self) -> None:
        await self.plugin.shutdown()
        self.state = PluginState.DEACTIVATED
