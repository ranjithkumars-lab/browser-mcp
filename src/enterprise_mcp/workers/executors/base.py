"""Executor abstraction."""

from __future__ import annotations

from typing import Any

__all__ = ["Executor"]


class Executor:
    """Abstract task executor.

    Implemented in a later phase.
    """

    async def execute(self, task: Any) -> Any:
        """Execute ``task`` and return its result."""
        raise NotImplementedError

    async def cancel(self, task_id: str) -> None:
        """Cancel a running task."""
        raise NotImplementedError
