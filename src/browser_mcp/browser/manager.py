"""Browser lifecycle management.

``BrowserManager`` launches and closes browser instances in the pool. It is
the only manager that understands the difference between a normal browser
launch and a persistent-context launch (used for ``persistent`` profiles).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from browser_mcp.browser.factory import BrowserFactory
from browser_mcp.browser.models import (
    BrowserHandle,
    BrowserState,
    ContextHandle,
    ContextState,
    new_browser_id,
    new_context_id,
)
from browser_mcp.browser.pool import BrowserPool
from browser_mcp.browser.profile import ProfileManager
from browser_mcp.config.models import BrowserConfig, BrowserEngine, BrowserProfile, BrowserSettings

if TYPE_CHECKING:
    pass

__all__ = ["BrowserManager"]


class BrowserManager:
    """Launches and closes browsers in the :class:`BrowserPool`."""

    def __init__(
        self,
        settings: BrowserSettings,
        pool: BrowserPool,
        factory: BrowserFactory,
        profiles: ProfileManager,
    ) -> None:
        self._settings = settings
        self._pool = pool
        self._factory = factory
        self._profiles = profiles

    def _merged_config(
        self,
        *,
        engine: BrowserEngine | str | None,
        headless: bool | None,
    ) -> tuple[BrowserConfig, BrowserEngine]:
        base = self._settings.browser
        resolved_engine = BrowserEngine(engine) if engine else base.engine
        updates: dict[str, object] = {}
        if headless is not None:
            updates["headless"] = headless
        config = base.model_copy(update=updates)
        return config, resolved_engine

    async def launch(
        self,
        *,
        engine: BrowserEngine | str | None = None,
        headless: bool | None = None,
        profile: BrowserProfile | str | None = None,
        label: str | None = None,
    ) -> BrowserState:
        """Launch a new browser and register it in the pool.

        Parameters
        ----------
        engine:
            Override the configured browser engine.
        headless:
            Override the configured headless mode.
        profile:
            Profile type: ``temporary``, ``persistent``, or ``incognito``.
        label:
            Stable label for a persistent profile directory.
        """
        config, resolved_engine = self._merged_config(engine=engine, headless=headless)
        profile_name = BrowserProfile(profile or self._settings.profiles.default_profile)
        profile_spec = self._profiles.resolve(profile_name, label=label)

        browser_id = new_browser_id()
        state = BrowserState(
            browser_id=browser_id,
            engine=resolved_engine,
            headless=config.headless,
            profile=profile_name,
        )

        if profile_spec.is_persistent:
            persistent = await self._factory.launch_persistent_context(
                resolved_engine,
                config,
                profile_spec.user_data_dir or "",
            )
            handle = BrowserHandle(browser_id=browser_id, browser=persistent, state=state)
            await self._pool.add_browser(handle)
            context_state = ContextState(
                context_id=new_context_id(),
                browser_id=browser_id,
                profile=profile_name,
            )
            context_handle = ContextHandle(
                context_id=context_state.context_id,
                browser_id=browser_id,
                context=persistent,
                state=context_state,
            )
            await self._pool.add_context(context_handle)
            return state

        browser = await self._factory.launch_browser(resolved_engine, config)
        handle = BrowserHandle(browser_id=browser_id, browser=browser, state=state)
        await self._pool.add_browser(handle)
        return state

    async def close(self, browser_id: str) -> None:
        """Close ``browser_id`` and all resources beneath it."""
        handle = self._pool.get_browser(browser_id)
        try:
            await self._factory.close_browser(handle.browser)
        finally:
            await self._pool.remove_browser(browser_id)

    def get(self, browser_id: str) -> BrowserHandle:
        """Return the live handle for ``browser_id``."""
        return self._pool.get_browser(browser_id)

    def state(self, browser_id: str) -> BrowserState:
        """Return the state snapshot for ``browser_id``."""
        return self._pool.browser_state(browser_id)
