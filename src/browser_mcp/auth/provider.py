"""Driver provider abstraction for the authentication engine.

:class:`AuthProvider` isolates the auth subsystem from the underlying browser
automation library. Strategies only ever touch the provider interface; the
Playwright binding lives in :class:`PlaywrightAuthProvider`, so a CDP or
Selenium provider can replace it without touching the strategies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext

__all__ = ["AuthProvider", "PlaywrightAuthProvider"]


class AuthProvider(ABC):
    """Interface for browser context auth operations."""

    @abstractmethod
    async def inject_cookies(self, context: Any, cookies: list[dict[str, Any]]) -> None:
        """Inject ``cookies`` into ``context``."""

    @abstractmethod
    async def inject_headers(self, context: Any, headers: dict[str, str]) -> None:
        """Route requests through ``context`` with ``headers``."""

    @abstractmethod
    async def extract_storage_state(self, context: Any) -> dict[str, Any]:
        """Return the full storage state (cookies + localStorage) for ``context``."""

    @abstractmethod
    async def apply_storage_state(self, context: Any, state: dict[str, Any]) -> None:
        """Restore a previously extracted storage state into ``context``."""


class PlaywrightAuthProvider(AuthProvider):
    """Playwright-backed implementation of :class:`AuthProvider`.

    Only this class knows about Playwright; every other part of the auth
    subsystem works against the abstract interface.
    """

    async def inject_cookies(self, context: BrowserContext, cookies: list[dict[str, Any]]) -> None:
        await context.add_cookies(cookies)  # type: ignore[arg-type]

    async def inject_headers(self, context: BrowserContext, headers: dict[str, str]) -> None:
        await context.set_extra_http_headers(headers)

    async def extract_storage_state(self, context: BrowserContext) -> dict[str, Any]:
        state = await context.storage_state()
        return dict(state)

    async def apply_storage_state(self, context: BrowserContext, state: dict[str, Any]) -> None:
        await context.add_cookies(state.get("cookies", []))  # type: ignore[arg-type]
        origins: dict[str, Any] = state.get("origins") or {}
        for key, value in origins.items():
            try:
                await context.goto(key)  # type: ignore[attr-defined]
                localStorage_items: dict[str, str] = value.get("localStorage") or {}
                for name, val in localStorage_items.items():
                    await context.evaluate(f"localStorage.setItem('{name}', '{val}')")  # type: ignore[attr-defined]
            except Exception:
                pass
