"""Generic repository abstraction."""

from __future__ import annotations

from typing import Any

from enterprise_mcp.persistence.models.base import Entity

__all__ = ["Repository"]


class Repository:
    """Abstract repository over persistent entities.

    Concrete implementations (SQLAlchemy, SQLite, PostgreSQL) are added in
    later phases.
    """

    async def get(self, entity_id: str) -> Entity:
        """Fetch a single entity by identifier."""
        raise NotImplementedError

    async def list(self, **filters: Any) -> list[Entity]:
        """Return entities matching ``filters``."""
        raise NotImplementedError

    async def save(self, entity: Entity) -> Entity:
        """Persist ``entity`` and return it."""
        raise NotImplementedError

    async def delete(self, entity_id: str) -> None:
        """Delete an entity by identifier."""
        raise NotImplementedError
