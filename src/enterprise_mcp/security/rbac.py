"""Role-based access control scaffolding."""

from __future__ import annotations

from enum import StrEnum

__all__ = ["Permission", "RBACPolicy", "Role"]


class Permission(StrEnum):
    """Named permissions granted to roles."""

    TOOLS_READ = "tools:read"
    TOOLS_EXECUTE = "tools:execute"
    SYSTEM_READ = "system:read"
    ADMIN = "admin"


class Role(StrEnum):
    """Built-in roles."""

    GUEST = "guest"
    USER = "user"
    OPERATOR = "operator"
    ADMIN = "admin"


_ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.GUEST: {Permission.SYSTEM_READ},
    Role.USER: {Permission.SYSTEM_READ, Permission.TOOLS_READ, Permission.TOOLS_EXECUTE},
    Role.OPERATOR: {Permission.SYSTEM_READ, Permission.TOOLS_READ, Permission.TOOLS_EXECUTE},
    Role.ADMIN: set(Permission),
}


class RBACPolicy:
    """Assigns and checks permissions against roles."""

    def __init__(self, role_permissions: dict[Role, set[Permission]] | None = None) -> None:
        self._role_permissions = role_permissions or _ROLE_PERMISSIONS

    def grant(self, role: Role, permission: Permission) -> None:
        """Grant ``permission`` to ``role``."""
        self._role_permissions.setdefault(role, set()).add(permission)

    def can(self, role: Role, permission: Permission) -> bool:
        """Return whether ``role`` holds ``permission``."""
        return permission in self._role_permissions.get(role, set())
