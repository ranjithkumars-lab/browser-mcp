"""Pydantic settings models for the Browser MCP server."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from browser_mcp.config.defaults import ENV_VAR_PREFIX

__all__ = [
    "BrowserConfig",
    "BrowserEngine",
    "BrowserProfile",
    "BrowserSettings",
    "PoolConfig",
    "ProfilesConfig",
    "ViewportConfig",
]


class BrowserEngine(StrEnum):
    """Supported browser engines."""

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class BrowserProfile(StrEnum):
    """Supported browser profile types."""

    TEMPORARY = "temporary"
    PERSISTENT = "persistent"
    INCOGNITO = "incognito"


class ViewportConfig(BaseModel):
    """Default browser viewport size."""

    width: int = Field(default=1280, ge=1)
    height: int = Field(default=720, ge=1)


class BrowserConfig(BaseModel):
    """Per-browser launch options."""

    engine: BrowserEngine = BrowserEngine.CHROMIUM
    headless: bool = True
    slow_mo: int = Field(default=0, ge=0)
    viewport: ViewportConfig = Field(default_factory=ViewportConfig)
    locale: str | None = None
    timezone: str | None = None
    downloads_dir: str | None = None
    user_agent: str | None = None
    ignore_https_errors: bool = False


class PoolConfig(BaseModel):
    """Browser pool capacity limits."""

    max_browsers: int = Field(default=10, ge=1, description="Maximum live browsers.")
    max_contexts_per_browser: int = Field(default=10, ge=1)
    max_pages_per_context: int = Field(default=50, ge=1)


class ProfilesConfig(BaseModel):
    """Profile storage and defaults."""

    directory: str = Field(
        default="~/.browser-mcp/profiles",
        description="Root directory for persistent profiles.",
    )
    default_profile: BrowserProfile = BrowserProfile.TEMPORARY
    default_persistent: bool = False


class BrowserSettings(BaseSettings):
    """Root browser settings.

    Merge order (lowest to highest priority):

    1. Bundled ``settings/default.yaml``
    2. Environment-specific YAML (``settings/{env}.yaml``)
    3. Environment variables prefixed with ``BROWSER_MCP_``
    4. Explicit programmatic overrides
    """

    model_config = SettingsConfigDict(
        env_prefix=ENV_VAR_PREFIX,
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",
    )

    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    pool: PoolConfig = Field(default_factory=PoolConfig)
    profiles: ProfilesConfig = Field(default_factory=ProfilesConfig)
