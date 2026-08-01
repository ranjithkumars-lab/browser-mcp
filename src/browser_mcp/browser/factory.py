"""Playwright-backed browser factory.

This is the only module in the browser engine that imports Playwright. It
translates configuration into concrete Playwright objects and converts
Playwright failures into domain errors.

Playwright browser binaries are **not** auto-installed. When the required
binary is missing, :meth:`launch_browser` raises a clear :class:`BrowserError`
with installation guidance instead.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from browser_mcp.config.models import BrowserConfig, BrowserEngine, BrowserProfile
from browser_mcp.errors import BrowserError, ProfileError

if TYPE_CHECKING:
    from playwright.async_api import (
        Browser,
        BrowserContext,
        BrowserType,
        Page,
        Playwright,
    )

__all__ = ["BrowserFactory"]

_LOG = structlog.get_logger("browser_mcp.factory")

_ENGINE_ATTR: dict[BrowserEngine, str] = {
    BrowserEngine.CHROMIUM: "chromium",
    BrowserEngine.FIREFOX: "firefox",
    BrowserEngine.WEBKIT: "webkit",
}

_MISSING_BINARY_HINT = (
    "Playwright browser binaries are missing. Install them with "
    "'playwright install {engine}' (or run the project bootstrap script) "
    "and restart the server."
)


class BrowserFactory:
    """Creates and destroys Playwright browser objects."""

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._logger = structlog.get_logger("browser_mcp.factory")

    @property
    def is_started(self) -> bool:
        """Return whether the underlying Playwright driver is running."""
        return self._playwright is not None

    async def start(self) -> None:
        """Start the Playwright driver if it is not already running."""
        if self._playwright is not None:
            return
        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
        except Exception as exc:
            raise BrowserError(f"failed to start Playwright driver: {exc}") from exc
        self._logger.info("playwright_started")

    async def stop(self) -> None:
        """Stop the Playwright driver."""
        if self._playwright is None:
            return
        try:
            await self._playwright.stop()
        except Exception as exc:
            self._logger.warning("playwright_stop_failed", error=str(exc))
        finally:
            self._playwright = None
        self._logger.info("playwright_stopped")

    def _browser_type(self, engine: BrowserEngine) -> BrowserType:
        if self._playwright is None:
            from browser_mcp.errors import BrowserNotReadyError

            raise BrowserNotReadyError("factory not started; call start() first")
        attribute = _ENGINE_ATTR[engine]
        browser_type = getattr(self._playwright, attribute, None)
        if browser_type is None:
            raise BrowserError(f"engine '{engine.value}' is not supported by Playwright")
        return browser_type

    @staticmethod
    def _launch_options(config: BrowserConfig) -> dict[str, Any]:
        return {
            "headless": config.headless,
            "slow_mo": config.slow_mo,
        }

    @staticmethod
    def _context_options(config: BrowserConfig) -> dict[str, Any]:
        options: dict[str, Any] = {
            "viewport": {
                "width": config.viewport.width,
                "height": config.viewport.height,
            },
            "ignore_https_errors": config.ignore_https_errors,
        }
        if config.locale:
            options["locale"] = config.locale
        if config.timezone:
            options["timezone_id"] = config.timezone
        if config.downloads_dir:
            options["accept_downloads"] = True
        if config.user_agent:
            options["user_agent"] = config.user_agent
        return options

    async def launch_browser(self, engine: BrowserEngine, config: BrowserConfig) -> Browser:
        """Launch a fresh browser instance for ``engine``.

        Raises
        ------
        BrowserError
            When Playwright binaries are missing or the launch fails.
        """
        browser_type = self._browser_type(engine)
        try:
            browser = await browser_type.launch(**self._launch_options(config))
        except Exception as exc:
            raise BrowserError(
                f"failed to launch '{engine.value}': {exc}. "
                + _MISSING_BINARY_HINT.format(engine=engine.value)
            ) from exc
        self._logger.info(
            "browser_launched", engine=engine.value, headless=config.headless
        )
        return browser

    async def new_context(
        self,
        browser: Browser,
        profile: BrowserProfile,
        config: BrowserConfig,
    ) -> BrowserContext:
        """Create a new context inside ``browser`` for ``profile``."""
        options = self._context_options(config)
        if profile == BrowserProfile.INCOGNITO:
            options.setdefault("incognito", True)
        try:
            return await browser.new_context(**options)
        except Exception as exc:
            raise BrowserError(f"failed to create context: {exc}") from exc

    async def launch_persistent_context(
        self,
        engine: BrowserEngine,
        config: BrowserConfig,
        user_data_dir: str | Path,
    ) -> BrowserContext:
        """Launch a persistent context backed by ``user_data_dir``."""
        browser_type = self._browser_type(engine)
        options = self._context_options(config)
        options.update(self._launch_options(config))
        try:
            return await browser_type.launch_persistent_context(
                str(user_data_dir), **options
            )
        except Exception as exc:
            raise ProfileError(
                f"failed to launch persistent context at '{user_data_dir}': {exc}"
            ) from exc

    async def new_page(self, context: BrowserContext) -> Page:
        """Open a new blank page in ``context``."""
        try:
            return await context.new_page()
        except Exception as exc:
            raise BrowserError(f"failed to open page: {exc}") from exc

    async def close_browser(self, browser: Browser) -> None:
        """Close ``browser`` and release its resources."""
        try:
            await browser.close()
        except Exception as exc:
            self._logger.warning("browser_close_failed", error=str(exc))
            raise BrowserError(f"failed to close browser: {exc}") from exc

    async def close_context(self, context: BrowserContext) -> None:
        """Close ``context`` and its pages."""
        try:
            await context.close()
        except Exception as exc:
            self._logger.warning("context_close_failed", error=str(exc))
            raise BrowserError(f"failed to close context: {exc}") from exc

    async def close_page(self, page: Page) -> None:
        """Close ``page``."""
        try:
            await page.close()
        except Exception as exc:
            self._logger.warning("page_close_failed", error=str(exc))
            raise BrowserError(f"failed to close page: {exc}") from exc
