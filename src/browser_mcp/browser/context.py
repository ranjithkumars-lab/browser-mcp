"""Context lifecycle management.

``ContextManager`` creates and closes browser contexts (tabs-with-storage
sandboxes) inside an existing browser. Contexts respect the browser's
configured profile and per-browser capacity limits.
"""

from __future__ import annotations

from browser_mcp.browser.factory import BrowserFactory
from browser_mcp.browser.models import (
    ContextHandle,
    ContextState,
    new_context_id,
)
from browser_mcp.browser.pool import BrowserPool
from browser_mcp.browser.profile import ProfileManager
from browser_mcp.config.models import BrowserProfile, BrowserSettings
from browser_mcp.errors import ContextError

__all__ = ["ContextManager"]


class ContextManager:
    """Creates and closes browser contexts within a live browser."""

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

    async def create(
        self,
        browser_id: str,
        *,
        profile: BrowserProfile | str | None = None,
        label: str | None = None,
    ) -> ContextState:
        """Create a new context inside ``browser_id``."""
        browser_handle = self._pool.get_browser(browser_id)
        profile_name = BrowserProfile(profile or self._settings.profiles.default_profile)
        profile_spec = self._profiles.resolve(profile_name, label=label)
        if profile_spec.is_persistent:
            raise ContextError(
                "persistent profiles create their own context at launch; "
                "use create_session with profile='persistent' instead"
            )

        context_id = new_context_id()
        context = await self._factory.new_context(
            browser_handle.browser, profile_name, self._settings.browser
        )
        state = ContextState(
            context_id=context_id,
            browser_id=browser_id,
            profile=profile_name,
        )
        handle = ContextHandle(
            context_id=context_id,
            browser_id=browser_id,
            context=context,
            state=state,
        )
        await self._pool.add_context(handle)
        return state

    async def close(self, context_id: str) -> None:
        """Close ``context_id`` and all of its pages."""
        handle = self._pool.get_context(context_id)
        try:
            await self._factory.close_context(handle.context)
        finally:
            await self._pool.remove_context(context_id)

    def get(self, context_id: str):
        """Return the live handle for ``context_id``."""
        return self._pool.get_context(context_id)

    def state(self, context_id: str) -> ContextState:
        """Return the state snapshot for ``context_id``."""
        return self._pool.context_state(context_id)
