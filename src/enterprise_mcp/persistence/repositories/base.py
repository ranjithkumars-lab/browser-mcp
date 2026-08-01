"""Repository implementation base."""

from __future__ import annotations

from typing import Any

from enterprise_mcp.persistence.base import Repository
from enterprise_mcp.persistence.models.base import Entity

__all__ = ["GenericRepository"]


class GenericRepository(Repository):
    """Base implementation useful for concrete repositories."""

    async def get(self, entity_id: str) -> Entity:
        raise NotImplementedError("implement in a later phase")

    async def list(self, **filters: Any) -> list[Entity]:
        raise NotImplementedError("implement in a later phase")

    async def save(self, entity: Entity) -> Entity:
        raise NotImplementedError("implement in a later phase")

    async def delete(self, entity_id: str) -> None:
        raise NotImplementedError("implement in a later phase")
