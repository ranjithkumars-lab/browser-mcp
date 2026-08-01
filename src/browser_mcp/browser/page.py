"""Page lifecycle management.

``PageManager`` opens and closes pages inside a live context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from browser_mcp.browser.factory import BrowserFactory
from browser_mcp.browser.models import PageHandle, PageState, new_page_id
from browser_mcp.browser.pool import BrowserPool

if TYPE_CHECKING:
    from playwright.async_api import Page

__all__ = ["PageManager"]


class PageManager:
    """Opens and closes pages within a live browser context."""

    def __init__(
        self,
        pool: BrowserPool,
        factory: BrowserFactory,
    ) -> None:
        self._pool = pool
        self._factory = factory

    async def create(self, context_id: str, *, url: str | None = None) -> PageState:
        """Open a new page in ``context_id`` and optionally navigate to ``url``."""
        context_handle = self._pool.get_context(context_id)
        page = await self._factory.new_page(context_handle.context)
        if url:
            try:
                await page.goto(url)
            except Exception as exc:
                await page.close()
                from browser_mcp.errors import NavigationError

                raise NavigationError(f"failed to navigate to '{url}': {exc}") from exc
        return await self.register(context_id, page, url=url)

    async def register(self, context_id: str, page: Page, *, url: str | None = None) -> PageState:
        """Register an existing (e.g. popup) page in ``context_id``.

        The live ``page`` is wrapped in a :class:`PageHandle` and added to the
        pool so popups and externally-created pages participate in the normal
        lifecycle and capacity limits.
        """
        context_handle = self._pool.get_context(context_id)
        page_id = new_page_id()
        state = PageState(page_id=page_id, context_id=context_id, url=url)
        handle = PageHandle(
            page_id=page_id,
            context_id=context_id,
            browser_id=context_handle.browser_id,
            page=page,
            state=state,
        )
        await self._pool.add_page(handle)
        return state

    async def close(self, page_id: str) -> None:
        """Close ``page_id``."""
        handle = self._pool.get_page(page_id)
        try:
            await self._factory.close_page(handle.page)
        finally:
            await self._pool.remove_page(page_id)

    def get(self, page_id: str) -> PageHandle:
        """Return the live handle for ``page_id``."""
        return self._pool.get_page(page_id)

    def state(self, page_id: str) -> PageState:
        """Return the state snapshot for ``page_id``."""
        return self._pool.page_state(page_id)
