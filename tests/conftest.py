"""Shared pytest fixtures."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from enterprise_mcp.config.loader import load_settings
from enterprise_mcp.config.models import Settings
from enterprise_mcp.foundation.app import AppContext
from enterprise_mcp.interfaces.rest.app import create_app


def pytest_configure(config: pytest.Config) -> None:
    """Point pytest's tmp base at a writable location on Windows.

    The default ``%TEMP%/pytest-of-<user>`` base can be unreadable in some
    environments, which breaks the ``tmp_path`` fixture.
    """
    if config.option.basetemp is None:
        root = Path(tempfile.gettempdir()) / "opencode" / "enterprise-mcp-pytest"
        root.mkdir(parents=True, exist_ok=True)
        config.option.basetemp = str(root)


@pytest.fixture
def settings() -> Settings:
    """Return test environment settings (isolated from user config)."""
    return load_settings(env="test")


@pytest.fixture
def context(settings: Settings) -> AppContext:
    """Return an application context bound to test settings."""
    return AppContext(settings=settings)


@pytest.fixture
def client(context: AppContext) -> TestClient:
    """Return a FastAPI test client for the application."""
    return TestClient(create_app(context))
