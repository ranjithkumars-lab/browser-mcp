"""Configuration path resolution for the Browser MCP server."""

from __future__ import annotations

from pathlib import Path

from browser_mcp.config.defaults import APP_NAME

__all__ = ["bundled_settings_dir", "default_profiles_dir"]


def bundled_settings_dir() -> Path:
    """Return the directory containing bundled YAML settings files."""
    return Path(__file__).parent / "settings"


def default_profiles_dir() -> Path:
    """Return the default root directory for persistent browser profiles."""
    return Path.home() / f".{APP_NAME}" / "profiles"
