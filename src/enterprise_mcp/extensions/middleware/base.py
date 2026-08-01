"""Middleware abstraction."""

from __future__ import annotations

from typing import Any

__all__ = ["Middleware"]


class Middleware:
    """Abstract middleware wrapper around a request handler."""

    def __call__(self, handler: Any) -> Any:
        """Wrap ``handler`` and return the decorated callable."""
        raise NotImplementedError
