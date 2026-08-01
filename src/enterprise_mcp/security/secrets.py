"""Secret management abstraction."""

from __future__ import annotations

import os

__all__ = ["EnvSecretStore", "SecretStore"]


class SecretStore:
    """Abstract secret resolver.

    External secret managers (Vault, cloud KMS) are integrated in later
    phases.
    """

    def get(self, key: str) -> str | None:
        """Return the secret stored under ``key``, or ``None``."""
        raise NotImplementedError


class EnvSecretStore(SecretStore):
    """Secret store backed by environment variables."""

    def __init__(self, prefix: str = "ENTERPRISE_MCP_SECRET_") -> None:
        self._prefix = prefix

    def get(self, key: str) -> str | None:
        return os.environ.get(f"{self._prefix}{key.upper()}")
