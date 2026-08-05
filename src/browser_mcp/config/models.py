"""Pydantic settings models for the Browser MCP server."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from browser_mcp.config.defaults import ENV_VAR_PREFIX

__all__ = [
    "ApiConfig",
    "AuthConfig",
    "BrowserConfig",
    "BrowserEngine",
    "BrowserProfile",
    "BrowserSettings",
    "EventsConfig",
    "NavigationConfig",
    "NavigationStrategy",
    "OllamaConfig",
    "PluginsConfig",
    "PoolConfig",
    "ProfilesConfig",
    "ScreenshotConfig",
    "ServerConfig",
    "TimeoutConfig",
    "TransferConfig",
    "UiConfig",
    "ViewportConfig",
    "ChatConfig",
    "ArtifactConfig",
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


class EventsConfig(BaseModel):
    """Browser event history, dispatch, and streaming configuration."""

    max_history_size: int = Field(default=1000, ge=1)
    max_queue_size: int = Field(default=10_000, ge=1)
    subscriber_timeout_seconds: float = Field(default=5.0, gt=0)
    worker_count: int = Field(default=4, ge=1)
    drop_policy: str = Field(default="drop_oldest")
    enable_metrics: bool = True
    enable_streaming: bool = True


class PluginsConfig(BaseModel):
    plugin_directory: str = "~/.browser-mcp/plugins"
    auto_discover: bool = True
    auto_reload: bool = True
    marketplace_enabled: bool = False
    verify_signatures: bool = False
    allow_unsigned: bool = True
    max_execution_time_seconds: float = Field(default=30.0, gt=0)
    max_memory_mb: int = Field(default=256, ge=1)


class ScreenshotConfig(BaseModel):
    """Screenshot capture settings."""

    directory: str = Field(
        default="~/.browser-mcp/screenshots",
        description="Directory where captured screenshots are stored.",
    )
    default_format: str = Field(
        default="png",
        description="Default image format: 'png' or 'jpeg'.",
    )
    default_full_page: bool = Field(
        default=False,
        description="Default value for the full-page screenshot flag.",
    )
    default_quality: int | None = Field(
        default=None,
        ge=1,
        le=100,
        description="Default JPEG quality (1-100).",
    )


class ServerConfig(BaseModel):
    default_transport: str = "stdio"
    protocol_version: str = "2025-06"
    host: str = "127.0.0.1"
    port: int = Field(default=0, ge=0, le=65535)
    request_timeout: float = Field(default=30.0, gt=0)
    max_connections: int = Field(default=100, ge=1)
    stream_buffer_size: int = Field(default=1000, ge=1)
    enable_notifications: bool = True
    enable_resources: bool = False
    enable_prompts: bool = False


class ApiConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = Field(default=0, ge=0, le=65535)
    api_key: str | None = None
    request_timeout: float = Field(default=30, gt=0)
    enable_docs: bool = True
    enable_redoc: bool = False
    enable_health: bool = True
    enable_metrics: bool = True
    job_retention_minutes: int = Field(default=60, ge=1)
    max_jobs: int = Field(default=1000, ge=1)
    default_sync_timeout: float = Field(default=5, gt=0)


class UiConfig(BaseModel):
    static_directory: str = "ui/dist"
    websocket_path: str = "/api/v1/dashboard/ws"
    reconnect_delay_ms: int = Field(default=1000, ge=100)
    event_buffer_size: int = Field(default=1000, ge=1)


class OllamaConfig(BaseModel):
    """Ollama chat agent configuration."""

    host: str = Field(
        default="http://10.0.0.170:11444",
        description="Ollama HTTP endpoint used by the chat agent.",
    )
    model: str = Field(default="gpt-oss:20b", description="Default chat model name.")
    timeout_seconds: float = Field(default=300.0, gt=0)
    keep_alive: str = Field(
        default="30m",
        description=(
            "How long Ollama keeps the model resident after each request "
            "(e.g. 5m, 30m, -1 for indefinite). Prevents cold-load stalls."
        ),
    )
    max_tool_steps: int = Field(default=16, ge=1, le=64)
    context_tokens: int | None = Field(
        default=None,
        ge=512,
        description=(
            "Ollama num_ctx. Leave unset to use the model's already-loaded "
            "context (avoids an Ollama reload, which can hang on large models "
            "hosted on a remote server)."
        ),
    )
    temperature: float = Field(default=0.0, ge=0, le=2)


class ChatConfig(BaseModel):
    """Chat UI and Response Pipeline configuration."""
    
    response_style: str = Field(default="conversational")
    compact_responses: bool = Field(default=True)
    max_history_turns: int = Field(default=20, ge=1)
    artifact_preview: bool = Field(default=True)


class ArtifactConfig(BaseModel):
    """Artifact storage and lifecycle configuration."""
    
    retention_hours: int = Field(default=24, ge=1)
    cleanup_policy: str = Field(default="on_expiration")
    max_preview_size_mb: int = Field(default=5, ge=1)


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
    screenshot: ScreenshotConfig = Field(default_factory=ScreenshotConfig)
    events: EventsConfig = Field(default_factory=EventsConfig)
    plugins: PluginsConfig = Field(default_factory=PluginsConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    ui: UiConfig = Field(default_factory=UiConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    chat: ChatConfig = Field(default_factory=ChatConfig)
    artifacts: ArtifactConfig = Field(default_factory=ArtifactConfig)
