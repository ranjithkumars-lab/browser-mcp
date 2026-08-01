"""Base formatter abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

__all__ = ["BaseFormatter"]


class BaseFormatter(ABC):
    """Abstract base for all output formatters."""

    @property
    def format_name(self) -> str:
        return self.__class__.__name__.removesuffix("Formatter").lower()

    @abstractmethod
    def format(self, data: list[Any]) -> str:
        """Serialise ``data`` (list of typed models) into a string."""
