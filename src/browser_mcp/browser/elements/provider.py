"""Locator provider abstraction.

:class:`LocatorProvider` isolates the element engine from the underlying
browser automation library. The engine and its strategies only ever touch the
provider interface; the Playwright binding lives in
:class:`PlaywrightLocatorProvider`, so a Selenium or CDP provider can replace
it without touching the engine.

The interface is split into *synchronous* creation/navigation methods
(Playwright locators are lazy and cheap to build) and *asynchronous* query
methods (which drive the browser).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.async_api import Frame, Locator, Page

__all__ = ["LocatorProvider", "PlaywrightLocatorProvider"]

# A locator *target* is either a page or a frame; both expose the locator API.
LocatorTarget = Any
LocatorHandle = Any


class LocatorProvider(ABC):
    """Interface isolating the element engine from a concrete browser engine."""

    # -- creation -------------------------------------------------------

    @abstractmethod
    def create_css(self, target: LocatorTarget, value: str) -> LocatorHandle:
        """Create a locator from a CSS selector."""

    @abstractmethod
    def create_xpath(self, target: LocatorTarget, value: str) -> LocatorHandle:
        """Create a locator from an XPath expression."""

    @abstractmethod
    def create_text(
        self, target: LocatorTarget, value: str, *, exact: bool = False
    ) -> LocatorHandle:
        """Create a locator matching an element by its visible text."""

    @abstractmethod
    def create_role(
        self,
        target: LocatorTarget,
        role: str,
        *,
        name: str | None = None,
        exact: bool = False,
    ) -> LocatorHandle:
        """Create a locator matching an element by ARIA role and name."""

    @abstractmethod
    def create_playwright(self, target: LocatorTarget, value: str) -> LocatorHandle:
        """Create a locator from a raw engine selector string."""

    @abstractmethod
    def nth(self, locator: LocatorHandle, index: int) -> LocatorHandle:
        """Return the ``index``-th match of ``locator``."""

    # -- queries --------------------------------------------------------

    @abstractmethod
    async def count(self, locator: LocatorHandle) -> int:
        """Return the number of matches for ``locator``."""

    @abstractmethod
    async def inner_text(self, locator: LocatorHandle) -> str:
        """Return the rendered inner text of the first match."""

    @abstractmethod
    async def inner_html(self, locator: LocatorHandle) -> str:
        """Return the inner HTML of the first match."""

    @abstractmethod
    async def outer_html(self, locator: LocatorHandle) -> str:
        """Return the outer HTML of the first match."""

    @abstractmethod
    async def get_attribute(self, locator: LocatorHandle, name: str) -> str | None:
        """Return the value of attribute ``name`` or ``None``."""

    @abstractmethod
    async def is_visible(self, locator: LocatorHandle) -> bool:
        """Return whether the first match is visible."""

    @abstractmethod
    async def is_enabled(self, locator: LocatorHandle) -> bool:
        """Return whether the first match is enabled."""

    @abstractmethod
    async def is_editable(self, locator: LocatorHandle) -> bool:
        """Return whether the first match is editable (Phase 4 preparatory)."""

    @abstractmethod
    async def is_checked(self, locator: LocatorHandle) -> bool:
        """Return whether the first match is checked (Phase 4 preparatory)."""

    @abstractmethod
    async def is_disabled(self, locator: LocatorHandle) -> bool:
        """Return whether the first match is disabled."""

    @abstractmethod
    async def wait_for(
        self,
        locator: LocatorHandle,
        state: str = "attached",
        timeout: int | None = None,
        *,
        strict: bool | None = None,
    ) -> None:
        """Wait until ``locator`` reaches ``state`` within ``timeout`` ms."""


class PlaywrightLocatorProvider(LocatorProvider):
    """Playwright-backed implementation of :class:`LocatorProvider`.

    Only this class (and this module) knows about Playwright; every other part
    of the element engine works against the abstract interface.
    """

    def create_css(self, target: Page | Frame, value: str) -> Locator:
        return target.locator(value)

    def create_xpath(self, target: Page | Frame, value: str) -> Locator:
        return target.locator(f"xpath={value}")

    def create_text(self, target: Page | Frame, value: str, *, exact: bool = False) -> Locator:
        return target.get_by_text(value, exact=exact)

    def create_role(
        self,
        target: Page | Frame,
        role: str,
        *,
        name: str | None = None,
        exact: bool = False,
    ) -> Locator:
        return target.get_by_role(role, name=name, exact=exact) # type: ignore

    def create_playwright(self, target: Page | Frame, value: str) -> Locator:
        return target.locator(value)

    def nth(self, locator: Locator, index: int) -> Locator:
        return locator.nth(index)

    async def count(self, locator: Locator) -> int:
        return await locator.count()

    async def inner_text(self, locator: Locator) -> str:
        return await locator.inner_text()

    async def inner_html(self, locator: Locator) -> str:
        return await locator.inner_html()

    async def outer_html(self, locator: Locator) -> str:
        return await locator.evaluate("(el) => el.outerHTML")

    async def get_attribute(self, locator: Locator, name: str) -> str | None:
        return await locator.get_attribute(name)

    async def is_visible(self, locator: Locator) -> bool:
        return await locator.is_visible()

    async def is_enabled(self, locator: Locator) -> bool:
        return await locator.is_enabled()

    async def is_editable(self, locator: Locator) -> bool:
        return await locator.is_editable()

    async def is_checked(self, locator: Locator) -> bool:
        return await locator.is_checked()

    async def is_disabled(self, locator: Locator) -> bool:
        return await locator.is_disabled()

    async def wait_for(
        self,
        locator: Locator,
        state: str = "attached",
        timeout: int | None = None,
        *,
        strict: bool | None = None,
    ) -> None:
        target = locator.first if strict is False else locator
        await target.wait_for(state=state, timeout=timeout) # type: ignore
