"""Transport layer.

Transport implementations are added in a later phase. Phase 0 defines the
abstraction, a registry, and a factory so that business logic remains
transport-independent.
"""

from enterprise_mcp.transport.base import Transport
from enterprise_mcp.transport.factory import create_transport
from enterprise_mcp.transport.registry import AVAILABLE_TRANSPORTS, get_transport_class

__all__ = [
    "AVAILABLE_TRANSPORTS",
    "Transport",
    "create_transport",
    "get_transport_class",
]
