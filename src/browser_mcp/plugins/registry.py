"""Active plugin registry.

:class:`PluginRegistry` stores instantiated plugins by name and exposes
lookup, iteration, and lifecycle delegation (initialise, health, shutdown).
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from browser_mcp.plugins.base import Plugin

__all__ = ["PluginRegistry"]


class PluginRegistry:
    """Registry of active plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, name: str, plugin: Plugin) -> None:
        """Register ``plugin`` under ``name``."""
        if name in self._plugins:
            raise ValueError(f"Plugin '{name}' is already registered")
        self._plugins[name] = plugin

    def get(self, name: str) -> Plugin:
        """Return the plugin registered under ``name``."""
        if name not in self._plugins:
            raise KeyError(f"Plugin '{name}' not found")
        return self._plugins[name]

    def remove(self, name: str) -> Plugin | None:
        """Remove and return the plugin registered under ``name``."""
        return self._plugins.pop(name, None)

    def names(self) -> list[str]:
        """Return all registered plugin names."""
        return list(self._plugins)

    def __len__(self) -> int:
        return len(self._plugins)

    def __iter__(self) -> Any:
        return iter(self._plugins.items())

    async def initialize_all(self, context: Any) -> None:
        """Initialise every registered plugin."""
        for _name, plugin in self._plugins.items():
            await plugin.initialize(context)

    async def shutdown_all(self) -> None:
        """Shut down every registered plugin."""
        for _name, plugin in self._plugins.items():
            with contextlib.suppress(Exception):
                await plugin.shutdown()

    async def health_all(self) -> dict[str, dict[str, Any]]:
        """Return health payloads for every registered plugin."""
        results: dict[str, dict[str, Any]] = {}
        for name, plugin in self._plugins.items():
            try:
                results[name] = await plugin.health()
            except Exception as exc:
                results[name] = {"healthy": False, "error": str(exc)}
        return results
