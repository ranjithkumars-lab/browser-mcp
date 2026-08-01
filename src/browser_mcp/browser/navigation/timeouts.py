"""Global timeout resolution.

Timeouts are configured globally (``BrowserSettings.timeouts``) and only
overridden per-call when a caller explicitly passes a value. This avoids
scattering timeout defaults across the navigation package.
"""

from __future__ import annotations

from typing import Literal

from browser_mcp.config.models import BrowserSettings

__all__ = ["TimeoutKind", "resolve_timeout"]

TimeoutKind = Literal["default", "navigation", "interaction", "wait"]

_KIND_ATTR: dict[TimeoutKind, str] = {
    "default": "default_timeout_ms",
    "navigation": "navigation_timeout_ms",
    "interaction": "interaction_timeout_ms",
    "wait": "wait_timeout_ms",
}


def resolve_timeout(
    settings: BrowserSettings,
    kind: TimeoutKind,
    override_ms: int | None,
) -> int:
    """Return the effective timeout for ``kind`` in milliseconds.

    ``override_ms`` wins when provided; otherwise the globally configured
    timeout for ``kind`` is returned.
    """
    if override_ms is not None:
        if override_ms < 1:
            from browser_mcp.errors import NavigationTimeoutError

            raise NavigationTimeoutError("timeout must be a positive number of milliseconds")
        return override_ms
    return int(getattr(settings.timeouts, _KIND_ATTR[kind]))
