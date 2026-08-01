"""Plugin base class."""

from __future__ import annotations

from typing import ClassVar

from enterprise_mcp.extensions.base import Extension

__all__ = ["Plugin"]


class Plugin(Extension):
    """Base class for feature plugins.

    Plugins expose a manifest (metadata, version, permissions, input/output
    schemas) and can register tools during :meth:`setup`. The plugin
    framework is implemented in a later phase.
    """

    manifest: ClassVar[dict[str, object]] = {}
