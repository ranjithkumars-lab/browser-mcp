from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseUploadStrategy(ABC):
    name: str

    @abstractmethod
    async def execute(
        self, page: Any, *, selector: str, files: list[str], frame_id: str | None = None
    ) -> None:
        """Deliver local files to an upload target."""
