"""Authentication strategies package."""

from __future__ import annotations

from browser_mcp.auth.strategies.base import BaseAuthStrategy
from browser_mcp.auth.strategies.cookie import CookieAuthStrategy
from browser_mcp.auth.strategies.form import FormAuthStrategy
from browser_mcp.auth.strategies.header import HeaderAuthStrategy
from browser_mcp.auth.strategies.registry import AuthStrategyRegistry

__all__ = [
    "AuthStrategyRegistry",
    "BaseAuthStrategy",
    "CookieAuthStrategy",
    "FormAuthStrategy",
    "HeaderAuthStrategy",
]
