#!/usr/bin/env python3
"""Print the current package version."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from enterprise_mcp import __version__  # noqa: E402


def main() -> None:
    """Print the version."""
    print(__version__)


if __name__ == "__main__":
    main()
