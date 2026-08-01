"""Database abstraction."""

from __future__ import annotations

from typing import Any

__all__ = ["Database"]


class Database:
    """Abstract database connection manager.

    Concrete backends (SQLite, PostgreSQL, Redis) are implemented in later
    phases and must never be imported directly by business logic.
    """

    async def connect(self) -> None:
        """Establish the connection pool."""
        raise NotImplementedError

    async def disconnect(self) -> None:
        """Close the connection pool."""
        raise NotImplementedError

    async def execute(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Execute ``statement`` and return its result."""
        raise NotImplementedError
