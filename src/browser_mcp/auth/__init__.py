"""Authentication Engine package."""

from __future__ import annotations

from browser_mcp.auth.events import AuthEvent, emit_auth_expired, emit_auth_failed, emit_auth_headers_updated, emit_auth_started, emit_auth_state_loaded, emit_auth_state_saved, emit_auth_success
from browser_mcp.auth.models import AuthCredentials, AuthHeaders, AuthMetadata, AuthSession, AuthState, CookieCollection
from browser_mcp.auth.provider import AuthProvider, PlaywrightAuthProvider
from browser_mcp.auth.storage.manager import AuthStorageManager
from browser_mcp.auth.storage.serializer import StateSerializer
from browser_mcp.auth.storage.encryption import AuthEncryptionEngine
from browser_mcp.auth.storage.ttl import TTLValidator
from browser_mcp.auth.strategies.base import BaseAuthStrategy
from browser_mcp.auth.strategies.registry import AuthStrategyRegistry
from browser_mcp.auth.strategies.cookie import CookieAuthStrategy
from browser_mcp.auth.strategies.form import FormAuthStrategy
from browser_mcp.auth.strategies.header import HeaderAuthStrategy
from browser_mcp.auth.manager import AuthManager
from browser_mcp.auth.tools import AuthToolkit
from browser_mcp.errors import (
    AuthenticationError,
    AuthError,
    LoginFailedError,
    SessionExpiredError,
    StateLoadError,
    StateSaveError,
    UnsupportedAuthStrategyError,
)

__all__ = [
    "AuthCredentials",
    "AuthHeaders",
    "AuthMetadata",
    "AuthSession",
    "AuthState",
    "AuthenticationError",
    "AuthError",
    "AuthEvent",
    "AuthManager",
    "AuthProvider",
    "AuthStorageManager",
    "AuthStrategyRegistry",
    "AuthToolkit",
    "AuthEncryptionEngine",
    "BaseAuthStrategy",
    "CookieAuthStrategy",
    "CookieCollection",
    "FormAuthStrategy",
    "HeaderAuthStrategy",
    "LoginFailedError",
    "PlaywrightAuthProvider",
    "SessionExpiredError",
    "StateLoadError",
    "StateSaveError",
    "StateSerializer",
    "TTLValidator",
    "UnsupportedAuthStrategyError",
    "emit_auth_expired",
    "emit_auth_failed",
    "emit_auth_headers_updated",
    "emit_auth_started",
    "emit_auth_state_loaded",
    "emit_auth_state_saved",
    "emit_auth_success",
]
