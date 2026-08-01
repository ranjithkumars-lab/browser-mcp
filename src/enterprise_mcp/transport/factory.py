"""Transport factory."""

from __future__ import annotations

from enterprise_mcp.transport.base import Transport
from enterprise_mcp.transport.registry import get_transport_class

__all__ = ["create_transport"]


def create_transport(name: str) -> Transport:
    """Instantiate the transport registered under ``name``."""
    transport_class = get_transport_class(name)
    return transport_class()
