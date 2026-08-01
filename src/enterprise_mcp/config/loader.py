"""Hierarchical configuration loader.

Merge order (lowest to highest priority):

1. Bundled ``settings/default.yaml``
2. Environment-specific YAML (``settings/{env}.yaml``)
3. Environment variables prefixed with ``ENTERPRISE_MCP_``
4. Explicit programmatic overrides
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

import yaml

from enterprise_mcp.config.defaults import DEFAULT_ENV, ENV_VAR_PREFIX
from enterprise_mcp.config.models import Settings
from enterprise_mcp.config.paths import bundled_settings_dir
from enterprise_mcp.utils.errors import ConfigError

__all__ = ["load_settings"]


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            raw: Any = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ConfigError(f"failed to parse YAML file '{path}': {exc}") from exc
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ConfigError(f"YAML file '{path}' must contain a mapping at its root")
    return cast(dict[str, Any], raw)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(
                cast(dict[str, Any], merged[key]),
                cast(dict[str, Any], value),
            )
        else:
            merged[key] = value
    return merged


def _effective_environment(env: str | None) -> str:
    if env is not None:
        return env
    return os.environ.get(f"{ENV_VAR_PREFIX}ENV", DEFAULT_ENV)


def _env_overrides() -> dict[str, Any]:
    """Extract explicit environment variable overrides for settings fields."""
    base = Settings()
    return base.model_dump(exclude_unset=True)


def load_settings(
    *,
    env: str | None = None,
    settings_dir: str | Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> Settings:
    """Load and validate application settings.

    Parameters
    ----------
    env:
        Environment name. Falls back to ``ENTERPRISE_MCP_ENV`` then ``development``.
    settings_dir:
        Directory containing ``default.yaml`` and ``{env}.yaml``. Defaults to the
        bundled settings directory.
    overrides:
        Highest-priority programmatic overrides (e.g. from the CLI).
    """
    directory = Path(settings_dir) if settings_dir else bundled_settings_dir()
    environment = _effective_environment(env)

    merged: dict[str, Any] = {}
    merged = _deep_merge(merged, _read_yaml(directory / "default.yaml"))
    merged = _deep_merge(merged, _read_yaml(directory / f"{environment}.yaml"))
    merged = _deep_merge(merged, _env_overrides())
    if overrides:
        merged = _deep_merge(merged, overrides)

    return Settings.model_validate(merged)
