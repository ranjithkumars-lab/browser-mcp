"""Shared configuration constants for the Browser MCP server."""

APP_NAME = "browser-mcp"
ENV_VAR_PREFIX = "BROWSER_MCP_"
DEFAULT_ENV = "development"
DEFAULT_PROFILES_DIR_NAME = "profiles"

SUPPORTED_ENGINES = ("chromium", "firefox", "webkit")
SUPPORTED_PROFILES = ("temporary", "persistent", "incognito")

__all__ = [
    "APP_NAME",
    "DEFAULT_ENV",
    "DEFAULT_PROFILES_DIR_NAME",
    "ENV_VAR_PREFIX",
    "SUPPORTED_ENGINES",
    "SUPPORTED_PROFILES",
]
