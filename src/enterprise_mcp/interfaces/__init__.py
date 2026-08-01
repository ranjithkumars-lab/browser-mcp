"""External interfaces: REST, WebSocket, and internal APIs."""

from enterprise_mcp.interfaces.rest.app import create_app

__all__ = ["create_app"]
