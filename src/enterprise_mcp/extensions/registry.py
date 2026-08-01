"""Extension registry."""

from __future__ import annotations

from enterprise_mcp.extensions.base import Extension
from enterprise_mcp.utils.errors import EnterpriseMCPError

__all__ = ["ExtensionRegistry"]


class ExtensionError(EnterpriseMCPError):
    """Raised when an extension cannot be registered or set up."""


class ExtensionRegistry:
    """Registry of named extensions."""

    def __init__(self) -> None:
        self._extensions: dict[str, Extension] = {}

    def register(self, extension: Extension) -> None:
        """Register ``extension`` by name."""
        if extension.name in self._extensions:
            raise ExtensionError(f"extension '{extension.name}' is already registered")
        self._extensions[extension.name] = extension

    def get(self, name: str) -> Extension:
        """Return the extension registered under ``name``."""
        extension = self._extensions.get(name)
        if extension is None:
            raise ExtensionError(f"extension '{name}' is not registered")
        return extension

    def list(self) -> list[Extension]:
        """Return all registered extensions."""
        return list(self._extensions.values())

    def __contains__(self, name: str) -> bool:
        return name in self._extensions
