"""Authentication abstraction."""

from __future__ import annotations

from typing import Any

__all__ = ["APIKeyAuthenticator", "Authenticator"]


class Authenticator:
    """Abstract authentication provider.

    JWT, OAuth, and session backends are implemented in later phases.
    """

    async def authenticate(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        """Validate ``credentials`` and return a principal, or ``None``."""
        raise NotImplementedError


class APIKeyAuthenticator(Authenticator):
    """API-key authenticator backed by a configured key set."""

    def __init__(self, api_keys: set[str]) -> None:
        self._api_keys = api_keys

    async def authenticate(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        api_key = credentials.get("api_key")
        if api_key in self._api_keys:
            return {"subject": "api-key", "api_key_hash": hash(api_key)}
        return None
