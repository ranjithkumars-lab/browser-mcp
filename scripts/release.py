#!/usr/bin/env python3
"""Validate and build a release."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(command: list[str]) -> None:
    print(f"+ {' '.join(command)}")
    subprocess.run(command, cwd=ROOT, check=True)  # noqa: S603 - fixed command list


def main() -> None:
    """Run the full pre-release validation pipeline."""
    run(["uv", "sync", "--all-extras"])
    run(["uv", "run", "ruff", "check", "."])
    run(["uv", "run", "ruff", "format", "--check", "."])
    run(["uv", "run", "pyright"])
    run(["uv", "run", "pytest"])
    run(["uv", "build"])
    print("\nRelease artifacts ready in dist/.")


if __name__ == "__main__":
    sys.exit(main())
