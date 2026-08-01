"""WebSocket endpoint abstraction."""

from __future__ import annotations

from typing import Any

__all__ = ["WebSocketEndpoint"]


class WebSocketEndpoint:
    """Abstract WebSocket endpoint.

    Live event streaming over WebSocket is implemented in a later phase.
    """

    async def connect(self) -> None:
        """Accept a client connection."""
        raise NotImplementedError

    async def send(self, payload: dict[str, Any]) -> None:
        """Send a JSON payload to the connected client."""
        raise NotImplementedError

    async def close(self) -> None:
        """Close the connection."""
        raise NotImplementedError
