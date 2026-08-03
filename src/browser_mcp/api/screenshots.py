"""Screenshot registry shared between the browser core and the REST API.

The :class:`ScreenshotStore` lives with :class:`ScreenshotManager` in the
browser core so every capture — regardless of transport (MCP tool, REST job,
chat agent) — is recorded once and can be served by the web UI.
"""

from __future__ import annotations

from browser_mcp.browser.screenshot import ScreenshotRecord, ScreenshotStore

__all__ = ["ScreenshotRecord", "ScreenshotStore"]
