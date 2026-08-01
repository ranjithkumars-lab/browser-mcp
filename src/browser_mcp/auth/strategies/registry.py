"""Dynamic strategy lookup registry."""

from __future__ import annotations

from browser_mcp.errors import UnsupportedAuthStrategyError
from browser_mcp.auth.strategies.base import BaseAuthStrategy

__all__ = ["AuthStrategyRegistry"]


class AuthStrategyRegistry:
    """Dynamic lookup for registered auth strategies."""

    def __init__(self) -> None:
        self._strategies: dict[str, BaseAuthStrategy] = {}

    def register(self, strategy: BaseAuthStrategy) -> None:
        self._strategies[strategy.name] = strategy

    def get(self, name: str) -> BaseAuthStrategy:
        if name == "oauth":
            raise UnsupportedAuthStrategyError(
                "OAuth strategy is reserved; use a dedicated OAuth provider."
            )
        strategy = self._strategies.get(name)
        if strategy is None:
            raise UnsupportedAuthStrategyError(
                f"auth strategy '{name}' is not registered"
            )
        return strategy

    def names(self) -> list[str]:
        return list(self._strategies)
