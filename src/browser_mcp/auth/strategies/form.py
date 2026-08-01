"""Form-based login strategy."""

from __future__ import annotations

import time
from typing import Any

from browser_mcp.auth.strategies.base import BaseAuthStrategy
from browser_mcp.errors import LoginFailedError

__all__ = ["FormAuthStrategy"]


class FormAuthStrategy(BaseAuthStrategy):
    """Form login via element detection and form submission."""

    @property
    def name(self) -> str:
        return "form"

    async def execute(self, context: Any, credentials: Any) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            await context.goto(credentials.url)
            username_selector = credentials.metadata.get(
                "username_selector", 'input[name="username"], input[name="email"], #email'
            )
            password_selector = credentials.metadata.get(
                "password_selector", 'input[name="password"], #password'
            )
            submit_selector = credentials.metadata.get(
                "submit_selector", 'button[type="submit"], input[type="submit"]'
            )
            await context.fill(username_selector, credentials.username or "")
            await context.fill(password_selector, credentials.password or "")
            await context.click(submit_selector)
            await context.wait_for_load_state("networkidle")
            duration_ms = (time.perf_counter() - started) * 1000
            return {
                "success": True,
                "duration_ms": duration_ms,
                "url": context.url,
            }
        except Exception as exc:
            duration_ms = (time.perf_counter() - started) * 1000
            raise LoginFailedError(f"form login failed: {exc}") from exc
