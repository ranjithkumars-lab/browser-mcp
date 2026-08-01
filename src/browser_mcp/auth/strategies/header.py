"""Dynamic HTTP header injection strategy."""

from __future__ import annotations

from typing import Any

from browser_mcp.auth.strategies.base import BaseAuthStrategy

__all__ = ["HeaderAuthStrategy"]


class HeaderAuthStrategy(BaseAuthStrategy):
    """Dynamic HTTP header injection (JWT, Bearer, API Keys)."""

    @property
    def name(self) -> str:
        return "header"

    async def execute(self, context: Any, credentials: Any) -> dict[str, Any]:
        headers = credentials.headers
        await context.set_extra_http_headers(headers)
        return {"success": True, "headers_injected": list(headers.keys())}
