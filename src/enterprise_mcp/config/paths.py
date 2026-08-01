"""Configuration path resolution."""

from __future__ import annotations

from pathlib import Path

import platformdirs

from enterprise_mcp.config.defaults import APP_NAME

__all__ = ["bundled_defaults_path", "bundled_settings_dir", "default_config_dir"]


def default_config_dir() -> Path:
    """Return the per-user configuration directory for this application."""
    return Path(platformdirs.user_config_dir(APP_NAME))


def bundled_settings_dir() -> Path:
    """Return the directory containing bundled YAML settings files."""
    return Path(__file__).parent / "settings"


def bundled_defaults_path() -> Path:
    """Return the path to the bundled default settings file."""
    return bundled_settings_dir() / "default.yaml"
