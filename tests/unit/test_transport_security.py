"""Tests for RBAC, secrets, and transports."""

from __future__ import annotations

import pytest

from enterprise_mcp.security.rbac import Permission, RBACPolicy, Role
from enterprise_mcp.security.secrets import EnvSecretStore
from enterprise_mcp.transport.factory import create_transport
from enterprise_mcp.transport.registry import AVAILABLE_TRANSPORTS, get_transport_class
from enterprise_mcp.utils.errors import TransportError

pytestmark = pytest.mark.unit


class TestRBAC:
    def test_admin_has_all_permissions(self) -> None:
        policy = RBACPolicy()
        assert policy.can(Role.ADMIN, Permission.TOOLS_EXECUTE)
        assert policy.can(Role.ADMIN, Permission.ADMIN)

    def test_guest_limited(self) -> None:
        policy = RBACPolicy()
        assert policy.can(Role.GUEST, Permission.SYSTEM_READ)
        assert not policy.can(Role.GUEST, Permission.TOOLS_EXECUTE)

    def test_grant(self) -> None:
        policy = RBACPolicy()
        policy.grant(Role.GUEST, Permission.TOOLS_READ)
        assert policy.can(Role.GUEST, Permission.TOOLS_READ)


def test_env_secret_store(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENTERPRISE_MCP_SECRET_API_KEY", "s3cret")
    store = EnvSecretStore()
    assert store.get("api_key") == "s3cret"
    assert store.get("missing") is None


class TestTransports:
    def test_registry_lists_supported_transports(self) -> None:
        assert set(AVAILABLE_TRANSPORTS) == {"streamable-http", "sse", "stdio"}

    def test_factory_creates_known_transport(self) -> None:
        transport = create_transport("sse")
        assert transport.name == "sse"
        assert not transport.is_running

    def test_unknown_transport_raises(self) -> None:
        with pytest.raises(TransportError):
            get_transport_class("carrier-pigeon")

    @pytest.mark.asyncio
    async def test_transport_stub_raises_not_implemented(self) -> None:
        transport = create_transport("stdio")
        with pytest.raises(NotImplementedError):
            await transport.start()
