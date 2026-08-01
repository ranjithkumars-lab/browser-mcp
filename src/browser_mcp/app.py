"""Browser MCP application composition.

Wires the browser engine (factory, pool, managers) into an enterprise
``AppContext``, registers the structured lifecycle tools, and exposes a
health provider reporting browser pool statistics.
"""

from __future__ import annotations

from typing import Any

import structlog

from browser_mcp.browser.context import ContextManager
from browser_mcp.browser.elements.engine import ElementEngine
from browser_mcp.browser.elements.locators.registry import LocatorRegistry
from browser_mcp.browser.elements.provider import PlaywrightLocatorProvider
from browser_mcp.browser.factory import BrowserFactory
from browser_mcp.browser.manager import BrowserManager
from browser_mcp.browser.navigation.frames import FrameManager
from browser_mcp.browser.navigation.history import HistoryManager
from browser_mcp.browser.navigation.interactions import InteractionManager
from browser_mcp.browser.navigation.manager import NavigationManager
from browser_mcp.browser.navigation.policy import NavigationPolicy
from browser_mcp.browser.navigation.state import StateManager
from browser_mcp.browser.navigation.waiting import WaitingManager
from browser_mcp.browser.navigation.windows import WindowManager
from browser_mcp.browser.page import PageManager
from browser_mcp.browser.pool import BrowserPool
from browser_mcp.browser.profile import ProfileManager
from browser_mcp.browser.runtime import check_playwright_binaries
from browser_mcp.browser.session import SessionManager
from browser_mcp.config.loader import load_browser_settings
from browser_mcp.config.models import BrowserSettings
from browser_mcp.tools.browser import BrowserToolkit
from browser_mcp.tools.elements import ElementToolkit
from browser_mcp.tools.navigation import NavigationToolkit
from enterprise_mcp.foundation.app import AppContext

__all__ = ["create_browser_app", "create_browser_context"]

_LOGGER = structlog.get_logger("browser_mcp.app")


def create_browser_context(
    settings: BrowserSettings | None = None,
    *,
    context: AppContext | None = None,
) -> AppContext:
    """Return an :class:`AppContext` wired with the browser engine and tools.

    Parameters
    ----------
    settings:
        Browser settings; falls back to the standard loader.
    context:
        An existing enterprise :class:`AppContext` to extend (used in tests).
    """
    browser_settings = settings or load_browser_settings()
    resolved = context or AppContext()

    factory = BrowserFactory()
    pool = BrowserPool(browser_settings)
    profiles = ProfileManager(browser_settings)
    browsers = BrowserManager(browser_settings, pool, factory, profiles)
    contexts = ContextManager(browser_settings, pool, factory, profiles)
    pages = PageManager(pool, factory)
    sessions = SessionManager(pool, browsers, contexts, pages)

    events = resolved.events
    state = StateManager(pool, sessions, browser_settings)
    policy = NavigationPolicy(browser_settings)
    frames = FrameManager(state, events, browser_settings)
    navigation = NavigationManager(state, policy, events, browser_settings)
    history = HistoryManager(state, events, browser_settings)
    windows = WindowManager(pool, state, pages, events, browser_settings)
    element_registry = LocatorRegistry(PlaywrightLocatorProvider())
    elements = ElementEngine(state, frames, element_registry, events, browser_settings)
    interactions = InteractionManager(state, frames, events, browser_settings, elements)
    waiting = WaitingManager(state, windows, events, browser_settings)

    resolved.register_startup_hook(factory.start)
    resolved.register_shutdown_hook(factory.stop)
    resolved.register_shutdown_hook(sessions.stop)
    resolved.register_health_provider(
        "browser_pool", _browser_pool_health(sessions, browser_settings)
    )
    resolved.register_health_provider("navigation", _navigation_health(state, browser_settings))
    resolved.register_health_provider("elements", _elements_health(elements))

    lifecycle = BrowserToolkit(sessions)
    lifecycle.register(resolved.tools)
    navigation_toolkit = NavigationToolkit(
        navigation, history, frames, windows, interactions, waiting
    )
    navigation_toolkit.register(resolved.tools)
    element_toolkit = ElementToolkit(elements)
    element_toolkit.register(resolved.tools)

    resolved.container.register_instance(sessions, name="browser_sessions")
    resolved.container.register_instance(state, name="navigation_state")
    resolved.container.register_instance(navigation, name="navigation_manager")
    resolved.container.register_instance(elements, name="element_engine")

    _LOGGER.info(
        "browser_context_ready",
        engine=browser_settings.browser.engine.value,
        headless=browser_settings.browser.headless,
        max_browsers=browser_settings.pool.max_browsers,
    )
    return resolved


def _browser_pool_health(sessions: SessionManager, settings: BrowserSettings) -> Any:
    async def health() -> dict[str, Any]:
        check = check_playwright_binaries(settings.browser.engine)
        return {
            "engine": settings.browser.engine.value,
            "headless": settings.browser.headless,
            "stats": sessions.stats(),
            "playwright_binary": {
                "installed": check.installed,
                "detail": check.detail,
            },
        }

    return health


def _navigation_health(state: StateManager, settings: BrowserSettings) -> Any:
    async def health() -> dict[str, Any]:
        return {
            "metrics": state.metrics(),
            "navigation": {
                "default_strategy": settings.navigation.default_strategy.value,
                "allowed_domains": settings.navigation.allowed_domains,
                "blocked_domains": settings.navigation.blocked_domains,
                "allow_redirects": settings.navigation.allow_redirects,
                "max_redirects": settings.navigation.max_redirects,
                "allowed_schemes": settings.navigation.allowed_schemes,
            },
        }

    return health


def _elements_health(elements: ElementEngine) -> Any:
    async def health() -> dict[str, Any]:
        return {"cache": elements.cache_stats()}

    return health


def create_browser_app(
    settings: BrowserSettings | None = None,
    *,
    context: AppContext | None = None,
) -> Any:
    """Build the FastAPI application with the browser MCP server mounted.

    Pass either ``settings`` (a fresh context is wired from them) or an
    already-wired ``context``. Suitable for ``uvicorn --factory`` style
    launches.
    """
    from enterprise_mcp.interfaces.rest.app import create_app

    if context is None:
        context = create_browser_context(settings)
    return create_app(context)
