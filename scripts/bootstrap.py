#!/usr/bin/env python3
"""Bootstrap the development environment."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(command: list[str]) -> None:
    print(f"+ {' '.join(command)}")
    subprocess.run(command, cwd=ROOT, check=True)  # noqa: S603 - fixed command list


def main() -> None:
    """Sync dependencies and install git hooks."""
    run(["uv", "sync", "--all-extras"])
    run(["uv", "run", "pre-commit", "install"])
    print("\nEnvironment ready. Run `uv run enterprise-mcp doctor` to verify.")


if __name__ == "__main__":
    sys.exit(main())
