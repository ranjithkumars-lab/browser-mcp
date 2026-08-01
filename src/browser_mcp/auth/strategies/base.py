"""Abstract base class for authentication strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

__all__ = ["BaseAuthStrategy"]


class BaseAuthStrategy(ABC):
    """Abstract base class for authentication execution."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the strategy identifier."""

    @abstractmethod
    async def execute(self, context: Any, credentials: Any) -> dict[str, Any]:
        """Perform the authentication against ``context``.

        Returns a structured mapping with at least ``success`` and
        ``session`` fields.
        """
