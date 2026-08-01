"""Domain Pydantic models for the authentication engine."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

__all__ = [
    "AuthCredentials",
    "AuthHeaders",
    "AuthMetadata",
    "AuthSession",
    "AuthState",
    "CookieCollection",
]


class AuthCredentials(BaseModel):
    """Authentication credentials for a login attempt."""

    username: str | None = Field(default=None, description="Login username or email.")
    password: str | None = Field(default=None, description="Login password.")
    url: str = Field(description="Target URL for the login page.")
    strategy: str = Field(default="form", description="Auth strategy identifier.")
    headers: dict[str, str] = Field(default_factory=dict[str, str], description="Extra headers for the login request.")
    cookies: dict[str, str] = Field(default_factory=dict[str, str], description="Extra cookies for the login request.")
    metadata: dict[str, Any] = Field(default_factory=dict[str, Any], description="Strategy-specific extra data.")


class AuthHeaders(BaseModel):
    """Structured HTTP headers to inject into requests."""

    headers: dict[str, str] = Field(default_factory=dict, description="Header name -> value mapping.")
    strategy: str = Field(default="header", description="Header injection strategy.")


class CookieCollection(BaseModel):
    """Collection of cookies for injection."""

    cookies: list[dict[str, object]] = Field(default_factory=list, description="Playwright-style cookie dicts.")  # type: ignore[reportUnknownVariableType]
    strategy: str = Field(default="cookie", description="Cookie injection strategy.")


class AuthMetadata(BaseModel):
    """Immutable audit metadata for an authentication session."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_refreshed_at: datetime | None = None
    expires_at: datetime | None = None
    strategy: str = Field(description="Strategy that created this session.")
    context_id: str = Field(description="Browser context the session belongs to.")
    session_id: str = Field(description="Browser session the session belongs to.")


class AuthSession(BaseModel):
    """Active authentication session state for a browser context."""

    session_id: str = Field(description="Browser session id.")
    context_id: str = Field(description="Browser context id.")
    authenticated: bool = Field(default=False)
    metadata: AuthMetadata | None = None


class AuthState(BaseModel):
    """Serialised authentication state that can be persisted and rehydrated."""

    session: AuthSession
    state_id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
