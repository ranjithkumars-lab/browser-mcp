"""Plugin framework for browser-mcp."""

from browser_mcp.plugins.base import Plugin
from browser_mcp.plugins.context import PluginContext
from browser_mcp.plugins.loader import PluginLoader
from browser_mcp.plugins.manifest import PluginManifest, parse_manifest
from browser_mcp.plugins.permissions import Permissions
from browser_mcp.plugins.registry import PluginRegistry

__all__ = [
    "Permissions",
    "Plugin",
    "PluginContext",
    "PluginLoader",
    "PluginManifest",
    "PluginRegistry",
    "parse_manifest",
]
