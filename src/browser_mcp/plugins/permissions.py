"""Minimal permissions scaffold.

Placeholder for future permission checking. For now it provides a
:class:`Permissions` value object that stores a set of granted
permission strings and a simple ``has()`` check.
"""

from __future__ import annotations

from collections.abc import Iterable

__all__ = ["Permissions"]


class Permissions:
    """A simple set of granted permission strings."""

    def __init__(self, granted: Iterable[str] | None = None) -> None:
        self._granted = set(granted or ())

    def grant(self, permission: str) -> None:
        self._granted.add(permission)

    def revoke(self, permission: str) -> None:
        self._granted.discard(permission)

    def has(self, permission: str) -> bool:
        return permission in self._granted

    def all(self) -> frozenset[str]:
        return frozenset(self._granted)
