"""Unit tests for the AuthToolkit (tool registration)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from browser_mcp.auth.tools import TOOL_NAMESPACE, AuthToolkit

pytestmark = pytest.mark.unit


def _toolkit() -> AuthToolkit:
    return AuthToolkit(MagicMock(), MagicMock(), MagicMock())


def test_tool_namespace() -> None:
    assert TOOL_NAMESPACE == "browser.auth"


def test_register_calls_registry_with_aliases() -> None:
    registry = MagicMock()
    registry.register = MagicMock()
    _toolkit().register(registry)
    assert registry.register.call_count == 8
    names = [
        call.kwargs.get("metadata").name
        for call in registry.register.call_args_list
        if call.kwargs.get("metadata") is not None
    ]
    assert "browser.auth_login" in names
    assert "browser.auth_set_headers" in names
