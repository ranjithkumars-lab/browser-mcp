"""Version and build-info endpoint."""

from __future__ import annotations

import sys

from fastapi import APIRouter

from enterprise_mcp import __version__
from enterprise_mcp.transport.registry import AVAILABLE_TRANSPORTS
from enterprise_mcp.utils.version import get_version

router = APIRouter(tags=["system"])


@router.get("/version")
async def version() -> dict[str, object]:
    """Return build information and supported transports."""
    return {
        "name": "enterprise-mcp-server",
        "version": get_version(),
        "package_version": __version__,
        "python": sys.version.split()[0],
        "transports": sorted(AVAILABLE_TRANSPORTS),
    }
