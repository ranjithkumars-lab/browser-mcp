"""Browser resource pool enforcing the strict resource hierarchy.

    Pool -> Browser -> Context -> Page

The pool is the single source of truth for live browser resources. It
enforces capacity limits, guarantees unique identifiers, and exposes read-only
statistics for health reporting.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import TYPE_CHECKING

from browser_mcp.browser.models import (
    BrowserHandle,
    BrowserState,
    ContextHandle,
    ContextState,
    PageHandle,
    PageState,
)
from browser_mcp.errors import (
    BrowserNotFoundError,
    BrowserPoolLimitError,
    ContextNotFoundError,
    PageNotFoundError,
)

if TYPE_CHECKING:
    from browser_mcp.config.models import BrowserSettings

__all__ = ["BrowserPool"]


class BrowserPool:
    """Strict hierarchy container for live browser resources."""

    def __init__(self, settings: BrowserSettings) -> None:
        self._settings = settings
        self._lock = asyncio.Lock()
        self._browsers: dict[str, BrowserHandle] = {}
        self._contexts: dict[str, ContextHandle] = {}
        self._pages: dict[str, PageHandle] = {}

    # -- capacity -------------------------------------------------------

    @property
    def max_browsers(self) -> int:
        """Maximum number of concurrent browsers allowed."""
        return self._settings.pool.max_browsers

    @property
    def max_contexts_per_browser(self) -> int:
        """Maximum contexts allowed inside a single browser."""
        return self._settings.pool.max_contexts_per_browser

    @property
    def max_pages_per_context(self) -> int:
        """Maximum pages allowed inside a single context."""
        return self._settings.pool.max_pages_per_context

    # -- read -----------------------------------------------------------

    def browser_ids(self) -> Iterable[str]:
        """Iterate over all live browser identifiers."""
        return tuple(self._browsers)

    def context_ids(self) -> Iterable[str]:
        """Iterate over all live context identifiers."""
        return tuple(self._contexts)

    def page_ids(self) -> Iterable[str]:
        """Iterate over all live page identifiers."""
        return tuple(self._pages)

    def get_browser(self, browser_id: str) -> BrowserHandle:
        """Return the browser handle for ``browser_id``."""
        handle = self._browsers.get(browser_id)
        if handle is None:
            raise BrowserNotFoundError(f"browser '{browser_id}' not found")
        return handle

    def get_context(self, context_id: str) -> ContextHandle:
        """Return the context handle for ``context_id``."""
        handle = self._contexts.get(context_id)
        if handle is None:
            raise ContextNotFoundError(f"context '{context_id}' not found")
        return handle

    def get_page(self, page_id: str) -> PageHandle:
        """Return the page handle for ``page_id``."""
        handle = self._pages.get(page_id)
        if handle is None:
            raise PageNotFoundError(f"page '{page_id}' not found")
        return handle

    def has_browser(self, browser_id: str) -> bool:
        """Return whether ``browser_id`` is a live browser."""
        return browser_id in self._browsers

    def has_context(self, context_id: str) -> bool:
        """Return whether ``context_id`` is a live context."""
        return context_id in self._contexts

    def has_page(self, page_id: str) -> bool:
        """Return whether ``page_id`` is a live page."""
        return page_id in self._pages

    # -- write ----------------------------------------------------------

    async def add_browser(self, handle: BrowserHandle) -> None:
        """Register ``handle``, enforcing the browser capacity limit."""
        async with self._lock:
            if handle.browser_id in self._browsers:
                raise BrowserPoolLimitError(f"browser '{handle.browser_id}' is already registered")
            if len(self._browsers) >= self.max_browsers:
                raise BrowserPoolLimitError(f"browser pool capacity reached ({self.max_browsers})")
            self._browsers[handle.browser_id] = handle

    async def add_context(self, handle: ContextHandle) -> None:
        """Register a context under its owning browser."""
        async with self._lock:
            if handle.context_id in self._contexts:
                raise BrowserPoolLimitError(f"context '{handle.context_id}' is already registered")
            browser = self._browsers.get(handle.browser_id)
            if browser is None:
                raise BrowserNotFoundError(f"browser '{handle.browser_id}' not found for context")
            if len(browser.state.contexts) >= self.max_contexts_per_browser:
                raise BrowserPoolLimitError(
                    f"context capacity reached for browser '{handle.browser_id}'"
                )
            self._contexts[handle.context_id] = handle
            browser.state.contexts.append(handle.state)

    async def add_page(self, handle: PageHandle) -> None:
        """Register a page under its owning context."""
        async with self._lock:
            if handle.page_id in self._pages:
                raise BrowserPoolLimitError(f"page '{handle.page_id}' is already registered")
            context = self._contexts.get(handle.context_id)
            if context is None:
                raise ContextNotFoundError(f"context '{handle.context_id}' not found for page")
            if len(context.state.pages) >= self.max_pages_per_context:
                raise BrowserPoolLimitError(
                    f"page capacity reached for context '{handle.context_id}'"
                )
            self._pages[handle.page_id] = handle
            context.state.pages.append(handle.state)

    async def remove_browser(self, browser_id: str) -> None:
        """Remove a browser and all of its contexts and pages."""
        async with self._lock:
            handle = self._browsers.pop(browser_id, None)
            if handle is None:
                return
            for context in handle.state.contexts:
                for page in context.pages:
                    self._pages.pop(page.page_id, None)
                self._contexts.pop(context.context_id, None)

    async def remove_context(self, context_id: str) -> None:
        """Remove a context and all of its pages."""
        async with self._lock:
            handle = self._contexts.pop(context_id, None)
            if handle is None:
                return
            for page in handle.state.pages:
                self._pages.pop(page.page_id, None)
            browser = self._browsers.get(handle.browser_id)
            if browser is not None:
                browser.state.contexts = [
                    c for c in browser.state.contexts if c.context_id != context_id
                ]

    async def remove_page(self, page_id: str) -> None:
        """Remove a single page."""
        async with self._lock:
            handle = self._pages.pop(page_id, None)
            if handle is None:
                return
            context = self._contexts.get(handle.context_id)
            if context is not None:
                context.state.pages = [p for p in context.state.pages if p.page_id != page_id]

    # -- statistics -----------------------------------------------------

    def stats(self) -> dict[str, int]:
        """Return live pool statistics for health reporting."""
        return {
            "browsers": len(self._browsers),
            "contexts": len(self._contexts),
            "pages": len(self._pages),
            "max_browsers": self.max_browsers,
        }

    def browser_state(self, browser_id: str) -> BrowserState:
        """Return the state snapshot for ``browser_id``."""
        return self.get_browser(browser_id).state

    def context_state(self, context_id: str) -> ContextState:
        """Return the state snapshot for ``context_id``."""
        return self.get_context(context_id).state

    def page_state(self, page_id: str) -> PageState:
        """Return the state snapshot for ``page_id``."""
        return self.get_page(page_id).state

    @property
    def is_empty(self) -> bool:
        """Return whether the pool holds no resources at all."""
        return not self._browsers

    def all_browsers(self) -> list[BrowserHandle]:
        """Return all live browser handles."""
        return list(self._browsers.values())

    def all_contexts(self) -> list[ContextHandle]:
        """Return all live context handles."""
        return list(self._contexts.values())

    def all_pages(self) -> list[PageHandle]:
        """Return all live page handles."""
        return list(self._pages.values())
