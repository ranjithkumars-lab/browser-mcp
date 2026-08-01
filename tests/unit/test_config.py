"""Tests for the configuration loader and models."""

from __future__ import annotations

from pathlib import Path

import pytest

from enterprise_mcp.config.defaults import ENV_VAR_PREFIX
from enterprise_mcp.config.loader import load_settings
from enterprise_mcp.config.models import Environment, Settings
from enterprise_mcp.config.paths import bundled_defaults_path
from enterprise_mcp.utils.errors import ConfigError

pytestmark = pytest.mark.unit


def test_defaults_load_successfully() -> None:
    settings = load_settings(env="test")
    assert isinstance(settings, Settings)
    assert settings.server.environment == Environment.TEST
    assert settings.server.transports.default == "streamable-http"


def test_bundled_defaults_file_exists() -> None:
    assert bundled_defaults_path().exists()


def test_environment_selection() -> None:
    settings = load_settings(env="production")
    assert settings.server.environment == Environment.PRODUCTION
    assert settings.server.is_production
    assert not settings.server.debug


def test_override_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(f"{ENV_VAR_PREFIX}SERVER__TRANSPORTS__PORT", "9000")
    settings = load_settings(env="test")
    assert settings.server.transports.port == 9000


def test_programmatic_overrides_win() -> None:
    settings = load_settings(env="test", overrides={"server": {"transports": {"port": 7000}}})
    assert settings.server.transports.port == 7000


def test_invalid_yaml_raises_config_error(tmp_path: Path) -> None:
    (tmp_path / "default.yaml").write_text("server: [unclosed", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_settings(env="test", settings_dir=tmp_path)


def test_missing_environment_yaml_uses_defaults(tmp_path: Path) -> None:
    (tmp_path / "default.yaml").write_text("server:\n  debug: false", encoding="utf-8")
    settings = load_settings(env="production", settings_dir=tmp_path)
    assert settings.server.debug is False
