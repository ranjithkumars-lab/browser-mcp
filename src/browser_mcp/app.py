"""Browser MCP application composition.

Wires the browser engine (factory, pool, managers) into an enterprise
``AppContext``, registers the structured lifecycle tools, and exposes a
health provider reporting browser pool statistics.
"""

from __future__ import annotations

from typing import Any

import structlog

from browser_mcp.browser.context import ContextManager
from browser_mcp.browser.factory import BrowserFactory
from browser_mcp.browser.manager import BrowserManager
from browser_mcp.browser.page import PageManager
from browser_mcp.browser.pool import BrowserPool
from browser_mcp.browser.profile import ProfileManager
from browser_mcp.browser.runtime import check_playwright_binaries
from browser_mcp.browser.session import SessionManager
from browser_mcp.config.loader import load_browser_settings
from browser_mcp.config.models import BrowserSettings
from browser_mcp.tools.browser import BrowserToolkit
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

    resolved.register_startup_hook(factory.start)
    resolved.register_shutdown_hook(factory.stop)
    resolved.register_shutdown_hook(sessions.stop)
    resolved.register_health_provider(
        "browser_pool", _browser_pool_health(sessions, browser_settings)
    )

    toolkit = BrowserToolkit(sessions)
    toolkit.register(resolved.tools)
    resolved.container.register_instance(sessions, name="browser_sessions")

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
