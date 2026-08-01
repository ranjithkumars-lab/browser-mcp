"""Base collector abstraction.

A :class:`BaseCollector` receives a Playwright (or fake) page handle and
extracts *raw* data as a list of untyped dicts.  Subclasses implement
:meth:`collect` and may override :attr:`name` for event reporting.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

__all__ = ["BaseCollector"]


class BaseCollector(ABC):
    """Abstract base for all scraper data collectors."""

    @property
    def name(self) -> str:
        """Return the collector's short name (used in events/log)."""
        return self.__class__.__name__.removesuffix("Collector").lower()

    @abstractmethod
    async def collect(self, page: Any, **kwargs: Any) -> list[dict[str, Any]]:
        """Extract raw data from ``page``.

        Parameters
        ----------
        page:
            A Playwright ``Page`` (or compatible fake).
        **kwargs:
            Collector-specific options (selectors, limits, etc.).

        Returns
        -------
        A list of raw dicts.  A single-element list is returned for singleton
        collectors (text, metadata).
        """

    async def safe_collect(self, page: Any, **kwargs: Any) -> list[dict[str, Any]]:
        """Call :meth:`collect` and wrap failures in a single-item error dict."""
        try:
            return await self.collect(page, **kwargs)
        except Exception as exc:
            return [{"_error": str(exc), "_collector": self.name}]
