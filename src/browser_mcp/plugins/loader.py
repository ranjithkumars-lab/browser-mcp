"""Plugin discovery and instantiation.

The loader scans a directory for plugin manifests, imports the
entrypoint module, instantiates the plugin class, and registers
it with the :class:`PluginRegistry`.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from browser_mcp.plugins.base import Plugin
from browser_mcp.plugins.manifest import PluginManifest, parse_manifest
from browser_mcp.plugins.registry import PluginRegistry

__all__ = ["PluginLoader"]


class PluginLoader:
    """Discovers, instantiates, and registers plugins."""

    def __init__(self, plugins_dir: Path, registry: PluginRegistry | None = None) -> None:
        self._plugins_dir = plugins_dir
        self._registry = registry or PluginRegistry()

    @property
    def registry(self) -> PluginRegistry:
        return self._registry

    def discover(self) -> list[PluginManifest]:
        """Scan ``plugins_dir`` for manifest files and return parsed manifests."""
        manifests: list[PluginManifest] = []
        if not self._plugins_dir.exists():
            return manifests

        for path in sorted(self._plugins_dir.rglob("manifest.yaml")):
            try:
                manifest = parse_manifest(path)
                manifests.append(manifest)
            except (ValueError, FileNotFoundError, yaml.YAMLError) as exc:
                _log_error("manifest_parse_failed", path=path, error=str(exc))

        for path in sorted(self._plugins_dir.rglob("manifest.json")):
            if path.with_suffix(".yaml").exists():
                continue
            try:
                manifest = parse_manifest(path)
                manifests.append(manifest)
            except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
                _log_error("manifest_parse_failed", path=path, error=str(exc))

        return manifests

    def load(self, manifest: PluginManifest) -> Plugin:
        """Instantiate a plugin from its manifest entrypoint."""
        module_path, class_name = _split_entrypoint(manifest.entrypoint)

        if module_path in sys.modules:
            module = sys.modules[module_path]
        else:
            module = importlib.import_module(module_path)

        cls = getattr(module, class_name)
        if not issubclass(cls, Plugin):
            raise TypeError(
                f"Entrypoint '{manifest.entrypoint}' is not a Plugin subclass"
            )

        plugin = cls()
        return plugin

    async def load_all(self, context: Any) -> PluginRegistry:
        """Discover, instantiate, initialise, and register all plugins."""
        manifests = self.discover()
        for manifest in manifests:
            try:
                plugin = self.load(manifest)
                self._registry.register(manifest.name, plugin)
                await plugin.initialize(context)
            except Exception as exc:
                _log_error(
                    "plugin_load_failed",
                    name=manifest.name,
                    error=str(exc),
                )
        return self._registry


def _split_entrypoint(entrypoint: str) -> tuple[str, str]:
    """Split ``module.path:ClassName`` into (module_path, class_name)."""
    if ":" not in entrypoint:
        raise ValueError(
            f"Entrypoint '{entrypoint}' must be in the form 'module.path:ClassName'"
        )
    module_path, class_name = entrypoint.rsplit(":", 1)
    return module_path, class_name


def _log_error(event: str, **kwargs: Any) -> None:
    import structlog

    logger = structlog.get_logger("browser_mcp.plugins.loader")
    logger.error(event, **kwargs)
