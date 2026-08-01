"""``doctor`` command: environment diagnostics."""

from __future__ import annotations

import socket
import sys
from dataclasses import dataclass

import typer

from enterprise_mcp.config.loader import load_settings
from enterprise_mcp.transport.registry import AVAILABLE_TRANSPORTS
from enterprise_mcp.utils.version import get_version

__all__ = ["doctor"]

_RESULTS = ("ok", "warn", "fail")


@dataclass
class Check:
    """A single diagnostic check result."""

    name: str
    status: str
    detail: str = ""


def _check_python_version() -> Check:
    ok = sys.version_info >= (3, 13)
    return Check(
        name="python-version",
        status="ok" if ok else "warn",
        detail=f"{sys.version.split()[0]} (>=3.13 required)",
    )


def _check_config() -> Check:
    try:
        settings = load_settings()
        return Check(name="config", status="ok", detail=settings.server.environment.value)
    except Exception as exc:
        return Check(name="config", status="fail", detail=str(exc))


def _check_port(port: int, host: str = "0.0.0.0") -> Check:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            sock.bind((host, port))
        return Check(name="port", status="ok", detail=f"{host}:{port} is available")
    except OSError as exc:
        return Check(name="port", status="warn", detail=f"{host}:{port}: {exc}")


def _check_imports() -> Check:
    missing: list[str] = []
    for module in ("fastapi", "uvicorn", "structlog", "mcp", "pydantic"):
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    if missing:
        return Check(name="imports", status="fail", detail=", ".join(missing))
    return Check(name="imports", status="ok", detail="all core modules importable")


def doctor() -> None:
    """Run environment and configuration diagnostics."""
    typer.echo(f"enterprise-mcp doctor ({get_version()})\n")

    settings = load_settings()
    checks = [
        _check_python_version(),
        _check_config(),
        _check_imports(),
        _check_port(settings.server.transports.port, settings.server.transports.host),
    ]

    failed = 0
    for check in checks:
        if check.status == "fail":
            failed += 1
        typer.echo(f"[{check.status.upper():>4}] {check.name}: {check.detail}")

    typer.echo(f"\ntransports available: {', '.join(sorted(AVAILABLE_TRANSPORTS))}")
    if failed:
        raise typer.Exit(code=1)
