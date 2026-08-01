"""Extension base class."""

from __future__ import annotations

from typing import Any

__all__ = ["Extension"]


class Extension:
    """Base class for all extensions.

    Subclasses declare a stable ``name`` and implement :meth:`setup`.
    """

    name: str = "unnamed"
    version: str = "0.1.0"

    def setup(self, context: Any) -> None:
        """Wire the extension into the application context."""
        raise NotImplementedError

    def teardown(self) -> None:
        """Release extension resources."""
