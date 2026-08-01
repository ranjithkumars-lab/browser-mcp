"""Shared configuration constants."""

APP_NAME = "enterprise-mcp-server"
ENV_VAR_PREFIX = "ENTERPRISE_MCP_"
DEFAULT_ENV = "development"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
SUPPORTED_TRANSPORTS = ("streamable-http", "sse", "stdio")
SUPPORTED_ENVIRONMENTS = ("development", "test", "production")

__all__ = [
    "APP_NAME",
    "DEFAULT_ENV",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "ENV_VAR_PREFIX",
    "SUPPORTED_ENVIRONMENTS",
    "SUPPORTED_TRANSPORTS",
]
