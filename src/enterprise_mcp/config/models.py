"""Pydantic settings models for the Enterprise MCP Server."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from enterprise_mcp import __version__
from enterprise_mcp.config.defaults import DEFAULT_HOST, DEFAULT_PORT, ENV_VAR_PREFIX

__all__ = [
    "Environment",
    "LoggingSettings",
    "MetricsSettings",
    "ObservabilitySettings",
    "SecuritySettings",
    "ServerSettings",
    "Settings",
    "TracingSettings",
    "TransportSettings",
]


class Environment(StrEnum):
    """Deployment environment selector."""

    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class LoggingSettings(BaseModel):
    """Structured logging configuration."""

    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: Literal["json", "console"] = "json"
    include_timestamps: bool = True


class MetricsSettings(BaseModel):
    """Metrics backend configuration (backend implemented in a later phase)."""

    enabled: bool = False
    prefix: str = "enterprise_mcp"
    backend: str = "null"


class TracingSettings(BaseModel):
    """Tracing backend configuration (backend implemented in a later phase)."""

    enabled: bool = False
    service_name: str = "enterprise-mcp-server"
    backend: str = "null"
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)


class ObservabilitySettings(BaseModel):
    """Aggregated observability configuration."""

    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    metrics: MetricsSettings = Field(default_factory=MetricsSettings)
    tracing: TracingSettings = Field(default_factory=TracingSettings)


class TransportSettings(BaseModel):
    """Transport layer configuration."""

    default: Literal["streamable-http", "sse", "stdio"] = "streamable-http"
    host: str = DEFAULT_HOST
    port: int = Field(default=DEFAULT_PORT, ge=1, le=65535)
    streamable_http_enabled: bool = True
    sse_enabled: bool = False
    stdio_enabled: bool = False

    @model_validator(mode="after")
    def _validate_default_enabled(self) -> TransportSettings:
        enabled_map = {
            "streamable-http": self.streamable_http_enabled,
            "sse": self.sse_enabled,
            "stdio": self.stdio_enabled,
        }
        if not enabled_map[self.default]:
            raise ValueError(f"default transport '{self.default}' is disabled")
        return self


class SecuritySettings(BaseModel):
    """Security configuration (authentication implemented in a later phase)."""

    enabled: bool = False
    api_key: str | None = None
    auth_provider: str = "none"


class ServerSettings(BaseModel):
    """Top-level server identity and behaviour settings."""

    name: str = "enterprise-mcp-server"
    version: str = __version__
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    config_dir: str | None = None
    transports: TransportSettings = Field(default_factory=TransportSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    @property
    def is_production(self) -> bool:
        """Return True when running in the production environment."""
        return self.environment == Environment.PRODUCTION


class Settings(BaseSettings):
    """Root settings object loaded from defaults, YAML, and environment.

    Merge order (lowest to highest priority):

    1. Bundled ``settings/default.yaml``
    2. Environment-specific YAML (``settings/{env}.yaml``)
    3. Environment variables prefixed with ``ENTERPRISE_MCP_``
    4. Explicit programmatic overrides
    """

    model_config = SettingsConfigDict(
        env_prefix=ENV_VAR_PREFIX,
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",
    )

    server: ServerSettings = Field(default_factory=ServerSettings)
