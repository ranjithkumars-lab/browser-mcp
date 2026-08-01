"""Health-check endpoints."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


async def _providers_payload(request: Request) -> dict[str, Any]:
    context = getattr(request.app.state, "context", None)
    providers = getattr(context, "health_providers", None)
    if not providers:
        return {}
    payload: dict[str, Any] = {}
    for name, provider in providers.items():
        try:
            result = provider()
            if isinstance(result, Awaitable):
                result = await result
            payload[name] = result
        except Exception as exc:
            payload[name] = {"error": str(exc)}
    return payload


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    """Liveness and basic health status (including registered providers)."""
    return {
        "status": "ok",
        "service": "enterprise-mcp-server",
        "checks": await _providers_payload(request),
    }


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
