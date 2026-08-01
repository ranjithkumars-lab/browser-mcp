"""Browser MCP configuration.

Hierarchical loading mirrors the enterprise template: bundled defaults,
environment YAML, environment variables (prefix ``BROWSER_MCP_``), then
explicit programmatic overrides.
"""

from browser_mcp.config.loader import load_browser_settings
from browser_mcp.config.models import (
    BrowserConfig,
    BrowserEngine,
    BrowserProfile,
    BrowserSettings,
    PoolConfig,
    ProfilesConfig,
    ViewportConfig,
)

__all__ = [
    "BrowserConfig",
    "BrowserEngine",
    "BrowserProfile",
    "BrowserSettings",
    "PoolConfig",
    "ProfilesConfig",
    "ViewportConfig",
    "load_browser_settings",
]
