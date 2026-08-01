"""Security subsystem scaffolds.

Authentication, RBAC, secrets management, and audit logging are implemented
in later phases. Phase 0 defines the interfaces and lightweight defaults.
"""

from enterprise_mcp.security.audit import AuditLogger
from enterprise_mcp.security.auth import APIKeyAuthenticator, Authenticator
from enterprise_mcp.security.rbac import Permission, RBACPolicy, Role
from enterprise_mcp.security.secrets import EnvSecretStore, SecretStore

__all__ = [
    "APIKeyAuthenticator",
    "AuditLogger",
    "Authenticator",
    "EnvSecretStore",
    "Permission",
    "RBACPolicy",
    "Role",
    "SecretStore",
]
