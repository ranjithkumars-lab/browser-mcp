#!/usr/bin/env python3
"""Run the server in development mode."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    """Launch the dev server with auto-reload."""
    subprocess.run(
        ["uv", "run", "enterprise-mcp", "serve", "--reload"],  # noqa: S607 - fixed command
        cwd=ROOT,
        check=False,
    )


if __name__ == "__main__":
    sys.exit(main())
