"""Playwright binary runtime diagnostics.

Playwright browser binaries are **not** auto-installed at startup. This module
performs a lightweight, non-launching check that the required binaries are
present so operators can surface a clear error instead of a cryptic traceback.
"""

from __future__ import annotations

from dataclasses import dataclass

from browser_mcp.config.models import BrowserEngine

__all__ = ["BinaryCheckResult", "check_playwright_binaries"]


@dataclass(slots=True, frozen=True)
class BinaryCheckResult:
    """Outcome of the Playwright binary availability check."""

    engine: str
    installed: bool
    detail: str


def _resolve_executable(engine: BrowserEngine) -> str | None:
    """Return the browser executable path without launching it.

    Uses Playwright's internal registry; returns ``None`` when the browser is
    not installed. This avoids spawning a browser process during health checks.
    """
    try:
        from playwright._impl._driver import (
            compute_driver_executable,  # type: ignore[import-untyped]
        )

        driver = compute_driver_executable()
        from playwright._impl._registry import Registry  # type: ignore[import-untyped]

        registry = Registry(driver)
        return registry.executable_path(engine.value)
    except Exception:
        return None


def check_playwright_binaries(engine: BrowserEngine = BrowserEngine.CHROMIUM) -> BinaryCheckResult:
    """Return whether the Playwright binary for ``engine`` is installed."""
    path = _resolve_executable(engine)
    if path:
        return BinaryCheckResult(engine=engine.value, installed=True, detail=path)
    return BinaryCheckResult(
        engine=engine.value,
        installed=False,
        detail=f"missing; run 'playwright install {engine.value}'",
    )
