"""Direct cookie injection strategy."""

from __future__ import annotations

from typing import Any

from browser_mcp.auth.strategies.base import BaseAuthStrategy

__all__ = ["CookieAuthStrategy"]


class CookieAuthStrategy(BaseAuthStrategy):
    """Direct cookie injection into a browser context."""

    @property
    def name(self) -> str:
        return "cookie"

    async def execute(self, context: Any, credentials: Any) -> dict[str, Any]:
        raw = credentials.cookies
        cookies: list[dict[str, str]]
        if isinstance(raw, dict):
            url = getattr(credentials, "url", "") or ""
            cookies = []
            for k, v in raw.items():  # type: ignore[reportUnknownVariableType]
                cookies.append({"name": str(k), "value": str(v), "url": url or "http://127.0.0.1"})  # type: ignore[reportUnknownArgumentType]
        else:
            cookies = list(raw)
        await context.add_cookies(cookies)  # type: ignore[arg-type]
        return {"success": True, "cookies_injected": len(cookies)}
