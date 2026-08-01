"""Transport abstraction."""

from __future__ import annotations

from typing import Any

__all__ = ["Transport"]


class Transport:
    """Base interface for all MCP transports.

    Implementations must start accepting traffic on :meth:`start` and release
    all resources on :meth:`stop`. Business logic never depends on a concrete
    transport; it interacts only with this interface.
    """

    name: str = "base"

    async def start(self) -> None:
        """Start accepting and processing requests."""
        raise NotImplementedError

    async def stop(self) -> None:
        """Stop accepting requests and release resources."""
        raise NotImplementedError

    @property
    def is_running(self) -> bool:
        """Return whether the transport is currently running."""
        return False

    async def handle(self, request: Any) -> Any:
        """Process a single request (implementation-specific)."""
        raise NotImplementedError
