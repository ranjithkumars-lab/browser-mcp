"""Plugin runtime context.

:class:`PluginContext` provides every plugin with a unified, read-only
view of the services it needs. Plugins never instantiate or import these
services directly; they receive them through this context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from browser_mcp.browser.elements.engine import ElementEngine
    from browser_mcp.browser.manager import BrowserManager
    from browser_mcp.browser.navigation.state import StateManager
    from browser_mcp.browser.pool import BrowserPool
    from browser_mcp.browser.session import SessionManager
    from enterprise_mcp.events.bus import EventBus
    from enterprise_mcp.foundation.app import AppContext
    from enterprise_mcp.foundation.container import Container

__all__ = ["PluginContext"]


class PluginContext:
    """Unified context passed to every plugin at initialisation time."""

    def __init__(
        self,
        app_context: AppContext,
        container: Container,
        browser_manager: BrowserManager,
        browser_pool: BrowserPool,
        session_manager: SessionManager,
        element_engine: ElementEngine,
        state_manager: StateManager,
        event_bus: EventBus,
        auth_manager: Any | None = None,
        transfer_manager: Any | None = None,
    ) -> None:
        self._app_context = app_context
        self._container = container
        self._browser_manager = browser_manager
        self._browser_pool = browser_pool
        self._session_manager = session_manager
        self._element_engine = element_engine
        self._state_manager = state_manager
        self._event_bus = event_bus
        self._auth_manager = auth_manager
        self._transfer_manager = transfer_manager

    @property
    def app_context(self) -> AppContext:
        return self._app_context

    @property
    def container(self) -> Container:
        return self._container

    @property
    def browser_manager(self) -> BrowserManager:
        return self._browser_manager

    @property
    def browser_pool(self) -> BrowserPool:
        return self._browser_pool

    @property
    def session_manager(self) -> SessionManager:
        return self._session_manager

    @property
    def element_engine(self) -> ElementEngine:
        return self._element_engine

    @property
    def state_manager(self) -> StateManager:
        return self._state_manager

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def auth_manager(self) -> Any | None:
        return self._auth_manager

    @property
    def transfer_manager(self) -> Any | None:
        """Shared download/upload engine facade."""
        return self._transfer_manager

    @property
    def settings(self) -> Any:
        return self._app_context.settings

    @property
    def tools(self) -> Any:
        return self._app_context.tools

    @property
    def logger(self) -> Any:
        import structlog

        return structlog.get_logger("browser_mcp.plugins")
