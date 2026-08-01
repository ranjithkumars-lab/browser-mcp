from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseDownloadStrategy(ABC):
    name: str

    @abstractmethod
    async def execute(self, page: Any, **options: Any) -> dict[str, Any]:
        """Perform a download and return saved-file metadata."""
