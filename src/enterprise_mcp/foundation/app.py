"""Application bootstrap context.

Binds configuration, the dependency injection container, the lifecycle
manager, and configured services into a single runtime context.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import structlog

from enterprise_mcp.config.loader import load_settings
from enterprise_mcp.config.models import Settings
from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.foundation.container import Container
from enterprise_mcp.foundation.lifecycle import LifecycleEvent, LifecycleManager
from enterprise_mcp.mcp.server.base import MCPServer
from enterprise_mcp.observability.logging.setup import configure_logging
from enterprise_mcp.tools.registry import ToolRegistry

__all__ = ["AppContext"]

HealthProvider = Callable[[], dict[str, Any] | Awaitable[dict[str, Any]]]


class AppContext:
    """Runtime context for a running Enterprise MCP Server instance."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        container: Container | None = None,
        lifecycle: LifecycleManager | None = None,
    ) -> None:
        self.settings = settings or load_settings()
        self.container = container or Container()
        self.lifecycle = lifecycle or LifecycleManager()
        self.events = EventBus()
        self.tools = ToolRegistry()
        self.mcp = MCPServer(tools=self.tools, name=self.settings.server.name)
        self._health_providers: dict[str, HealthProvider] = {}
        self._started = False

        self._register_core_services()
        configure_logging(self.settings.server.observability.logging)
        self.logger = structlog.get_logger("enterprise_mcp.app")

    def _register_core_services(self) -> None:
        self.container.register_instance(self.settings, name="settings")
        self.container.register_instance(self.container, name="container")
        self.container.register_instance(self.lifecycle, name="lifecycle")
        self.container.register_instance(self.events, name="events")
        self.container.register_instance(self.tools, name="tools")
        self.container.register_instance(self.mcp, name="mcp")

    # -- health providers -------------------------------------------------

    def register_health_provider(self, name: str, provider: HealthProvider) -> None:
        """Register a named health check contributing to the ``/health`` payload."""
        if name in self._health_providers:
            raise ValueError(f"health provider '{name}' is already registered")
        self._health_providers[name] = provider

    @property
    def health_providers(self) -> dict[str, HealthProvider]:
        """Return registered health providers by name."""
        return dict(self._health_providers)

    # -- lifecycle ---------------------------------------------------------

    def register_startup_hook(self, hook: Callable[[], Awaitable[None] | None]) -> None:
        """Register a startup hook to run during :meth:`start`."""
        self.lifecycle.register(LifecycleEvent.STARTUP, hook)

    def register_shutdown_hook(self, hook: Callable[[], Awaitable[None] | None]) -> None:
        """Register a shutdown hook to run during :meth:`stop`."""
        self.lifecycle.register(LifecycleEvent.SHUTDOWN, hook)

    async def start(self) -> None:
        """Run all registered startup hooks."""
        if self._started:
            return
        await self.lifecycle.run_startup()
        await self.mcp.start()
        self._started = True
        self.logger.info("application_started", name=self.settings.server.name)

    async def stop(self) -> None:
        """Run all registered shutdown hooks."""
        if not self._started:
            return
        await self.mcp.stop()
        await self.lifecycle.run_shutdown()
        self._started = False
        self.logger.info("application_stopped", name=self.settings.server.name)
