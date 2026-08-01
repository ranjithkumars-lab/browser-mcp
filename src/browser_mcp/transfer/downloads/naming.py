"""Safe destination filename selection."""

from __future__ import annotations

from pathlib import Path

from browser_mcp.transfer.errors import DownloadError
from browser_mcp.transfer.models import CollisionStrategy


class FileNamingStrategy:
    def destination(self, directory: str | Path, filename: str, *, collision_strategy: CollisionStrategy | str = CollisionStrategy.AUTO_RENAME) -> Path:
        root = Path(directory).expanduser()
        root.mkdir(parents=True, exist_ok=True)
        # A suggested filename must never escape the configured artifact root.
        clean = Path(filename).name or "download"
        candidate = root / clean
        strategy = CollisionStrategy(collision_strategy)
        if not candidate.exists() or strategy is CollisionStrategy.OVERWRITE:
            return candidate
        if strategy is CollisionStrategy.REJECT:
            raise DownloadError(f"destination '{candidate}' already exists")
        for index in range(1, 10_000):
            renamed = root / f"{candidate.stem} ({index}){candidate.suffix}"
            if not renamed.exists():
                return renamed
        raise DownloadError(f"could not allocate a unique name for '{clean}'")
