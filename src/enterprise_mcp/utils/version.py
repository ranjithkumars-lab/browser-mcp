"""Version helpers."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

__all__ = ["get_version"]


def get_version() -> str:
    """Return the installed package version, falling back to the module constant."""
    try:
        return version("enterprise-mcp-server")
    except PackageNotFoundError:
        from enterprise_mcp import __version__

        return __version__
