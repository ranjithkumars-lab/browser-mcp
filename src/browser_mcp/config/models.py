"""Pydantic settings models for the Browser MCP server."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from browser_mcp.config.defaults import ENV_VAR_PREFIX

__all__ = [
    "AuthConfig",
    "TransferConfig",
    "BrowserConfig",
    "BrowserEngine",
    "BrowserProfile",
    "BrowserSettings",
    "NavigationConfig",
    "NavigationStrategy",
    "PoolConfig",
    "ProfilesConfig",
    "TimeoutConfig",
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


class NavigationStrategy(StrEnum):
    """Vendor-neutral navigation wait strategies.

    Maps onto Playwright's ``wait_until`` values:

    - ``fast``: wait for ``domcontentloaded``
    - ``normal``: wait for ``load``
    - ``complete``: wait for ``networkidle``
    """

    FAST = "fast"
    NORMAL = "normal"
    COMPLETE = "complete"

    def wait_until(self) -> Literal["domcontentloaded", "load", "networkidle"]:
        """Return the underlying ``wait_until`` value for this strategy."""
        if self is NavigationStrategy.FAST:
            return "domcontentloaded"
        if self is NavigationStrategy.COMPLETE:
            return "networkidle"
        return "load"


class ViewportConfig(BaseModel):
    """Default browser viewport size."""

    width: int = Field(default=1280, ge=1)
    height: int = Field(default=720, ge=1)


class AuthConfig(BaseModel):
    """Authentication engine configuration."""

    storage_directory: str = Field(
        default="~/.browser-mcp/auth_states",
        description="Root directory for persisted auth states.",
    )
    allow_plaintext: bool = Field(
        default=False,
        description="Allow unencrypted auth state files in development.",
    )


class TransferConfig(BaseModel):
    """Download/upload engine limits and storage behaviour."""

    download_directory: str = Field(default="~/.browser-mcp/artifacts")
    max_file_size_bytes: int = Field(default=500 * 1024 * 1024, ge=1)
    allowed_extensions: list[str] = Field(default_factory=list[str])
    allowed_mime_types: list[str] = Field(default_factory=list[str])
    checksum_algorithm: str = Field(default="sha256")
    collision_strategy: str = Field(default="auto_rename")
    cleanup_policy: str = Field(default="on_failure")


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


class TimeoutConfig(BaseModel):
    """Global browser operation timeouts (milliseconds)."""

    default_timeout_ms: int = Field(
        default=30_000,
        ge=1,
        description="Default timeout applied when a caller does not specify one.",
    )
    navigation_timeout_ms: int = Field(
        default=30_000,
        ge=1,
        description="Timeout for goto/reload/back/forward operations.",
    )
    interaction_timeout_ms: int = Field(
        default=10_000,
        ge=1,
        description="Timeout for clicks, hovers, scrolls and other interactions.",
    )
    wait_timeout_ms: int = Field(
        default=10_000,
        ge=1,
        description="Timeout for wait_* operations that do not override it.",
    )


class NavigationConfig(BaseModel):
    """Enterprise navigation boundaries and defaults.

    ``blocked_extensions``, ``allowed_ports`` and ``max_navigation_depth`` are
    reserved for future enforcement; they are parsed and validated now but not
    yet applied by the navigation policy.
    """

    allowed_domains: list[str] = Field(
        default_factory=list[str],
        description="Domains navigation is restricted to; empty allows all.",
    )
    blocked_domains: list[str] = Field(
        default_factory=list[str],
        description="Domains navigation is never allowed to visit.",
    )
    allow_redirects: bool = Field(
        default=True,
        description="Whether server-side redirects are followed.",
    )
    max_redirects: int = Field(
        default=10,
        ge=0,
        description="Maximum redirect hops permitted during a navigation.",
    )
    allowed_schemes: list[str] = Field(
        default_factory=lambda: ["http", "https", "file"],
        description="URL schemes navigation may use.",
    )
    default_strategy: NavigationStrategy = NavigationStrategy.NORMAL
    blocked_extensions: list[str] = Field(
        default_factory=list[str],
        description="Reserved: file extensions navigation is not allowed to load.",
    )
    allowed_ports: list[int] = Field(
        default_factory=list[int],
        description="Reserved: ports navigation is restricted to; empty allows all.",
    )
    max_navigation_depth: int | None = Field(
        default=None,
        ge=1,
        description="Reserved: maximum navigation depth from the session root.",
    )


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
    navigation: NavigationConfig = Field(default_factory=NavigationConfig)
    timeouts: TimeoutConfig = Field(default_factory=TimeoutConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    transfer: TransferConfig = Field(default_factory=TransferConfig)
