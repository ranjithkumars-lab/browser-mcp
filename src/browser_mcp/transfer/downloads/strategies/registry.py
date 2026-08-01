from __future__ import annotations

from browser_mcp.transfer.downloads.strategies.base import BaseDownloadStrategy
from browser_mcp.transfer.errors import DownloadError


class DownloadStrategyRegistry:
    def __init__(self) -> None:
        self._strategies: dict[str, BaseDownloadStrategy] = {}

    def register(self, strategy: BaseDownloadStrategy) -> None:
        self._strategies[strategy.name] = strategy

    def get(self, name: str) -> BaseDownloadStrategy:
        try:
            return self._strategies[name]
        except KeyError as exc:
            raise DownloadError(f"download strategy '{name}' is not registered") from exc

    def names(self) -> list[str]:
        return list(self._strategies)
