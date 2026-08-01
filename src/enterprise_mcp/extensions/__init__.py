"""Extension framework scaffolds.

Plugins, middleware, hooks, and providers are implemented in later phases.
Phase 0 defines the extension points and the registry.
"""

from enterprise_mcp.extensions.base import Extension
from enterprise_mcp.extensions.hooks.base import Hook, HookDispatcher
from enterprise_mcp.extensions.middleware.base import Middleware
from enterprise_mcp.extensions.plugins.base import Plugin
from enterprise_mcp.extensions.providers.base import Provider
from enterprise_mcp.extensions.registry import ExtensionRegistry

__all__ = [
    "Extension",
    "ExtensionRegistry",
    "Hook",
    "HookDispatcher",
    "Middleware",
    "Plugin",
    "Provider",
]
