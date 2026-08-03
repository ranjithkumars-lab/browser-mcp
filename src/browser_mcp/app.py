"""Browser MCP application composition.

Wires the browser engine (factory, pool, managers) into an enterprise
``AppContext``, registers the structured lifecycle tools, and exposes a
health provider reporting browser pool statistics.
"""

from __future__ import annotations

from typing import Any

import structlog

from browser_mcp.auth.manager import AuthManager
from browser_mcp.auth.provider import PlaywrightAuthProvider
from browser_mcp.auth.storage.encryption import AuthEncryptionEngine
from browser_mcp.auth.storage.manager import AuthStorageManager
from browser_mcp.auth.strategies.cookie import CookieAuthStrategy
from browser_mcp.auth.strategies.form import FormAuthStrategy
from browser_mcp.auth.strategies.header import HeaderAuthStrategy
from browser_mcp.auth.strategies.registry import AuthStrategyRegistry
from browser_mcp.auth.tools import AuthToolkit
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
from browser_mcp.browser.screenshot import ScreenshotManager
from browser_mcp.browser.session import SessionManager
from browser_mcp.config.loader import load_browser_settings
from browser_mcp.config.models import BrowserSettings
from browser_mcp.events.manager import BrowserEventManager
from browser_mcp.events.middleware import MetricsMiddleware
from browser_mcp.events.provider import InMemoryEventProvider
from browser_mcp.events.router import EventRouter
from browser_mcp.events.store import EventHistoryStore
from browser_mcp.events.tools import EventsToolkit
from browser_mcp.plugins.manager import PluginLifecycleManager
from browser_mcp.plugins.scraper.actions import ScraperActions
from browser_mcp.plugins.scraper.sizer import PayloadSizer
from browser_mcp.plugins.scraper.tools import ScraperToolkit
from browser_mcp.plugins.tools import PluginToolkit
from browser_mcp.tools.browser import BrowserToolkit
from browser_mcp.tools.elements import ElementToolkit
from browser_mcp.tools.navigation import NavigationToolkit
from browser_mcp.tools.screenshot import ScreenshotToolkit
from browser_mcp.transfer.downloads.integrity import ChecksumVerifier
from browser_mcp.transfer.downloads.manager import DownloadManager
from browser_mcp.transfer.downloads.naming import FileNamingStrategy
from browser_mcp.transfer.downloads.strategies.browser import BrowserDownloadStrategy
from browser_mcp.transfer.downloads.strategies.registry import DownloadStrategyRegistry
from browser_mcp.transfer.manager import TransferManager
from browser_mcp.transfer.provider import PlaywrightTransferProvider
from browser_mcp.transfer.state import TransferStateManager
from browser_mcp.transfer.tools import TransferToolkit
from browser_mcp.transfer.uploads.manager import UploadManager
from browser_mcp.transfer.uploads.strategies.chooser import ChooserUploadStrategy
from browser_mcp.transfer.uploads.strategies.drag_drop import DragDropUploadStrategy
from browser_mcp.transfer.uploads.strategies.input import InputUploadStrategy
from browser_mcp.transfer.uploads.strategies.registry import UploadStrategyRegistry
from browser_mcp.transfer.uploads.validator import FileValidator
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

    auth_registry = AuthStrategyRegistry()
    auth_registry.register(FormAuthStrategy())
    auth_registry.register(CookieAuthStrategy())
    auth_registry.register(HeaderAuthStrategy())
    auth_storage = AuthStorageManager(
        directory=browser_settings.auth.storage_directory,
        encryption=AuthEncryptionEngine(allow_plaintext=browser_settings.auth.allow_plaintext),
    )
    auth_provider = PlaywrightAuthProvider()
    auth_manager = AuthManager(
        registry=auth_registry,
        storage=auth_storage,
        provider=auth_provider,
        event_bus=events,
    )
    resolved.container.register_instance(auth_manager, name="auth_manager")

    transfer_provider = PlaywrightTransferProvider()
    download_registry = DownloadStrategyRegistry()
    download_registry.register(BrowserDownloadStrategy(transfer_provider))
    upload_registry = UploadStrategyRegistry()
    upload_registry.register(InputUploadStrategy(transfer_provider))
    upload_registry.register(ChooserUploadStrategy(transfer_provider))
    upload_registry.register(DragDropUploadStrategy(transfer_provider))
    transfer_manager = TransferManager(
        DownloadManager(
            download_registry,
            FileNamingStrategy(),
            ChecksumVerifier(),
            directory=browser_settings.transfer.download_directory,
            collision_strategy=browser_settings.transfer.collision_strategy,
            checksum_algorithm=browser_settings.transfer.checksum_algorithm,
        ),
        UploadManager(
            upload_registry,
            FileValidator(
                max_file_size_bytes=browser_settings.transfer.max_file_size_bytes,
                allowed_extensions=browser_settings.transfer.allowed_extensions,
                allowed_mime_types=browser_settings.transfer.allowed_mime_types,
            ),
        ),
        TransferStateManager(),
        events,
    )
    resolved.container.register_instance(transfer_manager, name="transfer_manager")

    event_manager = BrowserEventManager(
        InMemoryEventProvider(),
        EventHistoryStore(browser_settings.events.max_history_size),
        EventRouter(browser_settings.events.subscriber_timeout_seconds),
        [MetricsMiddleware()] if browser_settings.events.enable_metrics else [],
    )
    # Preserve every existing EventBus publisher; the typed engine observes it.
    events.subscribe(None, event_manager.publish_domain_event)
    resolved.container.register_instance(event_manager, name="event_manager")
    plugin_manager = PluginLifecycleManager()
    resolved.container.register_instance(plugin_manager, name="plugin_manager")

    lifecycle = BrowserToolkit(sessions)
    lifecycle.register(resolved.tools)
    navigation_toolkit = NavigationToolkit(
        navigation, history, frames, windows, interactions, waiting
    )
    navigation_toolkit.register(resolved.tools)
    element_toolkit = ElementToolkit(elements)
    element_toolkit.register(resolved.tools)

    screenshot_manager = ScreenshotManager(state, browser_settings)
    screenshot_toolkit = ScreenshotToolkit(screenshot_manager)
    screenshot_toolkit.register(resolved.tools)

    scraper_actions = ScraperActions(state, events, PayloadSizer())
    scraper_toolkit = ScraperToolkit(scraper_actions)
    scraper_toolkit.register(resolved.tools)

    auth_toolkit = AuthToolkit(auth_manager, pool, sessions)
    auth_toolkit.register(resolved.tools)
    TransferToolkit(transfer_manager, pool, sessions).register(resolved.tools)
    EventsToolkit(event_manager).register(resolved.tools)
    PluginToolkit(plugin_manager).register(resolved.tools)

    resolved.container.register_instance(sessions, name="browser_sessions")
    resolved.container.register_instance(state, name="navigation_state")
    resolved.container.register_instance(navigation, name="navigation_manager")
    resolved.container.register_instance(elements, name="element_engine")
    resolved.container.register_instance(screenshot_manager, name="screenshot_manager")

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
