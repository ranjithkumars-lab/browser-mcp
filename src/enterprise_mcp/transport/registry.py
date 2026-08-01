"""Transport registry mapping names to implementation classes."""

from __future__ import annotations

from enterprise_mcp.transport.base import Transport
from enterprise_mcp.transport.http import StreamableHTTPTransport
from enterprise_mcp.transport.sse import SSETransport
from enterprise_mcp.transport.stdio import StdioTransport
from enterprise_mcp.utils.errors import TransportError

__all__ = ["AVAILABLE_TRANSPORTS", "get_transport_class"]

AVAILABLE_TRANSPORTS: dict[str, type[Transport]] = {
    "streamable-http": StreamableHTTPTransport,
    "sse": SSETransport,
    "stdio": StdioTransport,
}


def get_transport_class(name: str) -> type[Transport]:
    """Return the transport class registered under ``name``."""
    transport_class = AVAILABLE_TRANSPORTS.get(name)
    if transport_class is None:
        raise TransportError(
            f"unknown transport '{name}', available: {', '.join(AVAILABLE_TRANSPORTS)}"
        )
    return transport_class
