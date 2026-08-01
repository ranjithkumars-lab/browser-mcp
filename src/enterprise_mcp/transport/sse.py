"""Server-Sent Events (SSE) transport.

Legacy transport for compatibility. Implemented in a later phase.
"""

from __future__ import annotations

from enterprise_mcp.transport.base import Transport

__all__ = ["SSETransport"]


class SSETransport(Transport):
    """SSE transport stub."""

    name = "sse"

    async def start(self) -> None:
        raise NotImplementedError("SSE transport is implemented in a later phase")

    async def stop(self) -> None:
        raise NotImplementedError("SSE transport is implemented in a later phase")
