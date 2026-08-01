from __future__ import annotations

from browser_mcp.transfer.errors import UploadError
from browser_mcp.transfer.uploads.strategies.base import BaseUploadStrategy


class UploadStrategyRegistry:
    def __init__(self) -> None:
        self._strategies: dict[str, BaseUploadStrategy] = {}

    def register(self, strategy: BaseUploadStrategy) -> None:
        self._strategies[strategy.name] = strategy

    def get(self, name: str) -> BaseUploadStrategy:
        try:
            return self._strategies[name]
        except KeyError as exc:
            raise UploadError(f"upload strategy '{name}' is not registered") from exc

    def names(self) -> list[str]:
        return list(self._strategies)
