"""REST route modules."""

from enterprise_mcp.interfaces.rest.routes.health import router as health_router
from enterprise_mcp.interfaces.rest.routes.version import router as version_router

__all__ = ["health_router", "version_router"]
