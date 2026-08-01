"""Convenience holder for transfer strategy registries."""

from dataclasses import dataclass

from browser_mcp.transfer.downloads.strategies.registry import DownloadStrategyRegistry
from browser_mcp.transfer.uploads.strategies.registry import UploadStrategyRegistry


@dataclass(slots=True)
class TransferRegistry:
    downloads: DownloadStrategyRegistry
    uploads: UploadStrategyRegistry
