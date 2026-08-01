"""Task queue abstraction."""

from __future__ import annotations

from typing import Any

__all__ = ["TaskQueue"]


class TaskQueue:
    """Abstract task queue (in-memory or distributed).

    Implemented in a later phase.
    """

    async def push(self, task: Any) -> None:
        """Enqueue ``task``."""
        raise NotImplementedError

    async def pop(self) -> Any:
        """Dequeue the next task, blocking until one is available."""
        raise NotImplementedError

    async def size(self) -> int:
        """Return the number of pending tasks."""
        raise NotImplementedError
