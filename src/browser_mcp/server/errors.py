from __future__ import annotations

from typing import Any

from browser_mcp.errors import (
    AuthenticationError,
    BrowserError,
    ElementNotFoundError,
    NavigationError,
)
from browser_mcp.plugins.errors import PluginPermissionDeniedError, PluginSchemaValidationError
from browser_mcp.transfer.errors import TransferError


def translate_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, (ElementNotFoundError, PluginSchemaValidationError)):
        code = -32602
    elif isinstance(exc, NavigationError):
        code = -32600
    elif isinstance(exc, PluginPermissionDeniedError):
        code = -32000
    elif isinstance(exc, AuthenticationError):
        code = -32001
    elif isinstance(exc, (TransferError, BrowserError)):
        code = -32603
    else:
        code = -32603
    return {"code": code, "message": str(exc) or exc.__class__.__name__}
