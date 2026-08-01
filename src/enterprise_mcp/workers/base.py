"""Worker base class."""

from __future__ import annotations

__all__ = ["Worker"]


class Worker:
    """Abstract worker consuming tasks from a queue.

    Implemented in a later phase.
    """

    async def run(self) -> None:
        """Consume tasks until stopped."""
        raise NotImplementedError

    async def stop(self) -> None:
        """Gracefully stop consuming."""
        raise NotImplementedError
