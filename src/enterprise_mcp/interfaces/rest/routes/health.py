"""Health-check endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness and basic health status."""
    return {"status": "ok", "service": "enterprise-mcp-server"}


@router.get("/live")
async def live() -> dict[str, str]:
    """Liveness probe: the process is up."""
    return {"status": "alive"}


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    """Readiness probe: core services are ready."""
    context = getattr(request.app.state, "context", None)
    if context is None:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return JSONResponse(status_code=200, content={"status": "ready"})
