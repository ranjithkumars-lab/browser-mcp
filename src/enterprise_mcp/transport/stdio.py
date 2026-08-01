"""Standard input/output transport.

Local-development transport over stdin/stdout. Implemented in a later phase.
"""

from __future__ import annotations

from enterprise_mcp.transport.base import Transport

__all__ = ["StdioTransport"]


class StdioTransport(Transport):
    """stdio transport stub."""

    name = "stdio"

    async def start(self) -> None:
        raise NotImplementedError("stdio transport is implemented in a later phase")

    async def stop(self) -> None:
        raise NotImplementedError("stdio transport is implemented in a later phase")
