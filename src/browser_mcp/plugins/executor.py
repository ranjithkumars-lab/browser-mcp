from __future__ import annotations
import asyncio
from typing import Any
from browser_mcp.plugins.errors import PluginExecutionError


class PluginExecutor:
    async def execute(self, plugin: Any, payload: dict[str, Any], *, timeout_seconds: float) -> Any:
        target = getattr(plugin, "execute", None)
        if target is None: raise PluginExecutionError("plugin does not expose an execute method")
        try:
            result = target(payload)
            if asyncio.iscoroutine(result): return await asyncio.wait_for(result, timeout_seconds)
            return result
        except TimeoutError as exc: raise PluginExecutionError("plugin execution timed out") from exc
        except PluginExecutionError: raise
        except Exception as exc: raise PluginExecutionError(str(exc)) from exc
