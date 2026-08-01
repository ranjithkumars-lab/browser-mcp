"""Plugin protocol definition.

Every plugin must implement the :class:`Plugin` protocol, which defines
the four lifecycle hooks that the framework calls at the appropriate
points during the server lifecycle.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from browser_mcp.plugins.context import PluginContext

__all__ = ["Plugin"]


class Plugin(ABC):
    """Protocol that every plugin must implement."""

    @abstractmethod
    async def initialize(self, context: PluginContext) -> None:
        """Initialise the plugin with its runtime context.

        Called once during plugin discovery after instantiation.
        """

    @abstractmethod
    def register_tools(self, registry: Any) -> None:
        """Register MCP tools provided by this plugin.

        ``registry`` is the :class:`~enterprise_mcp.tools.registry.ToolRegistry`
        attached to the active :class:`~enterprise_mcp.foundation.app.AppContext`.
        """

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Return a health-check payload for this plugin."""

    @abstractmethod
    async def shutdown(self) -> None:
        """Perform any cleanup when the server is stopping."""
