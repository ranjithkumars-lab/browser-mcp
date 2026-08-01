"""Validate cookie expiry and session TTL."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from browser_mcp.errors import SessionExpiredError

__all__ = ["TTLValidator"]


class TTLValidator:
    """Check cookie ``expires`` attributes and session expiration."""

    def is_cookie_valid(self, cookie: dict[str, Any]) -> bool:
        expires = cookie.get("expires")
        if expires is None:
            return True
        try:
            expiry = datetime.fromisoformat(str(expires).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return True
        return expiry > datetime.now(UTC)

    def validate_session(self, metadata: Any) -> None:
        if metadata is None:
            return
        expires_at = metadata.expires_at
        if expires_at is None:
            return
        if expires_at <= datetime.now(UTC):
            raise SessionExpiredError(
                f"auth session expired at {expires_at.isoformat()}"
            )
